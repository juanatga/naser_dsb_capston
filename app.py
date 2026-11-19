"""Home page and entrypoint: ``streamlit run app.py``."""
import streamlit as st

st.set_page_config(page_title='Western Balkan Route — Migration Trends', page_icon='🧭', layout='wide')

from app_common import arrivals_note, datasets_or_stop, get_target, source_footer  # noqa: E402
from src.data import TARGETS  # noqa: E402

st.title('Western Balkan Route: migration trends and forecasting')
st.markdown(
    'How well can past arrival patterns estimate the next **3, 6 and 12 months** of recorded '
    'migrant arrivals? This app explores IOM DTM data for the Western Balkan Route (WBR) '
    'as a whole and for **Montenegro**, and compares three regression models with a '
    'seasonal baseline.'
)

datasets_or_stop()
series = {key: get_target(key) for key in TARGETS}

cols = st.columns(len(series))
for col, (key, s) in zip(cols, series.items()):
    with col, st.container(border=True):
        st.subheader(TARGETS[key]['label'])
        a, b = st.columns(2)
        a.metric('Recorded arrivals', f'{int(s.sum()):,}')
        b.metric('Monthly observations', len(s))
        a.metric('Last 12 months', f'{int(s.tail(12).sum()):,}')
        b.metric('Period', f'{s.index.min():%b %Y} – {s.index.max():%b %Y}')

arrivals_note()

st.subheader('Explore')
c1, c2, c3 = st.columns(3)
with c1, st.container(border=True):
    st.page_link('pages/1_Explore_Data.py', label='**Explore data**', icon='📊')
    st.caption('Data quality, route trends, monthly series, countries of origin and migrant presence.')
with c2, st.container(border=True):
    st.page_link('pages/2_Forecasts.py', label='**Forecasts**', icon='📈')
    st.caption('Compare models on the last 12 months and view 3, 6 or 12-month forecasts.')
with c3, st.container(border=True):
    st.page_link('pages/3_Map.py', label='**Route map**', icon='🗺️')
    st.caption('Corridors, border crossing points and recorded arrivals by country.')

with st.expander('About the method and its limits'):
    st.markdown(
        '- **Features:** time index, seasonal month terms, lags of 1, 3, 6 and 12 months, and '
        '3- and 6-month rolling averages that exclude the month being predicted.\n'
        '- **Models:** Linear Regression, Ridge Regression and Random Forest, plus a seasonal-naive '
        'baseline (same month last year).\n'
        '- **Evaluation:** trained on 99 months, tested on April 2025 – March 2026. Test predictions '
        'use observed previous months, so they measure one-month-ahead accuracy.\n'
        '- **Forecasts:** the chosen model is refitted on all data and predicts month by month, '
        'feeding each prediction back in. They start from March 2026 data and cover '
        'April 2026 – March 2027.\n'
        '- **Not included:** policy changes, border restrictions, conflicts or other external '
        'factors, and prediction intervals. Forecasts are model estimates, not confirmed arrivals.'
    )

source_footer()
