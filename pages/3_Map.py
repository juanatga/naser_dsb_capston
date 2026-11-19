"""Route map — the Folium maps from the two modeling notebooks."""
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

from app_common import (country_label, datasets_or_stop, get_evaluation, get_forecast, get_target,
                        source_footer)
from src import data, maps

VIEWS = {'Western Balkan Route': 'WBR', 'Montenegro detail': 'MNE'}

st.title('Route map')
st.markdown('Where recorded arrivals happen along the Western Balkan Route, and the main entry and exit '
            'points through Montenegro. Hover over a marker for totals; click it for details.')

ds = datasets_or_stop()
monthly_df = ds[data.MONTHLY_SHEET]

c1, c2 = st.columns([1.3, 1])
view = VIEWS[c1.radio('View', list(VIEWS), horizontal=True)]
show_forecast = c2.toggle('Show 12-month forecast in the legend', value=True,
                          help='Uses the model with the lowest test error for the series shown on this map.')

forecast = None
if show_forecast:
    best = get_evaluation(view).best_model
    forecast = get_forecast(view, best)

if view == 'WBR':
    fmap = maps.build_wbr_map(monthly_df, forecast,
                              forecast_label=f'WBR, {get_evaluation(view).best_model}' if forecast is not None else None)
    height = 640
else:
    fmap = maps.build_montenegro_map(get_target('MNE'), forecast)
    height = 600

# returned_objects=[] keeps panning/zooming from re-running the script.
st_folium(fmap, height=height, use_container_width=True, returned_objects=[], key=f'map_{view}')

st.caption('Corridor lines are illustrative paths drawn between countries or crossing points; they are '
           'not tracked journeys. Arrivals are recorded events, not unique people, and a country total '
           'is not a border-crossing count. Base maps © OpenStreetMap contributors, Esri.')

# Table view of what the map shows, so the numbers are readable without the map.
st.subheader('The numbers behind the map')
if view == 'WBR':
    totals = maps.wbr_country_totals(monthly_df)
    table = pd.DataFrame({
        'Country': [country_label(c) for c in totals['by_country_all']],
        f"Total {totals['first_month']:%b %Y} – {totals['last_month']:%b %Y}": list(totals['by_country_all'].values()),
        'Last 12 months': [totals['by_country_12m'].get(c, 0) for c in totals['by_country_all']],
    })
    table['Share of WBR total'] = table.iloc[:, 1] / totals['total_all']
    table = table.sort_values(table.columns[1], ascending=False)
    st.dataframe(table, hide_index=True, width='stretch', column_config={
        table.columns[1]: st.column_config.NumberColumn(format='localized'),
        'Last 12 months': st.column_config.NumberColumn(format='localized'),
        'Share of WBR total': st.column_config.NumberColumn(format='percent'),
    })
    no_records = [maps.COUNTRIES[c]['name'].split(' (')[0] for c in maps.COUNTRIES if c not in totals['by_country_all']]
    if no_records:
        st.caption(f"Also on the map but with no WBR records in this sheet (shown as zero): {', '.join(no_records)}. "
                   'They mark where the corridors begin or lead.')
else:
    last_12 = get_target('MNE').tail(12)
    table = pd.DataFrame({'Month': last_12.index.strftime('%b %Y'), 'Recorded arrivals': last_12.astype(int).values})
    st.dataframe(table, hide_index=True, width='stretch', height=35 * (len(table) + 1) + 3,
                 column_config={'Recorded arrivals': st.column_config.NumberColumn(format='localized')})

if forecast is not None:
    st.caption(f'Forecast in the legend: {get_evaluation(view).best_model}, '
               f'{forecast.index.min():%b %Y} – {forecast.index.max():%b %Y}. '
               'See the Forecasts page for the method and its limits.')

source_footer()
