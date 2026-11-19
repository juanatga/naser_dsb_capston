import streamlit as st

st.set_page_config(page_title='Forecasts — Western Balkan Route', page_icon='📈', layout='wide')

from app_common import datasets_or_stop, source_footer  # noqa: E402

st.title('Forecasts')
datasets_or_stop()
st.info('This page is under construction (plan step 4).')
source_footer()
