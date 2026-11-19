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
