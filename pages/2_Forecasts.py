"""Forecasts — model comparison and recursive forecasts from the two modeling notebooks."""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from app_charts import HISTORY, INK, MODEL_COLORS, line, style
from app_common import (arrivals_note, datasets_or_stop, get_evaluation, get_forecast,
                        get_target, source_footer)
from src import data, modeling

HORIZONS = [3, 6, 12]

st.title('Forecasts')
st.markdown('Compare three regression models and a seasonal baseline on the last 12 observed months, '
            'then see what the chosen model projects for the next 3, 6 or 12 months.')

datasets_or_stop()

# --- Controls (one row) -----------------------------------------------------------
c1, c2, c3 = st.columns([1.2, 1.4, 1])
target_key = c1.radio('Series', list(data.TARGETS), index=1, horizontal=True,
                      format_func=lambda k: 'Western Balkan Route' if k == 'WBR' else 'Montenegro')
target = get_target(target_key)
label = data.TARGETS[target_key]['label']
ev = get_evaluation(target_key)

model_labels = {f'{m} (lowest test error)' if m == ev.best_model else m: m for m in modeling.MODEL_NAMES}
default_label = next(k for k, v in model_labels.items() if v == ev.best_model)
model_name = model_labels[c2.selectbox('Model', list(model_labels), index=list(model_labels).index(default_label),
                                       key=f'model_{target_key}')]
horizon = c3.segmented_control('Horizon (months)', HORIZONS, default=12, key='horizon') or 12

forecast = get_forecast(target_key, model_name).iloc[:horizon]
color = MODEL_COLORS[model_name]

# --- Headline numbers ----------------------------------------------------------------
same_months_last_year = target.reindex(forecast.index - pd.DateOffset(years=1))
period = f'{forecast.index.min():%b %Y} – {forecast.index.max():%b %Y}'

st.subheader(f'{label}: {horizon}-month forecast')
m1, m2, m3 = st.columns(3)
m1.metric(f'Next month ({forecast.index[0]:%b %Y})', f'{forecast.iloc[0]:,.0f}')
change = (forecast.sum() / same_months_last_year.sum() - 1) * 100 if same_months_last_year.sum() else None
m2.metric(f'Total, {period}', f'{forecast.sum():,.0f}',
          f'{change:+.0f}% vs same months a year earlier' if change is not None else None,
          delta_color='off')
test_mae = ev.metrics.set_index('Model').loc[model_name, 'MAE']
m3.metric('Typical monthly error on the test year (MAE)', f'± {test_mae:,.0f}',
          help='Mean absolute error on April 2025 – March 2026 using one-month-ahead predictions. '
               'Errors on a multi-month recursive forecast are likely to be larger.')

if model_name != ev.best_model:
    st.caption(f'You are viewing **{model_name}**. **{ev.best_model}** had the lowest test error for this series.')

# --- History + forecast chart -------------------------------------------------------
show_all = st.toggle('Show full history from 2016', value=False)
history = target if show_all else target[target.index >= target.index.max() - pd.DateOffset(years=4)]

fig = go.Figure()
line(fig, history.index, history.values, 'Recorded arrivals', HISTORY)
# Join the forecast to the last observation so the line is continuous.
joined = pd.concat([target.iloc[-1:], forecast])
line(fig, joined.index, joined.values, f'Forecast — {model_name}', color, dash='dash', markers=True)
fig.add_vline(x=target.index.max(), line=dict(color='#c3c2b7', width=1, dash='dot'))
fig.add_annotation(x=target.index.max(), y=1, yref='paper', text='Last observed month', showarrow=False,
                   xanchor='right', yanchor='bottom', font=dict(size=11, color='#7a7974'))
st.plotly_chart(style(fig, f'Recorded arrivals and {horizon}-month forecast — {label}', height=420),
                width='stretch')
arrivals_note()

