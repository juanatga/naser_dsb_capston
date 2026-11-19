"""Checks that the extracted code reproduces the saved notebook / README results."""
import subprocess
import sys

import folium
import pandas as pd
import pytest

from src import data, modeling, maps

# Test-set metrics from README.md (saved notebook outputs), rounded to 2 dp.
README_METRICS = {
    'WBR': {
        'Random Forest': (578.75, 740.38, 0.12),
        'Seasonal Naive': (1154.25, 1261.21, -1.56),
        'Linear Regression': (1210.77, 1499.68, -2.62),
        'Ridge Regression': (1405.93, 1756.58, -3.96),
    },
    'MNE': {
        'Linear Regression': (61.50, 84.89, 0.24),
        'Random Forest': (63.00, 95.85, 0.03),
        'Ridge Regression': (71.46, 88.97, 0.16),
        'Seasonal Naive': (146.92, 176.97, -2.31),
    },
}

# Saved 12-month forecasts (rounded) from the notebook outputs.
SAVED_FORECASTS = {
    'WBR': [3591, 3715, 3891, 3890, 3871, 3854, 3850, 3712, 3456, 3556, 3669, 4014],
    'MNE': [478, 553, 612, 627, 642, 631, 573, 494, 419, 357, 316, 315],
}


@pytest.fixture(scope='module')
def datasets():
    return data.load_workbook()


@pytest.fixture(scope='module')
def evaluations(datasets):
    return {k: modeling.evaluate_models(data.load_target(k, datasets)) for k in data.TARGETS}


def test_import_has_no_side_effects():
    code = 'import src.data, src.modeling, src.maps'
    result = subprocess.run([sys.executable, '-c', code], capture_output=True, text=True,
                            cwd=data.REPO_ROOT)
    assert result.returncode == 0, result.stderr
    assert result.stdout == ''


@pytest.mark.parametrize('key, total', [('WBR', 1_043_281), ('MNE', 40_897)])
def test_target_series(datasets, key, total):
    series = data.load_target(key, datasets)
    assert len(series) == 123
    assert series.index.min() == pd.Timestamp('2016-01-01')
    assert series.index.max() == pd.Timestamp('2026-03-01')
    assert series.sum() == total
    assert len(data.missing_months(series)) == 0


def test_validate_rejects_gaps():
    s = pd.Series([1.0] * 40, index=pd.date_range('2020-01-01', periods=40, freq='MS'))
    with pytest.raises(ValueError, match='missing months'):
        data.validate_monthly(s.drop(s.index[5]))
    with pytest.raises(ValueError, match='at least'):
        data.validate_monthly(s.iloc[:20])


@pytest.mark.parametrize('key', ['WBR', 'MNE'])
def test_metrics_match_readme(evaluations, key):
    ev = evaluations[key]
    assert ev.n_features_rows == 111 and ev.n_train == 99 and ev.n_test == 12
    assert ev.test_period == (pd.Timestamp('2025-04-01'), pd.Timestamp('2026-03-01'))
    got = ev.metrics.set_index('Model').round(2)
    for model, (mae, rmse, r2) in README_METRICS[key].items():
        assert got.loc[model, 'MAE'] == pytest.approx(mae, abs=0.01)
        assert got.loc[model, 'RMSE'] == pytest.approx(rmse, abs=0.01)
        assert got.loc[model, 'R2'] == pytest.approx(r2, abs=0.01)


def test_best_models(evaluations):
    assert evaluations['WBR'].best_model == 'Random Forest'
    assert evaluations['MNE'].best_model == 'Linear Regression'
    # README: CV ranking differs from the test ranking.
    assert evaluations['WBR'].cv.iloc[0]['Model'] == 'Ridge Regression'
    assert evaluations['MNE'].cv.iloc[0]['Model'] == 'Random Forest'


@pytest.mark.parametrize('key', ['WBR', 'MNE'])
def test_forecast_matches_saved_output(datasets, evaluations, key):
    target = data.load_target(key, datasets)
    fc = modeling.run_forecast(target, evaluations[key].best_model, horizon=12)
    assert fc.index[0] == pd.Timestamp('2026-04-01')
    assert fc.index[-1] == pd.Timestamp('2027-03-01')
    assert fc.round(0).astype(int).tolist() == SAVED_FORECASTS[key]
    assert (fc >= 0).all()


def test_shorter_horizons_are_prefixes(datasets):
    target = data.load_target('MNE', datasets)
    fc12 = modeling.run_forecast(target, 'Random Forest', 12)
    fc3 = modeling.run_forecast(target, 'Random Forest', 3)
    pd.testing.assert_series_equal(fc3, fc12.iloc[:3])


def test_maps_build(datasets):
    monthly = datasets[data.MONTHLY_SHEET]
    mne = data.load_target('MNE', datasets)
    fc = pd.Series([1.0] * 12, index=pd.date_range('2026-04-01', periods=12, freq='MS'))
    for m in (maps.build_wbr_map(monthly, fc, 'Montenegro — WBR'), maps.build_montenegro_map(mne, fc)):
        assert isinstance(m, folium.Map)
        html = m.get_root().render()
        assert 'illustrative' in html
    totals = maps.wbr_country_totals(monthly)
    assert totals['total_all'] == 1_043_281
    assert totals['by_country_all']['MNE'] == 40_897
