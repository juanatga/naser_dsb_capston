"""Feature engineering, model comparison and recursive forecasting.

Lifted from ``notebook/02_Modeling_Finall_.ipynb`` and
``notebook/02_1_Modeling_Montenegro_Only_Finall.ipynb``, whose modeling code is
identical. Numerical behavior is preserved deliberately, including:

* training features are rounded to 2 decimals, recursive-forecast features are not;
* test-set predictions use observed lags (one-step-ahead), not a recursive forecast;
* the final model is chosen by lowest test MAE among the ML models (baseline excluded).
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import TimeSeriesSplit, cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

FEATURES = [
    'Time_Index',
    'Month_Sin',
    'Month_Cos',
    'Lag_1',
    'Lag_3',
    'Lag_6',
    'Lag_12',
    'Rolling_Mean_3',
    'Rolling_Mean_6',
]

TEST_MONTHS = 12
CV_SPLITS = 3
MAX_HORIZON = 12
BASELINE_NAME = 'Seasonal Naive'
MODEL_NAMES = ['Linear Regression', 'Ridge Regression', 'Random Forest']


def make_features(series: pd.Series) -> pd.DataFrame:
    """Calendar, lag and shifted rolling-mean features. Rows with incomplete lags are dropped."""
    data = pd.DataFrame({'Arrivals': series.copy()})
    data.index.name = 'Month'

    data['Time_Index'] = np.arange(len(data))
    data['Month_Number'] = data.index.month

    data['Month_Sin'] = np.sin(2 * np.pi * data['Month_Number'] / 12)
    data['Month_Cos'] = np.cos(2 * np.pi * data['Month_Number'] / 12)

    data['Lag_1'] = data['Arrivals'].shift(1)
    data['Lag_3'] = data['Arrivals'].shift(3)
    data['Lag_6'] = data['Arrivals'].shift(6)
    data['Lag_12'] = data['Arrivals'].shift(12)

    data['Rolling_Mean_3'] = data['Arrivals'].shift(1).rolling(3).mean()
    data['Rolling_Mean_6'] = data['Arrivals'].shift(1).rolling(6).mean()
    data = data.round(2)
    return data.dropna()


def make_models() -> dict:
    """Fresh, unfitted estimators with the notebooks' fixed hyperparameters."""
    return {
        'Linear Regression': LinearRegression(),
        'Ridge Regression': Pipeline([
            ('scaler', StandardScaler()),
            ('model', Ridge(alpha=10.0)),
        ]),
        'Random Forest': RandomForestRegressor(
            n_estimators=300,
            max_depth=4,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42,
        ),
    }


def make_model(name: str):
    models = make_models()
    if name not in models:
        raise KeyError(f'Unknown model {name!r}; choose one of {MODEL_NAMES}')
    return models[name]


def calculate_metrics(actual, predicted) -> dict:
    return {
        'MAE': mean_absolute_error(actual, predicted),
        'RMSE': np.sqrt(mean_squared_error(actual, predicted)),
        'R2': r2_score(actual, predicted),
    }


def split_features(feature_df: pd.DataFrame, test_months: int = TEST_MONTHS):
    """Chronological split: the last ``test_months`` rows form the test set."""
    if len(feature_df) <= test_months + 12:
        raise ValueError('Not enough rows after feature engineering for this test split.')
    X = feature_df[FEATURES]
    y = feature_df['Arrivals']
    return X.iloc[:-test_months], X.iloc[-test_months:], y.iloc[:-test_months], y.iloc[-test_months:]


def seasonal_naive(target: pd.Series, index: pd.DatetimeIndex) -> pd.Series:
    """Predict each month with the value recorded in the same month one year earlier."""
    baseline = target.reindex(index - pd.DateOffset(years=1))
    baseline.index = index
    return baseline


@dataclass
class Evaluation:
    """Results of comparing the candidate models on one target series."""
    metrics: pd.DataFrame          # Model, MAE, RMSE, R2 — sorted by MAE, unrounded
    test_predictions: pd.DataFrame  # index = test months; 'Actual' plus one column per model
    cv: pd.DataFrame               # Model, Mean CV MAE, Std CV MAE
    best_model: str                # lowest test MAE among ML models (baseline excluded)
    train_period: tuple            # (first, last) training month
    test_period: tuple             # (first, last) test month
    n_train: int = 0
    n_test: int = 0
    n_features_rows: int = 0
    extra: dict = field(default_factory=dict)


