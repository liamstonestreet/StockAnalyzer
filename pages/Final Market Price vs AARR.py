
import streamlit as st
import numpy as np
import plotly.graph_objects as go
import pandas as pd
from utils import compute_aarr

st.set_page_config(page_title="Covered Call AARR Viewer", layout="wide")

st.title("\U0001F4CA AARR vs. Final Market Price")

call = st.session_state.get("selected_call")
ticker = st.session_state.get("ticker")
initial_price = st.session_state.get("stock_price")

if not call:
    st.error("No covered call selected. Please go back and choose one.")
    st.stop()

st.subheader(f"{ticker.upper()} Covered Call")
st.write(f"**Strike Price:** \\${call['strike']:.2f}  \n"
         f"**Premium:** ${call['premium']:.2f}  \n"
         f"**Expiration:** {pd.to_datetime(call['expiration']).date()}  \n"
         f"**Days to Expiration:** {call['days_to_expiration']}")

# --- AARR vs Final Market Price ---
strike = call['strike']
premium = call['premium']
expiry = call['days_to_expiration']
num_shares = 100

# NOTE Generate x_prices from 80% to 120% of strike price
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

# Determine x_min where AARR ~ 0%
x_neg_five = next((x for x, y in zip(x_prices, y_aarr) if y >= -5), x_prices[0])
x_zero = next((x for x, y in zip(x_prices, y_aarr) if y >= 0), x_prices[0])
x_five = next((x for x, y in zip(x_prices, y_aarr) if y >= 5), x_prices[-1])

fig = go.Figure()

fig.add_trace(go.Scatter(
    x=x_prices,
    y=y_aarr,
    mode='lines',
    name='AARR',
    line=dict(color='orange', width=2),
    hovertemplate='Price: $%{x:.2f}<br>AARR: %{y:.2f}%'
))

fig.add_vline(
    x=strike,
    line=dict(color='gray', dash='dash'),
    annotation_text=f"Strike (${strike:.2f})",
    annotation_position="top right"
)

fig.add_vline(
    x=x_five,
    line=dict(color='green', dash='dot'),
    annotation_text=f"AARR ≈ 5% (${x_five:.2f})",
    annotation_position="bottom right"
)

fig.add_vline(
    x=x_zero,
    line=dict(color='red', dash='dot'),
    annotation_text=f"AARR ≈ 0% (${x_zero:.2f})",
    annotation_position="top left"
)

fig.update_layout(
    title="AARR vs Final Market Price",
    xaxis_title="Final Market Price at Expiry",
    yaxis_title="AARR (%)",
    xaxis_range=[x_neg_five, x_prices[-1]],
    height=500,
    margin=dict(l=40, r=40, t=50, b=40),
    hovermode="x unified",
    template="plotly_white"
)

st.plotly_chart(fig, use_container_width=True)

if st.button("← Back to Calls"):
    st.switch_page("Home.py")
