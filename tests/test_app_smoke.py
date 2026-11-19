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
