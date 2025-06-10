# nicegui_app/aarr_graph.py

from nicegui import ui
import plotly.graph_objects as go
import numpy as np
import pandas as pd
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils import compute_aarr

def show_graph(call, ticker, initial_price):
    ui.page('/graph')

    ui.label(f'{ticker.upper()} Covered Call').classes('text-2xl font-bold')
    ui.markdown(
        f"**Strike Price:** ${call['strike']:.2f}  \n"
        f"**Premium:** ${call['premium']:.2f}  \n"
        f"**Expiration:** {pd.to_datetime(call['expiration']).date()}  \n"
        f"**Days to Expiration:** {call['days_to_expiration']}"
    )

    strike = call['strike']
    premium = call['premium']
    expiry = call['days_to_expiration']
    num_shares = 100

    x_prices = np.linspace(strike * 0.8, strike + 1, 100)
    y_aarr = []

    for final_price in x_prices:
        aarr, *_ = compute_aarr(
            num_shares=num_shares,
            initial_market_price=initial_price,
            strike_price=strike,
            premium=premium,
            expiry=expiry,
            final_market_price=final_price,
            strike_out=(final_price >= strike)
        )
        y_aarr.append(aarr)

    x_neg_five = next((x for x, y in zip(x_prices, y_aarr) if y >= -5), x_prices[0])
    x_zero = next((x for x, y in zip(x_prices, y_aarr) if y >= 0), x_prices[0])
    x_five = next((x for x, y in zip(x_prices, y_aarr) if y >= 5), x_prices[-1])

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x_prices, y=y_aarr, mode='lines', name='AARR', line=dict(color='orange')))
    fig.add_vline(x=strike, line=dict(color='gray', dash='dash'), annotation_text=f"Strike (${strike:.2f})", annotation_position="top right")
    fig.add_vline(x=x_five, line=dict(color='green', dash='dot'), annotation_text=f"AARR ≈ 5% (${x_five:.2f})", annotation_position="bottom right")
    fig.add_vline(x=x_zero, line=dict(color='red', dash='dot'), annotation_text=f"AARR ≈ 0% (${x_zero:.2f})", annotation_position="top left")

    fig.update_layout(title="AARR vs Final Market Price",
                      xaxis_title="Final Market Price at Expiry",
                      yaxis_title="AARR (%)",
                      xaxis_range=[x_neg_five, x_prices[-1]],
                      height=500,
                      template="plotly_white")

    ui.plotly(fig)
    # TODO fix 'ui.open' does not exist
    ui.button('← Back', on_click=lambda: ui.open('/')).props('color=secondary')
