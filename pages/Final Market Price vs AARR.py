import streamlit as st
import numpy as np
import plotly.graph_objects as go
import pandas as pd
from utils import compute_aarr, compute_hold_aarr, calculate_price_probabilities
import utils

st.set_page_config(page_title="Covered Call AARR Viewer", layout="wide")

st.title("📊 AARR vs. Final Market Price")

call = st.session_state.get("selected_call")
ticker = st.session_state.get("ticker")
initial_price = st.session_state.get("stock_price")
volatility = st.session_state.get("volatility")

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
# NOTE x range is determined here!
x_prices = np.linspace(initial_price * 0.5, initial_price * 1.5, 300) # TODO experiment with 300
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
    
    # Just hold stock AARR
    aarr_hold, *_ = compute_hold_aarr(
        num_shares=num_shares,
        initial_market_price=initial_price,
        final_market_price=final_price,
        days=expiry + 3
    )
    y_aarr_hold.append(aarr_hold)

# Calculate probabilities
probabilities = calculate_price_probabilities(initial_price, x_prices, expiry, volatility)

# Find key points
x_zero = next((x for x, y in zip(x_prices, y_aarr_covered) if y >= 0), x_prices[0])
# x_breakeven_vs_hold = next((x for x, (yc, yh) in enumerate(zip(y_aarr_covered, y_aarr_hold)) 
#                             if yc <= yh and x >= initial_price), strike)
# Find where covered call AARR drops below hold stock AARR (going upward from current price)
x_breakeven_vs_hold = strike  # Default to strike if never crosses
for i, (price, yc, yh) in enumerate(zip(x_prices, y_aarr_covered, y_aarr_hold)):
    if price >= initial_price and yc <= yh:
        x_breakeven_vs_hold = price
        break

# Find max AARR point
max_aarr_idx = np.argmax(y_aarr_covered)
x_max_aarr = x_prices[max_aarr_idx]
y_max_aarr = y_aarr_covered[max_aarr_idx]

# Calculate expected AARR (probability-weighted)
expected_aarr_covered = np.average(y_aarr_covered, weights=probabilities)
expected_aarr_hold = np.average(y_aarr_hold, weights=probabilities)

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

# Dynamic x-axis range with padding
# x_min = min(min(x_prices), initial_price * 0.5)
# x_max = max(max(x_prices), initial_price * 1.5)
# x_pad = (x_max - x_min) * 0.1

# Dynamic y-axis range with padding
y_min = min(min(y_aarr_covered), min(y_aarr_hold))
y_max = min(max(y_aarr_covered), max(y_aarr_hold))
y_pad = (y_max - y_min) * 0.1

# Probability density curve (fill between lines, not separate trace)
if volatility:
    # Create filled area showing probability distribution
    # Normalize probabilities to 0-1 range for opacity
    norm_probs = probabilities / probabilities.max()
    
    # Add subtle shading in high-probability regions
    for i in range(len(x_prices) - 1):
        if norm_probs[i] > 0.3:  # Only shade likely regions
            fig.add_shape(
                type="rect",
                x0=x_prices[i],
                x1=x_prices[i+1],
                y0=y_min - y_pad,
                y1=y_max + y_pad,
                fillcolor=f"rgba(100, 150, 255, {norm_probs[i] * 0.15})",
                line=dict(width=0),
                layer="below"
            )

# Current price line (add to legend)
fig.add_trace(go.Scatter(
    x=[initial_price, initial_price],
    y=[y_min - y_pad, y_max + y_pad],
    mode='lines',
    name='Current Price',
    line=dict(color='red', dash='dash', width=1),
    hovertemplate=f'Current: ${initial_price:.2f}<extra></extra>',
    showlegend=True
))

# Strike price line (add to legend)
fig.add_trace(go.Scatter(
    x=[strike, strike],
    y=[y_min - y_pad, y_max + y_pad],
    mode='lines',
    name='Strike Price',
    line=dict(color='gray', dash='dash', width=2),
    hovertemplate=f'Strike: ${strike:.2f}<extra></extra>',
    showlegend=True
))

# Max AARR point
fig.add_trace(go.Scatter(
    x=[x_max_aarr],
    y=[y_max_aarr],
    mode='markers+text',
    marker=dict(color='lime', size=12, symbol='star'),
    text=[f"Max: {y_max_aarr:.1f}%<br>@ ${x_max_aarr:.2f}"],
    textposition="top center",
    textfont=dict(color='lime', size=11),
    showlegend=False,
    hovertemplate=f'<b>Max AARR Point</b><br>Price: ${x_max_aarr:.2f}<br>AARR: {y_max_aarr:.2f}%<extra></extra>'
))

# Zero AARR line (breakeven)
fig.add_hline(
    y=0,
    line=dict(color='purple', dash='dot', width=1),
    annotation_text="0% Return",
    annotation_position="right"
)

