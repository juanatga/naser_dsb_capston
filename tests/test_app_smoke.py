"""Smoke tests: every page script runs without raising."""
import pytest
from streamlit.testing.v1 import AppTest

PAGES = ['../app.py', '../pages/1_Explore_Data.py', '../pages/2_Forecasts.py', '../pages/3_Map.py']


@pytest.mark.parametrize('page', PAGES)
def test_page_runs(page):
    at = AppTest.from_file(page, default_timeout=60).run()
    assert not at.exception, at.exception
    assert at.title, 'page should render a title'


def test_home_shows_both_targets():
    at = AppTest.from_file('../app.py', default_timeout=60).run()
    values = [m.value for m in at.metric]
    assert '40,897' in values  # Montenegro total
    assert '1,043,281' in values  # WBR total


def test_explore_page_totals_and_controls():
    at = AppTest.from_file('../pages/1_Explore_Data.py', default_timeout=60).run()
    assert not at.exception, at.exception
    series = at.selectbox[0]
    assert series.value == 'Montenegro (MNE)'  # default focus series
    assert at.metric[0].value == '40,897' and at.metric[1].value == '123'

    series.set_value('Western Balkan Route — all countries').run()
    assert not at.exception, at.exception
    assert at.metric[0].value == '1,043,281'

    # every country, every origin arrival country and every presence host renders
    for i in range(3):
        for j in range(len(at.selectbox[i].options)):
            at.selectbox[i].select_index(j).run()
            assert not at.exception, (i, j, at.exception)
    at.checkbox[0].check().run()
    assert not at.exception, at.exception


def test_forecast_page_defaults_match_notebooks():
    at = AppTest.from_file('../app.py', default_timeout=120)
    at.switch_page('pages/2_Forecasts.py').run()
    assert not at.exception, at.exception
    # Montenegro default: Linear Regression, 12 months, Apr 2026 = 478
    assert at.selectbox[0].value.startswith('Linear Regression')
    assert at.metric[0].value == '478'
    at.radio[0].set_value('WBR').run()
    assert not at.exception, at.exception
    assert at.selectbox[0].value.startswith('Random Forest')
    assert at.metric[0].value == '3,591'


def test_forecast_page_every_combination():
    at = AppTest.from_file('../app.py', default_timeout=120)
    at.switch_page('pages/2_Forecasts.py').run()
    for target in ['WBR', 'MNE']:
        at.radio[0].set_value(target).run()
        for i in range(3):
            at.selectbox[0].select_index(i).run()
            for horizon in [3, 6, 12]:
                at.session_state['horizon'] = horizon
                at.run()
                assert not at.exception, (target, i, horizon, at.exception)
                table = at.dataframe[0].value
                assert len(table) == horizon, (target, i, horizon)


def test_map_page_both_views():
    at = AppTest.from_file('../app.py', default_timeout=120)
    at.switch_page('pages/3_Map.py').run()
    assert not at.exception, at.exception
    assert len(at.dataframe[0].value) == 6  # WBR arrival countries in the sheet
    at.radio[0].set_value('Montenegro detail').run()
    assert not at.exception, at.exception
    assert len(at.dataframe[0].value) == 12  # last 12 months
    at.toggle[0].set_value(False).run()
    assert not at.exception, at.exception


@pytest.mark.parametrize('page', PAGES)
def test_missing_workbook_shows_friendly_error(page, monkeypatch, tmp_path):
    import streamlit as st
    from src import data
    monkeypatch.setattr(data, 'DEFAULT_WORKBOOK', tmp_path / 'missing.xlsx')
    st.cache_data.clear()
    try:
        at = AppTest.from_file(page, default_timeout=60).run()
        assert not at.exception, at.exception
        assert at.error and 'could not be found' in at.error[0].value
    finally:
        st.cache_data.clear()
