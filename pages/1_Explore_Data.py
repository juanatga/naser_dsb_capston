"""Explore data — the analysis from notebook/01_EDA_Final.ipynb, made interactive."""
import calendar

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from app_charts import BLUE, ORANGE, SERIES, line, series_line, style
from app_common import arrivals_note, country_label, datasets_or_stop, source_footer
from src import data

ROUTE_NAMES = {
    'EMR': 'Eastern Mediterranean', 'CMR': 'Central Mediterranean',
    'WMR': 'Western Mediterranean', 'WAAR': 'Western African Atlantic',
}
WBR_TOTAL = 'Western Balkan Route — all countries'


@st.cache_data
def monthly_options(_monthly: pd.DataFrame) -> dict[str, str | None]:
    wbr = _monthly[_monthly['Route'] == data.ROUTE_CODE]
    countries = sorted(wbr['ISO3 - Country of arrival'].dropna().unique(),
                       key=lambda c: (c != data.MONTENEGRO_CODE, country_label(c)))
    return {WBR_TOTAL: None, **{country_label(c): c for c in countries}}


@st.cache_data
def series_for(_monthly: pd.DataFrame, country: str | None) -> pd.Series:
    return data.monthly_series(_monthly, data.ROUTE_CODE, country)


st.title('Explore data')
st.markdown('The exploratory analysis behind the forecasts: what the source contains, how arrivals '
            'have moved over time, and where people recorded in Montenegro come from.')

ds = datasets_or_stop()
monthly_df = ds[data.MONTHLY_SHEET]

tab_series, tab_routes, tab_origins, tab_presence, tab_quality = st.tabs(
    ['Monthly arrivals', 'Routes compared', 'Countries of origin', 'Migrant presence', 'Data quality']
)

# --- Monthly arrivals ----------------------------------------------------------
with tab_series:
    options = monthly_options(monthly_df)
    c1, c2 = st.columns([1, 2])
    choice = c1.selectbox('Series', list(options), index=1 if len(options) > 1 else 0,
                          help='Montenegro is selected by `Route == WBR` and arrival country `MNE`.')
    series = series_for(monthly_df, options[choice])

    first, last = series.index.min().to_pydatetime(), series.index.max().to_pydatetime()
    start, end = c2.slider('Period', min_value=first, max_value=last, value=(first, last), format='MMM YYYY')
    window = series[(series.index >= pd.Timestamp(start)) & (series.index <= pd.Timestamp(end))]

    gaps = data.missing_months(series)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric('Recorded arrivals in period', f'{int(window.sum()):,}')
    m2.metric('Months', len(window))
    if len(window):
        m3.metric('Monthly average', f'{window.mean():,.0f}')
        m4.metric(f'Peak month ({window.idxmax():%b %Y})', f'{int(window.max()):,}')

    st.plotly_chart(series_line(window, choice, ORANGE if options[choice] == data.MONTENEGRO_CODE else BLUE,
                                f'Monthly recorded arrivals — {choice}'), width='stretch')
    if len(gaps):
        st.caption(f'{len(gaps)} month(s) have no records for this series in the source; they are shown as gaps, not zeros.')
    arrivals_note()

    left, right = st.columns(2)
    with left:
        seasonal = window.groupby(window.index.month).mean().reindex(range(1, 13))
        fig = go.Figure(go.Bar(
            x=[calendar.month_abbr[m] for m in seasonal.index], y=seasonal.values,
            marker=dict(color=BLUE, line=dict(width=0), cornerradius=4),
            hovertemplate='%{x}: %{y:,.0f}<extra>average</extra>',
        ))
        st.plotly_chart(style(fig, 'Average by calendar month (seasonality)', 'Average arrivals',
                              hover='closest', legend=False), width='stretch')
    with right:
        wbr_window = monthly_df[(monthly_df['Route'] == data.ROUTE_CODE)
                                & (monthly_df['Date'] >= pd.Timestamp(start))
                                & (monthly_df['Date'] < pd.Timestamp(end) + pd.offsets.MonthBegin(1))]
        by_country = (wbr_window.groupby('ISO3 - Country of arrival')['Arrivals'].sum()
                      .sort_values().rename(index=country_label))
        is_mne = by_country.index.str.endswith(f'({data.MONTENEGRO_CODE})')
        fig = go.Figure(go.Bar(
            x=by_country.values, y=by_country.index, orientation='h',
            marker=dict(color=[ORANGE if m else BLUE for m in is_mne], cornerradius=4),
            hovertemplate='%{y}: %{x:,.0f}<extra></extra>',
        ))
        fig = style(fig, 'WBR recorded arrivals by country, same period', None, hover='closest', legend=False)
        fig.update_xaxes(tickformat=',d', gridcolor='#e6e5e1', showgrid=True)
        fig.update_yaxes(gridcolor='rgba(0,0,0,0)', tickformat=None)
        st.plotly_chart(fig, width='stretch')

    st.download_button(
        'Download this series (CSV)',
        window.rename('Arrivals').rename_axis('Month').to_csv().encode(),
        file_name=f"monthly_arrivals_{(options[choice] or 'WBR').lower()}.csv", mime='text/csv',
    )

