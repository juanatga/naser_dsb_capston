"""Loading and preparing the IOM DTM Europe workbook.

Logic follows ``notebook/01_EDA_Final.ipynb`` and the data cells of the two
modeling notebooks. Paths are resolved relative to the repository, not ``/content``.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_WORKBOOK = REPO_ROOT / 'data' / 'raw' / 'DTM Europe_Q1_2026_Dataset.xlsx'

SHEETS = [
    'First_Arrival_Countries_Monthly',
    'Other_Countries_Areas_Monthly',
    'First_Arrival_Countries_CoO',
    'Others_Countries_CoO',
    'All_Migrant_Presence',
]

# The sheet used for both forecasting series.
MONTHLY_SHEET = 'Other_Countries_Areas_Monthly'
ORIGIN_SHEET = 'Others_Countries_CoO'
PRESENCE_SHEET = 'All_Migrant_Presence'

ROUTE_CODE = 'WBR'
MONTENEGRO_CODE = 'MNE'

# Supported forecasting targets: key -> (display label, country filter or None)
TARGETS = {
    'WBR': {'label': 'Western Balkan Route', 'country': None},
    'MNE': {'label': 'Montenegro — Western Balkan Route', 'country': MONTENEGRO_CODE},
}

MIN_OBSERVATIONS = 36


def load_workbook(path: str | Path | None = None, sheets: list[str] | None = None) -> dict[str, pd.DataFrame]:
    """Read the selected sheets and coerce ``Date``/``Arrivals`` like the notebooks do."""
    path = Path(path) if path is not None else DEFAULT_WORKBOOK
    if not path.exists():
        raise FileNotFoundError(f'Workbook not found: {path}')

    sheets = sheets or SHEETS
    datasets = pd.read_excel(path, sheet_name=sheets)
    for name, data in datasets.items():
        if 'Date' in data.columns:
            data['Date'] = pd.to_datetime(data['Date'], errors='coerce')
        if 'Arrivals' in data.columns:
            data['Arrivals'] = pd.to_numeric(data['Arrivals'], errors='coerce')
        datasets[name] = data
    return datasets


def monthly_series(df: pd.DataFrame, route: str = ROUTE_CODE, country: str | None = None) -> pd.Series:
    """Sum recorded arrivals per calendar month for a route, optionally one arrival country."""
    base = df.dropna(subset=['Date', 'Arrivals'])
    mask = base['Route'] == route
    if country is not None:
        mask &= base['ISO3 - Country of arrival'] == country
    selected = base[mask].copy()
    selected['Month'] = selected['Date'].dt.to_period('M').dt.to_timestamp()

    series = selected.groupby('Month')['Arrivals'].sum().sort_index().astype(float)
    series.name = 'Arrivals'
    return series


def missing_months(series: pd.Series) -> pd.DatetimeIndex:
    """Month starts between the first and last observation that are absent from the series."""
    if series.empty:
        return pd.DatetimeIndex([])
    expected = pd.date_range(series.index.min(), series.index.max(), freq='MS')
    return expected.difference(series.index)


def validate_monthly(series: pd.Series, name: str = 'Series', min_obs: int = MIN_OBSERVATIONS) -> pd.Series:
    """Raise if the series is empty, has gaps, missing values, or too few months.

    Missing months are never filled with zero: the source must confirm what they mean.
    """
    if series.empty:
        raise ValueError(f'{name} is empty. Check the route/country filters.')
    expected = pd.date_range(series.index.min(), series.index.max(), freq='MS')
    if not series.index.equals(expected):
        gaps = missing_months(series)
        raise ValueError(
            f'{name} has missing months or a non-month-start index ({len(gaps)} missing). '
            'Investigate the source before modeling; do not fill with zero.'
        )
    if series.isna().any():
        raise ValueError(f'{name} contains missing values.')
    if len(series) < min_obs:
        raise ValueError(f'{name} has only {len(series)} months; at least {min_obs} are needed.')
    return series


ISO3_SHEET = 'ISO3'
NAME_OVERRIDES = {'OOO': 'Other / unspecified', 'XKX': 'Kosovo*'}


def country_names(path: str | Path | None = None) -> dict[str, str]:
    """ISO3 code -> country name, from the workbook's own ``ISO3`` lookup sheet."""
    path = Path(path) if path is not None else DEFAULT_WORKBOOK
    lookup = pd.read_excel(path, sheet_name=ISO3_SHEET).dropna()
    names = dict(zip(lookup['ISO3'].astype(str).str.strip(), lookup['Country or Area'].astype(str).str.strip()))
    names.update(NAME_OVERRIDES)
    return names


def load_target(key: str, datasets: dict[str, pd.DataFrame] | None = None,
                path: str | Path | None = None) -> pd.Series:
    """Return the validated monthly series for a target key in ``TARGETS``."""
    if key not in TARGETS:
        raise KeyError(f'Unknown target {key!r}; choose one of {list(TARGETS)}')
    if datasets is None:
        datasets = load_workbook(path, sheets=[MONTHLY_SHEET])
    spec = TARGETS[key]
    series = monthly_series(datasets[MONTHLY_SHEET], ROUTE_CODE, spec['country'])
    return validate_monthly(series, spec['label'])


def quality_report(datasets: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Rows, columns, duplicates and missing cells per sheet (EDA notebook, cell 11)."""
    return pd.DataFrame([
        {
            'Dataset': name,
            'Rows': len(data),
            'Columns': data.shape[1],
            'Duplicate rows': int(data.duplicated().sum()),
            'Missing cells': int(data.isna().sum().sum()),
        }
        for name, data in datasets.items()
    ])


def arrivals_by_route_year(df: pd.DataFrame) -> pd.DataFrame:
    """Yearly recorded arrivals per route (EDA notebook, cell 16)."""
    return (
        df.groupby(['Year', 'Route'], as_index=False)['Arrivals']
        .sum()
        .sort_values(['Year', 'Route'])
        .reset_index(drop=True)
    )


def origins(df_coo: pd.DataFrame, route: str = ROUTE_CODE, country: str = MONTENEGRO_CODE) -> pd.DataFrame:
    """Recorded arrivals by country of origin for one route and arrival country (EDA cell 24)."""
    selected = df_coo[(df_coo['Route'] == route) & (df_coo['ISO3 - Country of arrival'] == country)]
    return (
        selected.groupby('ISO3 - Country of origin', as_index=False)['Arrivals']
        .sum()
        .sort_values('Arrivals', ascending=False)
        .reset_index(drop=True)
    )


def presence(df_presence: pd.DataFrame, host: str = MONTENEGRO_CODE) -> pd.DataFrame:
    """Reported migrant presence for a host country (EDA cell 31). A different measure from arrivals."""
    return (
        df_presence[df_presence['ISO3 - Host country'] == host]
        .sort_values('Date')
        .reset_index(drop=True)
    )
