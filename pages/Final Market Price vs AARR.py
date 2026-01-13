
# import streamlit as st
# import numpy as np
# import plotly.graph_objects as go
# import pandas as pd
# from utils import compute_aarr

# st.set_page_config(page_title="Covered Call AARR Viewer", layout="wide")

# st.title("\U0001F4CA AARR vs. Final Market Price")

# call = st.session_state.get("selected_call")
# ticker = st.session_state.get("ticker")
# initial_price = st.session_state.get("stock_price")

# if not call:
#     st.error("No covered call selected. Please go back and choose one.")
#     st.stop()

# st.subheader(f"{ticker.upper()} Covered Call")
# st.write(f"**Current Stock Price:** \\${initial_price:.2f}  \n"
#          f"**Strike Price:** \\${call['strike']:.2f}  \n"
#          f"**Premium:** ${call['premium']:.2f}  \n"
#          f"**Expiration:** {pd.to_datetime(call['expiration']).date()}  \n"
#          f"**Days to Expiration:** {call['days_to_expiration']}")

# # --- AARR vs Final Market Price ---
# strike = call['strike']
# premium = call['premium']
# expiry = call['days_to_expiration']
# num_shares = 100

# # NOTE Generate x_prices from 80% to 120% of strike price
# x_prices = np.linspace(strike * 0.8, strike + 1, 100)
# y_aarr = []

# for final_price in x_prices:
#     aarr, *_ = compute_aarr(
#         num_shares=num_shares,
#         initial_market_price=initial_price,
#         strike_price=strike,
#         premium=premium,
#         expiry=expiry,
#         final_market_price=final_price,
#         strike_out=(final_price >= strike)
#     )
#     y_aarr.append(aarr)

# # Determine x_min where AARR ~ 0%
# x_neg_five = next((x for x, y in zip(x_prices, y_aarr) if y >= -5), x_prices[0])
# x_zero = next((x for x, y in zip(x_prices, y_aarr) if y >= 0), x_prices[0])
# x_five = next((x for x, y in zip(x_prices, y_aarr) if y >= 5), x_prices[-1])

# fig = go.Figure()

# fig.add_trace(go.Scatter(
#     x=x_prices,
#     y=y_aarr,
#     mode='lines',
#     name='AARR',
#     line=dict(color='orange', width=2),
#     hovertemplate='Price: $%{x:.2f}<br>AARR: %{y:.2f}%'
# ))

# # Vertical line at strike price
# fig.add_vline(
#     x=strike,
#     line=dict(color='gray', dash='dash'),
#     annotation_text=f"Strike (${strike:.2f})",
#     annotation_position="top right"
# )

# # Green line at AARR ~ 5%
# fig.add_vline(
#     x=x_five,
#     line=dict(color='green', dash='dot'),
#     annotation_text=f"AARR ≈ 5% (${x_five:.2f})",
#     annotation_position="bottom right"
# )

# # Red line at AARR ~ 0%
# fig.add_vline(
#     x=x_zero,
#     line=dict(color='red', dash='dot'),
#     annotation_text=f"AARR ≈ 0% (${x_zero:.2f})",
#     annotation_position="top left"
# )

# y_pad = (max(y_aarr) - min(y_aarr)) * 0.1
# fig.update_layout(
#     title="AARR vs Final Market Price",
#     xaxis_title="Final Market Price at Expiry",
#     yaxis_title="AARR (%)",
#     xaxis_range=[x_neg_five, x_prices[-1]],
#     yaxis_range=[min(y_aarr) - y_pad, max(y_aarr) + y_pad],
#     height=500,
#     margin=dict(l=60, r=60, t=50, b=40),
#     hovermode="x unified",
#     template="plotly_white"
# )

# # fig.set_width(400)

# # st.plotly_chart(fig, use_container_width=True)
# st.plotly_chart(fig, use_container_width=True)

# if st.button("← Back to Calls"):
#     st.switch_page("Home.py")

import streamlit as st
import numpy as np
import plotly.graph_objects as go
import pandas as pd
from utils import compute_aarr

st.set_page_config(page_title="Covered Call AARR Viewer", layout="wide")

st.title("📊 AARR vs. Final Market Price")

call = st.session_state.get("selected_call")
ticker = st.session_state.get("ticker")
initial_price = st.session_state.get("stock_price")

if not call:
    st.error("No covered call selected. Please go back and choose one.")
    st.stop()

st.subheader(f"{ticker.upper()} Covered Call")

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Current Price", f"${initial_price:.2f}")
    st.metric("Strike Price", f"${call['strike']:.2f}")