# --- Routes compared --------------------------------------------------------------
with tab_routes:
    st.markdown('Yearly recorded arrivals on each **first-arrival** route into Europe '
                '(sheet `First_Arrival_Countries_Monthly`). The WBR is a secondary-movement route '
                'and is recorded in a different sheet, so it is not on this chart.')
    include_partial = st.checkbox('Include 2026 (January–March only)', value=False)
    yearly = data.arrivals_by_route_year(ds['First_Arrival_Countries_Monthly'])
    if not include_partial:
        yearly = yearly[yearly['Year'] < 2026]
    routes = (yearly.groupby('Route')['Arrivals'].sum().sort_values(ascending=False).index.tolist())
    fig = go.Figure()
    for i, route in enumerate(routes):
        r = yearly[yearly['Route'] == route]
        line(fig, r['Year'], r['Arrivals'], f'{ROUTE_NAMES.get(route, route)} ({route})', SERIES[i], markers=True)
    fig = style(fig, 'Recorded arrivals by first-arrival route, per year', height=420)
    fig.update_xaxes(dtick=1)
    st.plotly_chart(fig, width='stretch')
    with st.expander('Table'):
        st.dataframe(yearly.pivot(index='Year', columns='Route', values='Arrivals'), width='stretch')

# --- Countries of origin -------------------------------------------------------------
with tab_origins:
    coo = ds[data.ORIGIN_SHEET]
    period = f"{coo['Date'].min():%b %Y} – {coo['Date'].max():%b %Y}"
    wbr_arrival = sorted(coo.loc[coo['Route'] == data.ROUTE_CODE, 'ISO3 - Country of arrival'].dropna().unique(),
                         key=lambda c: (c != data.MONTENEGRO_CODE, country_label(c)))
    c1, c2 = st.columns([2, 1])
    arrival_opts = {country_label(c): c for c in wbr_arrival}
    arrival = arrival_opts[c1.selectbox('Country of arrival (WBR)', list(arrival_opts))]
    top_n = c2.slider('Show top', 5, 25, 15)
    st.info(f'Country-of-origin data in this release covers **{period} only**, so it describes '
            'the most recent quarter rather than the full 2016–2026 history.', icon='ℹ️')

    origin = data.origins(coo, data.ROUTE_CODE, arrival)
    if origin.empty:
        st.warning('No country-of-origin records for this selection.')
    else:
        total = origin['Arrivals'].sum()
        top = origin.head(top_n).iloc[::-1]
        fig = go.Figure(go.Bar(
            x=top['Arrivals'], y=[country_label(c) for c in top['ISO3 - Country of origin']], orientation='h',
            marker=dict(color=BLUE, cornerradius=4),
            customdata=(top['Arrivals'] / total * 100).round(1),
            hovertemplate='%{y}: %{x:,.0f} (%{customdata}% of total)<extra></extra>',
        ))
        fig = style(fig, f'Top {min(top_n, len(origin))} countries of origin — arrivals in {country_label(arrival)}',
                    None, height=max(320, 28 * len(top) + 80), hover='closest', legend=False)
        fig.update_xaxes(tickformat=',d', gridcolor='#e6e5e1', showgrid=True)
        fig.update_yaxes(gridcolor='rgba(0,0,0,0)', tickformat=None)
        st.plotly_chart(fig, width='stretch')
        st.caption(f'{len(origin)} countries of origin, {int(total):,} recorded arrivals in total. '
                   'Some origins are reported under unspecified or regional categories in the source.')

# --- Migrant presence --------------------------------------------------------------
with tab_presence:
    pres_df = ds[data.PRESENCE_SHEET]
    hosts = sorted(pres_df['ISO3 - Host country'].dropna().unique(),
                   key=lambda c: (c != data.MONTENEGRO_CODE, country_label(c)))
    host_opts = {country_label(c): c for c in hosts}
    host = host_opts[st.selectbox('Host country', list(host_opts))]
    st.info('Presence counts the people reported **present** in a country on a given date. It is a '
            'different measure from arrivals and should not be added to or compared directly with them.',
            icon='ℹ️')
    pres = data.presence(pres_df, host)
    if pres.empty:
        st.warning('No presence records for this country.')
    else:
        fig = line(go.Figure(), pres['Date'], pres['Individuals present'], 'Individuals present',
                   ORANGE if host == data.MONTENEGRO_CODE else BLUE, markers=True)
        st.plotly_chart(style(fig, f'Reported migrant presence — {country_label(host)} (weekly)',
                              'Individuals present', legend=False), width='stretch')
        st.caption(f"{len(pres)} weekly reports, {pres['Date'].min():%d %b %Y} – {pres['Date'].max():%d %b %Y}.")

# --- Data quality ---------------------------------------------------------------------
with tab_quality:
    st.markdown('Source: IOM DTM Europe workbook, Q1 2026 release. Five sheets are used.')
    report = data.quality_report(ds)
    coverage = []
    for name, df in ds.items():
        coverage.append({'Dataset': name,
                         'First date': df['Date'].min().date() if 'Date' in df else None,
                         'Last date': df['Date'].max().date() if 'Date' in df else None})
    st.dataframe(report.merge(pd.DataFrame(coverage), on='Dataset'), hide_index=True, width='stretch')
    st.markdown(
        '- **No duplicate rows or missing cells** in any of the five sheets.\n'
        '- The WBR and Montenegro monthly series both run **January 2016 – March 2026 with no missing months**.\n'
        '- Missing months would never be filled with zero: the source must confirm what they mean.\n'
        '- `Other_Countries_Areas_Monthly` also contains `EU Other` records; these are excluded from the WBR series.'
    )
    sheet = st.selectbox('Preview a sheet', list(ds))
    st.dataframe(ds[sheet].head(50), hide_index=True, width='stretch')

source_footer()
