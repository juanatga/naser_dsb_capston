"""Folium map builders for the regional WBR view and the Montenegro detail view.

Geography and styling come from the map cells of the two modeling notebooks.
Builders take their data as arguments and return a ``folium.Map``; rendering or
saving is left to the caller. Corridor lines are illustrative paths defined
here, not tracked individual journeys.
"""
from __future__ import annotations

import folium
import pandas as pd
from folium.plugins import AntPath

from src.data import MONTENEGRO_CODE, ROUTE_CODE

# --- Regional (WBR) geography -------------------------------------------------

COUNTRIES = {
    'GRC': {'name': 'Greece (Main Entry)', 'coords': [39.0742, 21.8243]},
    'TUR': {'name': 'Türkiye (Entry Point)', 'coords': [38.9637, 35.2433]},
    'BGR': {'name': 'Bulgaria (Transit)', 'coords': [42.7339, 25.4858]},
    'MKD': {'name': 'North Macedonia', 'coords': [41.6086, 21.7453]},
    'ALB': {'name': 'Albania', 'coords': [41.1533, 20.1683]},
    'XKX': {'name': 'Kosovo*', 'coords': [42.6026, 20.9030]},
    'MNE': {'name': 'Montenegro (Focus Country)', 'coords': [42.7087, 19.3744]},
    'SRB': {'name': 'Serbia', 'coords': [44.0165, 21.0059]},
    'ROU': {'name': 'Romania', 'coords': [45.9432, 24.9668]},
    'BIH': {'name': 'Bosnia and Herzegovina', 'coords': [43.9159, 17.6791]},
    'HRV': {'name': 'Croatia', 'coords': [45.1000, 15.2000]},
    'SVN': {'name': 'Slovenia', 'coords': [46.1512, 14.9955]},
}

BORDER_CROSSINGS = [
    {'name': 'BCP Kapitan Andreevo (TUR -> BGR)', 'coords': [41.7167, 26.3167], 'corridor': 'Eastern Corridor', 'country': 'BGR'},
    {'name': 'BCP Evzoni / Bogorodica (GRC -> MKD)', 'coords': [41.1033, 22.5514], 'corridor': 'Central Corridor', 'country': 'MKD'},
    {'name': 'BCP Kakavia (GRC -> ALB)', 'coords': [39.9144, 20.3611], 'corridor': 'Coastal Corridor', 'country': 'ALB'},
    {'name': 'BCP Tabanovce / Preševo (MKD -> SRB)', 'coords': [42.2261, 21.7036], 'corridor': 'Central Corridor', 'country': 'SRB'},
    {'name': 'BCP Božaj / Hani i Hotit (ALB -> MNE)', 'coords': [42.3331, 19.4239], 'corridor': 'Coastal Corridor', 'country': 'MNE'},
    {'name': 'BCP Sukobin / Muriqan (ALB -> MNE)', 'coords': [42.0169, 19.3664], 'corridor': 'Coastal Corridor', 'country': 'MNE'},
    {'name': 'BCP Šćepan Polje / Hum (MNE -> BIH)', 'coords': [43.3478, 18.8436], 'corridor': 'Coastal Corridor', 'country': 'BIH'},
    {'name': 'BCP Metaljka / Čajniče (MNE -> BIH)', 'coords': [43.5292, 19.1667], 'corridor': 'Coastal Corridor', 'country': 'BIH'},
    {'name': 'BCP Horgoš / Röszke (SRB -> HUN)', 'coords': [46.1736, 19.9814], 'corridor': 'Central Corridor (North)', 'country': 'SRB'},
    {'name': 'BCP Batrovci / Bajakovo (SRB -> HRV)', 'coords': [45.0489, 19.1047], 'corridor': 'Central Corridor (West)', 'country': 'HRV'},
    {'name': 'BCP Debeli Brijeg / Karasovići (MNE -> HRV)', 'coords': [42.4858, 18.4383], 'corridor': 'Coastal Corridor (EU Border)', 'country': 'HRV'},
    {'name': 'BCP Bregana / Obrežje (HRV -> SVN)', 'coords': [45.8425, 15.6914], 'corridor': 'Main Exit toward EU/Schengen', 'country': 'SVN'},
]

