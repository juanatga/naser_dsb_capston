"""Streamlit-side helpers shared by all pages: cached data access and common notices.

Caching lives here, not in ``src/``, so the modeling code stays framework-free.
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

from src import data

SOURCE_NAME = 'IOM Displacement Tracking Matrix (DTM) — Europe, Q1 2026 dataset'
SOURCE_URL = 'https://dtm.iom.int/europe'


@st.cache_data(show_spinner='Loading the DTM workbook…')
def get_datasets() -> dict[str, pd.DataFrame]:
    return data.load_workbook()


@st.cache_data
def get_country_names() -> dict[str, str]:
    return data.country_names()


def country_label(iso: str) -> str:
    """'Montenegro (MNE)' style label; falls back to the code if unknown."""
    name = get_country_names().get(iso)
    return f'{name} ({iso})' if name and name != iso else iso


@st.cache_data
def get_target(key: str) -> pd.Series:
    return data.load_target(key, get_datasets())


def datasets_or_stop() -> dict[str, pd.DataFrame]:
    """Load the workbook, or show a readable error and stop the page."""
    try:
        return get_datasets()
    except FileNotFoundError as exc:
        st.error(
            f'The data workbook could not be found.\n\n`{exc}`\n\n'
            'Place `DTM Europe_Q1_2026_Dataset.xlsx` in `data/raw/` and reload.'
        )
        st.stop()


def arrivals_note() -> None:
    st.caption(
        '“Arrivals” are recorded arrival events, not unique people: the same person can be '
        'recorded in more than one country. Migrant presence is a separate measure.'
    )


def source_footer() -> None:
    st.divider()
    st.caption(
        f'Data: [{SOURCE_NAME}]({SOURCE_URL}). Data runs to March 2026. '
        'DSB capstone project — exploratory analysis, not an operational planning tool.'
    )


@st.cache_data(show_spinner='Training and evaluating models…')
def get_evaluation(key: str):
    """Model comparison for a target (fits 3 models + CV; about a second, then cached)."""
    from src import modeling
    return modeling.evaluate_models(get_target(key))


@st.cache_data(show_spinner='Fitting the forecast…')
def get_forecast(key: str, model_name: str) -> pd.Series:
    """12-month recursive forecast; shorter horizons are prefixes of this path."""
    from src import modeling
    return modeling.run_forecast(get_target(key), model_name, modeling.MAX_HORIZON)