left, right = st.columns([1, 1.3])
with left:
    table = pd.DataFrame({
        'Month': forecast.index.strftime('%b %Y'),
        'Forecast': forecast.round(0).astype(int).values,
        'Same month a year earlier': same_months_last_year.round(0).astype(int).values,
    })
    st.dataframe(table, hide_index=True, width='stretch', height=35 * (len(table) + 1) + 3,
                 column_config={'Forecast': st.column_config.NumberColumn(format='localized'),
                                'Same month a year earlier': st.column_config.NumberColumn(format='localized')})
    export = forecast.round(0).rename('forecast_recorded_arrivals').rename_axis('month').to_frame()
    export.insert(0, 'model', model_name)
    export.insert(0, 'series', label)
    st.download_button('Download forecast (CSV)', export.to_csv().encode(),
                       file_name=f'forecast_{target_key.lower()}_{model_name.lower().replace(" ", "_")}_{horizon}m.csv',
                       mime='text/csv')
with right:
    st.warning(
        '**Read these numbers as model estimates, not predictions of what will happen.**\n'
        '- They use March 2026 data and cover April 2026 – March 2027. They are not updated live.\n'
        '- Each month is predicted from the previous predictions, so errors can build up over the horizon.\n'
        '- The models only see past arrivals and the calendar. Policy changes, border measures and '
        'conflicts are not included.\n'
        '- There are no prediction intervals. The test error above is the best guide to uncertainty.',
        icon='⚠️')

# --- Model comparison ---------------------------------------------------------------
st.divider()
st.subheader('How the models compare')
st.markdown(f'Each model was trained on {ev.n_train} months ({ev.train_period[0]:%b %Y} – '
            f'{ev.train_period[1]:%b %Y}) and tested on the next {ev.n_test} '
            f'({ev.test_period[0]:%b %Y} – {ev.test_period[1]:%b %Y}). Lower MAE and RMSE are better. '
            'The **seasonal naive** baseline repeats the same month from a year earlier. A useful model should beat it.')

tc, cc = st.columns([1.6, 1])
with tc:
    preds = ev.test_predictions
    fig = go.Figure()
    line(fig, preds.index, preds['Actual'], 'Actual', INK, markers=True)
    for name in [*modeling.MODEL_NAMES, modeling.BASELINE_NAME]:
        if name in preds:
            line(fig, preds.index, preds[name], name, MODEL_COLORS[name],
                 dash='dot' if name == modeling.BASELINE_NAME else None)
    st.plotly_chart(style(fig, 'Test year: actual vs predicted (one month ahead)', height=400), width='stretch')
with cc:
    metrics = ev.metrics.rename(columns={'R2': 'R²'})
    st.markdown('**Test-year error**')
    st.dataframe(
        metrics.style.format({'MAE': '{:,.1f}', 'RMSE': '{:,.1f}', 'R²': '{:.2f}'})
        .apply(lambda r: ['font-weight: 600' if r['Model'] == model_name else '' for _ in r], axis=1),
        hide_index=True, width='stretch')
    st.markdown('**Cross-validation on the training years**')
    st.dataframe(ev.cv.style.format({'Mean CV MAE': '{:,.1f}', 'Std CV MAE': '{:,.1f}'}),
                 hide_index=True, width='stretch')
    cv_best = ev.cv.iloc[0]['Model']
    if cv_best != ev.best_model:
        st.caption(f'The rankings disagree: **{ev.best_model}** wins on the test year, '
                   f'but **{cv_best}** wins in cross-validation over earlier periods. Treat the choice of model as uncertain.')

with st.expander('How the forecast is made'):
    st.markdown(
        '- **Features:** time index, seasonal sine/cosine of the month, lags of 1, 3, 6 and 12 months, '
        'and 3- and 6-month rolling averages that exclude the month being predicted.\n'
        '- **Models:** Linear Regression; Ridge Regression (α = 10, standardised features); Random Forest '
        '(300 trees, depth 4). The settings are fixed and match the notebooks.\n'
        '- **Test predictions** use the actual previous months, so they measure one-month-ahead accuracy.\n'
        '- **Forecasts:** the model is refitted on all months, then predicts one month at a time and '
        'feeds each prediction back in. Negative values are set to zero. The 3- and 6-month forecasts '
        'are the first months of the 12-month path.\n'
        '- The default model is the one with the lowest test MAE, as in the notebooks.'
    )

source_footer()