CORRIDORS = [
    {'path': ['GRC', 'MKD', 'SRB', 'HRV', 'SVN'], 'color': '#2b5c8f', 'weight': 5, 'label': 'Central Corridor (GRC - MKD - SRB - HRV - SVN)'},
    {'path': ['GRC', 'ALB', 'MNE', 'BIH', 'HRV', 'SVN'], 'color': '#d9534f', 'weight': 4, 'label': 'Coastal / Adriatic Corridor (GRC - ALB - MNE - BIH - HRV)'},
    {'path': ['TUR', 'BGR', 'SRB', 'ROU'], 'color': '#5bc0de', 'weight': 3, 'label': 'Eastern Corridor (TUR - BGR - SRB - ROU)'},
    {'path': ['SRB', 'BIH'], 'color': '#f0ad4e', 'weight': 3, 'label': 'Secondary Branch (SRB - BIH)'},
    {'path': ['MKD', 'XKX', 'SRB'], 'color': '#9b59b6', 'weight': 2, 'label': 'Kosovo* Branch (MKD - XKX - SRB)'},
]

# --- Montenegro detail geography ---------------------------------------------

MNE_POINTS = {
    'BOZAJ': {'name': 'BCP Božaj / Hani i Hotit (ALB → MNE)', 'type': 'Main Entry Point',
              'coords': [42.3331, 19.4239], 'color': '#d9534f',
              'desc': 'Primary entry corridor from Albania toward Podgorica.'},
    'SUKOBIN': {'name': 'BCP Sukobin / Muriqan (ALB → MNE)', 'type': 'Secondary Entry Point',
                'coords': [42.0169, 19.3664], 'color': '#e67e22',
                'desc': 'Coastal entry point from Albania (Shkodër – Ulcinj direction).'},
    'PG_HUB': {'name': 'Podgorica (Central Transit & Reception Hub)', 'type': 'Registration & Transit Hub',
               'coords': [42.4304, 19.2594], 'color': '#b30000',
               'desc': 'Main registration center (Spuž / Božaj reception facilities).'},
    'METALJKA': {'name': 'BCP Metaljka / Čajniče (MNE → BIH)', 'type': 'Main Exit Point (North)',
                 'coords': [43.5292, 19.1667], 'color': '#2b5c8f',
                 'desc': 'Primary northern exit route from Pljevlja toward Bosnia and Herzegovina.'},
    'SCEPAN_POLJE': {'name': 'BCP Šćepan Polje / Hum (MNE → BIH)', 'type': 'Main Exit Point (North-West)',
                     'coords': [43.3478, 18.8436], 'color': '#2b5c8f',
                     'desc': 'Key exit route via Nikšić and Plužine toward Foča (BiH).'},
    'ILINO_BRDO': {'name': 'BCP Ilino Brdo / Klobuk (MNE → BIH)', 'type': 'Exit Point (West)',
                   'coords': [42.7336, 18.5833], 'color': '#5bc0de',
                   'desc': 'Western exit route from Nikšić toward Trebinje (BiH).'},
    'DEBELI_BRIJEG': {'name': 'BCP Debeli Brijeg / Karasovići (MNE → HRV)', 'type': 'EU Border Exit Point',
                      'coords': [42.4858, 18.4383], 'color': '#9b59b6',
                      'desc': 'Direct coastal border crossing with Croatia (EU external border).'},
}

MNE_CORRIDORS = [
    {'path': ['BOZAJ', 'PG_HUB', 'SCEPAN_POLJE'], 'color': '#d9534f', 'weight': 5, 'label': 'Main Transit Axis: Božaj → Podgorica → Šćepan Polje (BiH)'},
    {'path': ['PG_HUB', 'METALJKA'], 'color': '#2b5c8f', 'weight': 4, 'label': 'Northern Branch: Podgorica → Pljevlja → Metaljka (BiH)'},
    {'path': ['SUKOBIN', 'PG_HUB', 'ILINO_BRDO'], 'color': '#e67e22', 'weight': 3, 'label': 'Western Branch: Sukobin → Podgorica → Ilino Brdo (BiH)'},
    {'path': ['SUKOBIN', 'DEBELI_BRIJEG'], 'color': '#9b59b6', 'weight': 3, 'label': 'Coastal Branch: Sukobin → Herceg Novi → Debeli Brijeg (Croatia / EU)'},
]