with col2:
    st.metric("Premium", f"${call['premium']:.2f}")
    st.metric("Days to Expiry", call['days_to_expiration'])
with col3:
    breakeven = initial_price - call['premium']
    st.metric("Breakeven Price", f"${breakeven:.2f}")
    pct_otm = ((call['strike'] - initial_price) / initial_price) * 100
    st.metric("% Out of Money", f"{pct_otm:.1f}%")

# --- AARR vs Final Market Price ---
strike = call['strike']
premium = call['premium']
expiry = call['days_to_expiration']
num_shares = 100

# Generate x_prices from 50% to 300% of current price
x_prices = np.linspace(initial_price * 0.5, initial_price * 3, 300)
y_aarr_covered = []
y_aarr_hold = []

for final_price in x_prices:
    # Covered call AARR
    aarr_cc, *_ = compute_aarr(
        num_shares=num_shares,
        initial_market_price=initial_price,
        strike_price=strike,
        premium=premium,
        expiry=expiry,
        final_market_price=final_price,
        strike_out=(final_price >= strike)
    )
    y_aarr_covered.append(aarr_cc)
    
    # Just hold stock AARR (no premium, no strike cap)
    aarr_hold, *_ = compute_aarr(
        num_shares=num_shares,
        initial_market_price=initial_price,
        strike_price=final_price,  # No cap
        premium=0,  # No premium
        expiry=expiry,
        final_market_price=final_price,
        strike_out=True
    )
    y_aarr_hold.append(aarr_hold)

# Find key points
x_zero = next((x for x, y in zip(x_prices, y_aarr_covered) if y >= 0), x_prices[0])
x_breakeven_vs_hold = next((x for x, (yc, yh) in enumerate(zip(y_aarr_covered, y_aarr_hold)) 
                            if yc <= yh and x >= initial_price), strike)

fig = go.Figure()

# Covered call line
fig.add_trace(go.Scatter(
    x=x_prices,
    y=y_aarr_covered,
    mode='lines',
    name='Covered Call',
    line=dict(color='orange', width=3),
    hovertemplate='Price: $%{x:.2f}<br>AARR: %{y:.2f}%<extra></extra>'
))

# Hold stock line
fig.add_trace(go.Scatter(
    x=x_prices,
    y=y_aarr_hold,
    mode='lines',
    name='Just Hold Stock',
    line=dict(color='cyan', width=2, dash='dot'),
    hovertemplate='Price: $%{x:.2f}<br>AARR: %{y:.2f}%<extra></extra>'
))

# Current price line
fig.add_vline(
    x=initial_price,
    line=dict(color='red', dash='dash', width=1),
    annotation_text=f"Current (${initial_price:.2f})",
    annotation_position="top left"
)

# Strike price line
fig.add_vline(
    x=strike,
    line=dict(color='gray', dash='dash', width=2),
    annotation_text=f"Strike (${strike:.2f})",
    annotation_position="top right"
)

# Zero AARR line (breakeven)
fig.add_hline(
    y=0,
    line=dict(color='white', dash='dot', width=1),
    annotation_text="0% Return",
    annotation_position="right"
)

# Dynamic y-axis range with padding
y_min = min(min(y_aarr_covered), min(y_aarr_hold))
y_max = max(max(y_aarr_covered), max(y_aarr_hold))
y_pad = (y_max - y_min) * 0.1

fig.update_layout(
    title="AARR vs Final Market Price at Expiry",
    xaxis_title="Final Market Price at Expiry",
    yaxis_title="AARR (%)",
    yaxis_range=[y_min - y_pad, y_max + y_pad],
    height=600,
    margin=dict(l=60, r=60, t=80, b=60),
    hovermode="x unified",
    template="plotly_dark",
    legend=dict(
        yanchor="top",
        y=0.99,
        xanchor="left",
        x=0.01
    )
)

st.plotly_chart(fig, use_container_width=True)

# Analysis
st.subheader("Analysis")
col1, col2 = st.columns(2)
with col1:
    st.write(f"**Breakeven price:** ${x_zero:.2f} ({((x_zero - initial_price) / initial_price * 100):.1f}% change)")
    st.write(f"**Max profit at strike:** {max(y_aarr_covered):.2f}% AARR")
with col2:
    st.write(f"**Downside protection:** ${premium:.2f} per share cushion")
    if x_breakeven_vs_hold > initial_price:
        st.write(f"**Covered call wins below:** ${x_breakeven_vs_hold:.2f}")
    else:
        st.write("**Warning:** Holding stock may be better at most price points")

if st.button("← Back to Calls"):
    st.switch_page("Home.py")