fig.update_layout(
    title="AARR vs Final Market Price at Expiry",
    xaxis_title="Final Market Price at Expiry",
    yaxis_title="AARR (%)",
    #xaxis=dict(range=[x_min - x_pad, x_max + x_pad], dtick=25),
    yaxis=dict(range=[y_min - y_pad, y_max + 2*y_pad], dtick=25),
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
st.subheader("📋 Analysis")

# Determine if ITM, ATM, or OTM
if strike < initial_price * 0.95:
    call_type = "🔴 Deep ITM (In-The-Money)"
    call_explanation = "This call is guaranteed to execute. You're essentially selling now at a discount but getting paid a huge premium upfront."
elif strike < initial_price:
    call_type = "🟠 ITM (In-The-Money)"
    call_explanation = "This call is very likely to execute. Lower upside potential but higher income now."
elif strike <= initial_price * 1.05:
    call_type = "🟡 ATM (At-The-Money)"
    call_explanation = "Balanced risk/reward. Good premium with reasonable upside if stock rises."
else:
    call_type = "🟢 OTM (Out-Of-The-Money)"
    call_explanation = "Lower premium but you keep shares if stock doesn't rise above strike."

st.info(f"**Call Type:** {call_type}\n\n{call_explanation}")

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Breakeven Price", f"${x_zero:.2f}", 
              f"{((x_zero - initial_price) / initial_price * 100):.1f}%",
              delta_color="inverse")
with col2:
    st.metric("Max AARR", f"{y_max_aarr:.2f}%",
              f"@ ${x_max_aarr:.2f}")
with col3:
    premium_yield = (premium / initial_price) * 100
    st.metric("Premium Yield", f"{premium_yield:.1f}%")

# Calculate safety score for this specific call
# safety_score_raw = calculate_safety_score(
#     strike=strike,
#     premium=premium,
#     market_price=initial_price,
#     days_to_expiry=expiry,
#     volatility=volatility
# )
# all_raw_scores = st.session_state.get("all_safety_scores_raw", [safety_score_raw])
# safety_normalized = normalize_safety_score(safety_score_raw, all_raw_scores)

# Don't recalculate - just get the value that was already computed
selected_call = st.session_state.get("selected_call")
safety_normalized = selected_call.get("safety_score", 5.0)  # It's already in the dict!

# Color code based on score
if safety_normalized >= 7:
    delta_label = "Very Safe"
    delta_color = "normal"
elif safety_normalized >= 4:
    delta_label = "Moderate"
    delta_color = "off"
else:
    delta_label = "Risky"
    delta_color = "inverse"

st.metric("Safety Score", f"{safety_normalized}/10", delta_label, delta_color=delta_color)

# Expected value analysis
if volatility:
    st.divider()
    st.markdown("### 🎲 Probability-Weighted Expected Returns")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Expected AARR (Covered Call)", f"{expected_aarr_covered:.2f}%")
    with col2:
        st.metric("Expected AARR (Hold Stock)", f"{expected_aarr_hold:.2f}%")
    
    if expected_aarr_covered > expected_aarr_hold:
        st.success(f"✅ Covered call has {expected_aarr_covered - expected_aarr_hold:.1f}% higher expected return")
    else:
        st.warning(f"⚠️ Holding stock has {expected_aarr_hold - expected_aarr_covered:.1f}% higher expected return")
    
    st.caption(f"Based on {volatility*100:.1f}% historical volatility over {expiry} days")

# Key insights
st.divider()
st.write("**Key Insights:**")

# Calculate position values
initial_investment = initial_price * num_shares
premium_received = premium * num_shares
strike_proceeds = strike * num_shares if strike < initial_price else 0
total_received = premium_received + (strike_proceeds if strike_proceeds > 0 else initial_price * num_shares)
net_gain = total_received - initial_investment

# Investment overview
st.write(f"- 💵 **Investment:** \\${initial_investment:,.2f} ({num_shares} shares @ \\${initial_price:.2f})")
st.write(f"- 💰 **Returns:** \\${total_received:,.2f} total (\\${premium_received:,.2f} premium + \
         \\${strike_proceeds if strike_proceeds > 0 else initial_investment:,.2f} shares)")

# Profit/loss and protection
if net_gain > 0:
    st.write(f"- ✅ **Net gain:** \\${net_gain:,.2f} ({(net_gain/initial_investment)*100:.1f}%) • Downside protected to \\${x_zero:.2f}")
else:
    st.write(f"- ❌ **Net loss:** \\${abs(net_gain):,.2f} ({(net_gain/initial_investment)*100:.1f}%) • Downside protected to \\${x_zero:.2f}")

# Optimal price and comparison
st.write(f"- 🎯 **Max AARR:** \\${x_max_aarr:.2f} ({((x_max_aarr - initial_price) / initial_price * 100):.1f}% move)")
if x_breakeven_vs_hold > initial_price:
    st.write(f"- 📈 **Strategy:** Beats holding if price stays below \\${x_breakeven_vs_hold:.2f}")
else:
    st.warning("⚠️ Holding stock may outperform at most price points")

# Back button
if st.button("← Back to Calls"):
    st.switch_page("Home.py")