LEGEND_STYLE = (
    'position:fixed; bottom:20px; left:20px; z-index:1000; background:white; padding:12px; '
    'border:2px solid #ccc; border-radius:6px; font-family:Arial, sans-serif; font-size:12px; '
    'color:#222; max-width:290px; box-shadow:2px 2px 6px rgba(0,0,0,0.2);'
)


def _base_map(location, zoom_start) -> folium.Map:
    m = folium.Map(location=location, zoom_start=zoom_start, tiles='OpenStreetMap')
    folium.TileLayer('Esri.WorldGrayCanvas', name='Light Gray Canvas (Clean View)').add_to(m)
    folium.TileLayer('Esri.WorldStreetMap', name='Esri Street Map').add_to(m)
    return m


def wbr_country_totals(df_monthly: pd.DataFrame, route: str = ROUTE_CODE) -> dict:
    """All-time and last-12-observed-month recorded arrivals per arrival country on a route."""
    data = df_monthly[df_monthly['Route'] == route].dropna(subset=['Date', 'Arrivals']).copy()
    data['Month'] = data['Date'].dt.to_period('M').dt.to_timestamp()
    last_12 = sorted(data['Month'].unique())[-12:]
    recent = data[data['Month'].isin(last_12)]
    return {
        'total_all': int(data['Arrivals'].sum()),
        'total_12m': int(recent['Arrivals'].sum()),
        'by_country_all': data.groupby('ISO3 - Country of arrival')['Arrivals'].sum().to_dict(),
        'by_country_12m': recent.groupby('ISO3 - Country of arrival')['Arrivals'].sum().to_dict(),
        'first_month': data['Month'].min(),
        'last_month': data['Month'].max(),
        'window_start': last_12[0] if last_12 else None,
    }


