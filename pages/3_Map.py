import streamlit as st

st.set_page_config(page_title='Route map — Western Balkan Route', page_icon='🗺️', layout='wide')

from app_common import datasets_or_stop, source_footer  # noqa: E402

st.title('Route map')
datasets_or_stop()
st.info('This page is under construction (plan step 5).')
source_footer()
