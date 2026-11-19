"""Shared Plotly styling so every chart in the app reads as one system.

Colors are the validated reference categorical palette, assigned in fixed order
and never cycled; text stays in ink colors, not series colors.
"""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

# Categorical slots, fixed order (light surface).
SERIES = ['#2a78d6', '#eb6834', '#1baf7a', '#eda100', '#e87ba4', '#008300', '#6250d6', '#e34948']
BLUE, ORANGE, AQUA, YELLOW = SERIES[:4]
MUTED = '#a3a29c'
INK = '#0b0b0b'
INK_2 = '#52514e'
GRID = '#e6e5e1'

# Fixed colour per model, used in every chart: colour follows the entity, never its rank.
MODEL_COLORS = {
    'Linear Regression': SERIES[0],
    'Ridge Regression': SERIES[1],
    'Random Forest': SERIES[2],
    'Seasonal Naive': SERIES[3],
}
HISTORY = INK_2

FONT = dict(family='-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif', size=13, color=INK_2)


def style(fig: go.Figure, title: str | None = None, y_title: str = 'Recorded arrivals',
          height: int = 380, hover: str = 'x unified', legend: bool = True) -> go.Figure:
    fig.update_layout(
        title=dict(text=title, font=dict(size=15, color=INK), x=0, xanchor='left') if title else None,
        height=height,
        margin=dict(l=8, r=8, t=48 if title else 16, b=8),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=FONT,
        hovermode=hover,
        hoverlabel=dict(bgcolor='white', font=dict(color=INK)),
        showlegend=legend,
        legend=dict(orientation='h', yanchor='top', y=-0.12, xanchor='left', x=0, title=None),
    )
    fig.update_xaxes(showgrid=False, linecolor=GRID, ticks='outside', tickcolor=GRID, title=None)
    fig.update_yaxes(gridcolor=GRID, zeroline=False, rangemode='tozero', title=y_title,
                     separatethousands=True, tickformat=',d')
    return fig


def line(fig: go.Figure, x, y, name: str, color: str, dash: str | None = None,
         markers: bool = False, hover_fmt: str = ',.0f') -> go.Figure:
    fig.add_trace(go.Scatter(
        x=x, y=y, name=name, mode='lines+markers' if markers else 'lines',
        line=dict(color=color, width=2, dash=dash),
        marker=dict(size=8, line=dict(color='white', width=2)),
        hovertemplate=f'%{{y:{hover_fmt}}}',
    ))
    return fig


def series_line(series: pd.Series, name: str, color: str = BLUE, title: str | None = None) -> go.Figure:
    fig = line(go.Figure(), series.index, series.values, name, color)
    return style(fig, title, legend=False)