def build_wbr_map(df_monthly: pd.DataFrame, forecast: pd.Series | None = None,
                  forecast_label: str | None = None) -> folium.Map:
    """Regional WBR map: animated corridors, country circles, border crossing points.

    ``forecast`` is optional; if given, its total is shown in the legend labelled with
    ``forecast_label`` so a Montenegro forecast is never presented as a regional one.
    """
    t = wbr_country_totals(df_monthly)
    period = f"{t['first_month']:%b %Y}–{t['last_month']:%b %Y}"
    recent_period = f"{t['window_start']:%b %Y}–{t['last_month']:%b %Y}"

    m = _base_map([43.0, 19.8], 6)
    fg_routes = folium.FeatureGroup(name='Migration Corridors (illustrative)', show=True)
    fg_countries = folium.FeatureGroup(name='Countries (Recorded Arrivals)', show=True)
    fg_bcps = folium.FeatureGroup(name='Key Border Crossing Points (BCPs)', show=True)

    for corr in CORRIDORS:
        AntPath(
            locations=[COUNTRIES[iso]['coords'] for iso in corr['path'] if iso in COUNTRIES],
            color=corr['color'], weight=corr['weight'], delay=1000, tooltip=corr['label'],
        ).add_to(fg_routes)

    for iso, info in COUNTRIES.items():
        arr_all = int(t['by_country_all'].get(iso, 0))
        arr_12m = int(t['by_country_12m'].get(iso, 0))
        share_all = arr_all / t['total_all'] * 100 if t['total_all'] else 0
        share_12m = arr_12m / t['total_12m'] * 100 if t['total_12m'] else 0
        is_mne = iso == MONTENEGRO_CODE
        radius = max(8, min(15, arr_all ** 0.30)) if arr_all > 0 else 7

        hover = (f"<b>{info['name']} ({iso})</b><br>Total ({period}): <b>{arr_all:,}</b> ({share_all:.1f}%)"
                 f"<br>Last 12 months: <b>{arr_12m:,}</b> ({share_12m:.1f}%)")
        popup = (f"<div><h4>{info['name']} ({iso})</h4><p><b>{period} total:</b> {arr_all:,} ({share_all:.2f}%)</p>"
                 f"<p><b>Last 12 months ({recent_period}):</b> {arr_12m:,} ({share_12m:.2f}%)</p></div>")
        folium.CircleMarker(
            location=info['coords'], radius=radius,
            color='#b30000' if is_mne else '#1f4e78', fill=True,
            fill_color='#ff3333' if is_mne else '#337ab7',
            fill_opacity=0.85 if is_mne else 0.65,
            tooltip=folium.Tooltip(hover), popup=folium.Popup(popup, max_width=280),
        ).add_to(fg_countries)

    for bcp in BORDER_CROSSINGS:
        iso = bcp['country']
        arr_12m = int(t['by_country_12m'].get(iso, 0))
        arr_all = int(t['by_country_all'].get(iso, 0))
        hover = (f"<b>{bcp['name']}</b><br>Corridor: {bcp['corridor']}"
                 f"<br>Receiving country ({iso}) last 12 months: <b>{arr_12m:,}</b>")
        popup = (f"<div><h4>{bcp['name']}</h4><p><b>Corridor:</b> {bcp['corridor']}</p>"
                 f"<p><b>{iso} last 12 months:</b> {arr_12m:,}</p><p><b>{iso} total ({period}):</b> {arr_all:,}</p></div>")
        folium.CircleMarker(
            location=bcp['coords'], radius=5, color='#111111', weight=1.5, fill=True,
            fill_color='#ffd700', fill_opacity=0.95,
            tooltip=folium.Tooltip(hover), popup=folium.Popup(popup, max_width=280),
        ).add_to(fg_bcps)

    for fg in (fg_routes, fg_countries, fg_bcps):
        fg.add_to(m)

    if forecast is not None and len(forecast):
        label = forecast_label or 'Forecast'
        forecast_line = (f"{len(forecast)}-month forecast — {label} "
                         f"({forecast.index.min():%b %Y}–{forecast.index.max():%b %Y}): "
                         f"<b>{int(round(forecast.sum())):,}</b><br>")
    else:
        forecast_line = ''

    legend = "".join([
        f"<div style='{LEGEND_STYLE}'>",
        "<b>Western Balkan Route (WBR)</b><br>",
        f"Total recorded ({period}): <b>{t['total_all']:,}</b><br>",
        f"Last 12 months recorded: <b>{t['total_12m']:,}</b><br>",
        forecast_line,
        "<hr style='margin:6px 0;'>",
        "<b style='color:#2b5c8f;'>━━</b> Central Corridor (MKD - SRB - HRV)<br>",
        "<b style='color:#d9534f;'>━━</b> Coastal Corridor (ALB - MNE - BIH)<br>",
        "<b style='color:#5bc0de;'>━━</b> Eastern Corridor (TUR - BGR - SRB - ROU)<br>",
        "<b style='color:#f0ad4e;'>━━</b> Secondary Branch (SRB - BIH)<br>",
        "<b style='color:#9b59b6;'>━━</b> Kosovo* Branch (MKD - XKX - SRB)<br>",
        "<hr style='margin:6px 0;'>",
        "<span style='color:#c9a800;'>●</span> Key border crossing point<br>",
        "<span style='color:#b30000;'>●</span> Montenegro (focus country)<br>",
        "<span style='color:#1f4e78;'>●</span> Other WBR countries<br>",
        "<i style='color:#666; font-size:10.5px;'>Corridors are illustrative, not tracked journeys. "
        "Arrivals are recorded events, not unique people.</i>",
        "</div>",
    ])
    m.get_root().html.add_child(folium.Element(legend))
    folium.LayerControl(collapsed=False).add_to(m)
    return m