def evaluate_models(target: pd.Series, test_months: int = TEST_MONTHS, cv_splits: int = CV_SPLITS) -> Evaluation:
    """Fit all models on the training window, score the held-out months and run expanding-window CV."""
    feature_df = make_features(target)
    X_train, X_test, y_train, y_test = split_features(feature_df, test_months)

    predictions = {'Actual': y_test.values}
    rows = []
    for name, model in make_models().items():
        model.fit(X_train, y_train)
        pred = model.predict(X_test)
        predictions[name] = pred
        rows.append({'Model': name, **calculate_metrics(y_test, pred)})

    baseline = seasonal_naive(target, y_test.index)
    if baseline.notna().all():
        predictions[BASELINE_NAME] = baseline.values
        rows.append({'Model': BASELINE_NAME, **calculate_metrics(y_test, baseline)})

    metrics = pd.DataFrame(rows).sort_values('MAE').reset_index(drop=True)

    tscv = TimeSeriesSplit(n_splits=cv_splits)
    cv_rows = []
    for name, model in make_models().items():
        scores = cross_val_score(model, X_train, y_train, cv=tscv, scoring='neg_mean_absolute_error')
        cv_rows.append({'Model': name, 'Mean CV MAE': -scores.mean(), 'Std CV MAE': scores.std()})
    cv = pd.DataFrame(cv_rows).sort_values('Mean CV MAE').reset_index(drop=True)

    best = metrics[metrics['Model'].isin(MODEL_NAMES)].iloc[0]['Model']

    return Evaluation(
        metrics=metrics,
        test_predictions=pd.DataFrame(predictions, index=y_test.index),
        cv=cv,
        best_model=best,
        train_period=(X_train.index.min(), X_train.index.max()),
        test_period=(X_test.index.min(), X_test.index.max()),
        n_train=len(X_train),
        n_test=len(X_test),
        n_features_rows=len(feature_df),
    )


def fit_final_model(target: pd.Series, model_name: str):
    """Refit the named model on every observation that has complete features."""
    feature_df = make_features(target)
    model = make_model(model_name)
    model.fit(feature_df[FEATURES], feature_df['Arrivals'])
    return model


def recursive_forecast(history: pd.Series, fitted_model, horizon: int = MAX_HORIZON,
                       feature_columns: list[str] = FEATURES) -> pd.Series:
    """Forecast month by month, feeding each prediction back in as history. Negatives clip to 0."""
    values = list(history.astype(float).values)
    last_date = history.index[-1]
    future_dates = []
    forecast_values = []

    for step in range(1, horizon + 1):
        next_date = last_date + pd.DateOffset(months=step)
        next_features = pd.DataFrame([{
            'Time_Index': len(values),
            'Month_Sin': np.sin(2 * np.pi * next_date.month / 12),
            'Month_Cos': np.cos(2 * np.pi * next_date.month / 12),
            'Lag_1': values[-1],
            'Lag_3': values[-3],
            'Lag_6': values[-6],
            'Lag_12': values[-12],
            'Rolling_Mean_3': np.mean(values[-3:]),
            'Rolling_Mean_6': np.mean(values[-6:]),
        }], columns=feature_columns)

        prediction = max(0.0, float(fitted_model.predict(next_features)[0]))
        future_dates.append(next_date)
        forecast_values.append(prediction)
        values.append(prediction)

    return pd.Series(
        forecast_values,
        index=pd.DatetimeIndex(future_dates, name='Month'),
        name='Forecasted recorded arrivals',
    )


def run_forecast(target: pd.Series, model_name: str, horizon: int = MAX_HORIZON) -> pd.Series:
    """Refit ``model_name`` on all data and return a ``horizon``-month recursive forecast.

    Shorter horizons are prefixes of the 12-month path, so callers can compute 12 once and slice.
    """
    if not 1 <= horizon <= MAX_HORIZON:
        raise ValueError(f'horizon must be between 1 and {MAX_HORIZON}')
    model = fit_final_model(target, model_name)
    return recursive_forecast(target, model, horizon)
