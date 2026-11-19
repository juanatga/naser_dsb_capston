"""Entrypoint: ``streamlit run app.py``. Defines page config and navigation."""
import streamlit as st

st.set_page_config(page_title='Western Balkan Route — Migration Trends', page_icon='🧭', layout='wide')

pages = st.navigation([
    st.Page('pages/home.py', title='Overview', icon='🧭', default=True),
    st.Page('pages/1_Explore_Data.py', title='Explore data', icon='📊', url_path='explore'),
    st.Page('pages/2_Forecasts.py', title='Forecasts', icon='📈', url_path='forecasts'),
    st.Page('pages/3_Map.py', title='Route map', icon='🗺️', url_path='map'),
])
pages.run()