def build_montenegro_map(mne_monthly: pd.Series, forecast: pd.Series | None = None) -> folium.Map:
    """Montenegro detail map: entry/exit points, Podgorica hub and internal corridors.

    Popups show the last 12 observed months of Montenegro WBR arrivals.
    """
    last_12 = mne_monthly.tail(12)
    total_12m = int(last_12.sum())
    window = f"{last_12.index.min():%b %Y} – {last_12.index.max():%b %Y}"

    rows = "".join(
        f"<tr><td style='padding:2px 8px; border-bottom:1px solid #eee;'>{dt:%b %Y}</td>"
        f"<td style='padding:2px 8px; border-bottom:1px solid #eee; text-align:right;'><b>{int(v):,}</b></td></tr>"
        for dt, v in last_12.items()
    )
    table = (
        "<table style='width:100%; border-collapse:collapse; font-size:11px; margin-top:6px;'>"
        "<thead><tr style='background-color:#f2f2f2;'><th style='padding:3px 8px; text-align:left;'>Month</th>"
        "<th style='padding:3px 8px; text-align:right;'>Arrivals</th></tr></thead>"
        f"<tbody>{rows}</tbody></table>"
    )

    m = _base_map([42.75, 19.15], 8)
    fg_routes = folium.FeatureGroup(name='Transit Corridors (illustrative)', show=True)
    fg_points = folium.FeatureGroup(name='Border Points & Hub', show=True)

    for corr in MNE_CORRIDORS:
        AntPath(
            locations=[MNE_POINTS[p]['coords'] for p in corr['path']],
            color=corr['color'], weight=corr['weight'], delay=900, dash_array=(10, 20),
            tooltip=corr['label'],
        ).add_to(fg_routes)

    for key, info in MNE_POINTS.items():
        hover = (f"<b>{info['name']}</b><br>Role: {info['type']}<br>"
                 f"Montenegro total (last 12 months): <b>{total_12m:,}</b><br>"
                 "<i>Click marker for the monthly breakdown</i>")
        popup = (
            f"<div style='font-family:Arial, sans-serif; width:250px;'>"
            f"<h4 style='margin:0 0 4px 0; color:{info['color']};'>{info['name']}</h4>"
            f"<p style='margin:0 0 6px 0; font-size:11px; color:#555;'>{info['desc']}</p>"
            f"<div style='background:#f8f9fa; padding:5px 8px; border-radius:4px; font-size:12px;'>"
            f"Total recorded in MNE ({window}): <b>{total_12m:,}</b></div>{table}</div>"
        )
        folium.CircleMarker(
            location=info['coords'], radius=16 if key == 'PG_HUB' else 10,
            color=info['color'], fill=True, fill_color=info['color'], fill_opacity=0.8,
            tooltip=folium.Tooltip(hover), popup=folium.Popup(popup, max_width=280),
        ).add_to(fg_points)

    fg_routes.add_to(m)
    fg_points.add_to(m)

    forecast_line = ''
    if forecast is not None and len(forecast):
        forecast_line = (f"{len(forecast)}-month forecast ({forecast.index.min():%b %Y}–"
                         f"{forecast.index.max():%b %Y}): <b>{int(round(forecast.sum())):,}</b><br>")

    legend = (
        f"<div style='{LEGEND_STYLE}'>"
        "<b style='font-size:13px; color:#b30000;'>Montenegro — last 12 months</b><br>"
        f"Period: <b>{window}</b><br>"
        f"Total recorded arrivals: <b>{total_12m:,}</b><br>"
        f"Peak month: <b>{last_12.idxmax():%b %Y} ({int(last_12.max()):,})</b><br>"
        f"Lowest month: <b>{last_12.idxmin():%b %Y} ({int(last_12.min()):,})</b><br>"
        f"{forecast_line}"
        "<hr style='margin:6px 0;'>"
        "<span style='color:#d9534f; font-weight:bold;'>━━</span> Main axis (Božaj → PG → Šćepan Polje)<br>"
        "<span style='color:#2b5c8f; font-weight:bold;'>━━</span> Northern exit (PG → Metaljka)<br>"
        "<span style='color:#e67e22; font-weight:bold;'>━━</span> Western exit (Sukobin → Ilino Brdo)<br>"
        "<span style='color:#9b59b6; font-weight:bold;'>━━</span> Coastal exit (Sukobin → Debeli Brijeg)<br>"
        "<i style='color:#666; font-size:10.5px;'>Corridors are illustrative. Hover a point for details; click for the monthly table.</i>"
        "</div>"
    )
    m.get_root().html.add_child(folium.Element(legend))
    folium.LayerControl().add_to(m)
    return m
