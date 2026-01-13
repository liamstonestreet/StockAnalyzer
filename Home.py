import streamlit as st
import pandas as pd
import yfinance as yf
import options
import utils

HOME_PAGE = "Home.py"
AARR_PAGE = "pages/Final Market Price vs AARR.py"

st.set_page_config(page_title="Covered Call Viewer", layout="wide", page_icon="📈")

st.title("📈 Covered Call Analyzer")
st.markdown("Find optimal covered call opportunities with probability-weighted analysis")

# Ticker input
col_ticker, col_price, col_vol = st.columns([2, 1, 1])
with col_ticker:
    ticker = st.text_input("Stock Ticker", value="AAPL", key="ticker_input")

# Show current market price and volatility
market_price = None
volatility = None

with col_price:
    if ticker:
        with st.spinner("Loading..."):
            market_price = utils.get_market_price(ticker)
        if market_price:
            st.metric("Current Price", f"${market_price:.2f}")
        else:
            st.warning("Unable to fetch price")

with col_vol:
    if ticker:
        with st.spinner("Loading..."):
            volatility = utils.get_historical_volatility(ticker)
        if volatility:
            st.metric("30d Volatility", f"{volatility*100:.1f}%")
        else:
            st.info("No volatility data")

# with col_vol:
#     if ticker:
#         with st.spinner("Loading..."):
#             # Try IV first, fall back to HV
#             volatility = utils.get_implied_volatility_from_options(ticker, 30)
#             if not volatility:
#                 volatility = utils.get_historical_volatility(ticker)
#         if volatility:
#             st.metric("Implied Vol", f"{volatility*100:.1f}%")

st.divider()

# Filters
st.subheader("🔍 Filters")

col1, col2 = st.columns(2)
with col1:
    first_exp = st.slider("First Expiration (days)", 0, 180, 30)
with col2:
    last_exp = st.slider("Last Expiration (days)", first_exp, 365, 90)

with st.expander("Advanced Filters", expanded=False):
    col3, col4 = st.columns(2)
    with col3:
        st.markdown("**Minimum Values**")
        min_strike_price = st.number_input("Min Strike Price", value=0.0, format="%.2f")
        min_premium = st.number_input("Min Premium", value=0.0, format="%.2f")
        min_aarr = st.number_input("Min AARR %", value=15.0, format="%.2f")
    with col4:
        st.markdown("**Maximum Values**")
        max_strike_price = st.number_input("Max Strike Price", value=99999.0, format="%.2f")
        max_premium = st.number_input("Max Premium", value=99999.0, format="%.2f")
        max_aarr = st.number_input("Max AARR %", value=200.0, format="%.2f")
    
    st.divider()
    
    # Call type filter
    st.markdown("**Filter by Call Type**")
    call_type_filter = st.multiselect(
        "Show only these types:",
        ["🔴 Deep ITM", "🟠 ITM", "🟡 ATM", "🟢 OTM", "🟢 Deep OTM"],
        default=["🔴 Deep ITM", "🟠 ITM", "🟡 ATM", "🟢 OTM", "🟢 Deep OTM"]
    )

# Sort option
sort_by = st.selectbox("Sort by", [
    "AARR (Highest)", 
    "AARR (Lowest)", 
    "Premium (Highest)", 
    "Days to Expiry (Soonest)",
    "Safety Score (Safest First)"
])

# Fetch button
if st.button("🔎 Fetch Covered Calls", type="primary", use_container_width=True):
    with st.spinner("Fetching options data..."):
        try:
            chain = options.fetch_options_chain(ticker, first_expiration=first_exp, last_expiration=last_exp)
            
            # Add call type classification
            def classify_call(row):
                strike = row['strike']
                if strike < market_price * 0.95:
                    return "🔴 Deep ITM"
                elif strike < market_price:
                    return "🟠 ITM"
                elif strike <= market_price * 1.05:
                    return "🟡 ATM"
                elif strike <= market_price * 1.15:
                    return "🟢 OTM"
                else:
                    return "🟢 Deep OTM"
            
            chain['call_type'] = chain.apply(classify_call, axis=1)
            
            # Calculate safety score (higher = safer)
            # Safety = premium yield + inverse of how far strike is from current price
            if volatility:
                # With volatility: factor in probability of reaching max AARR price
                chain['safety_score'] = chain.apply(
                    lambda row: (row['premium'] / market_price * 100) * 
                                (1 - abs(row['strike'] - market_price) / market_price),
                    axis=1
                )
            else:
                # Without volatility: just use premium yield and distance from current
                chain['safety_score'] = chain.apply(
                    lambda row: (row['premium'] / market_price * 100) * 
                                (1 - abs(row['strike'] - market_price) / market_price),
                    axis=1
                )
            
            # Apply call type filter
            if call_type_filter:
                chain = chain[chain['call_type'].isin(call_type_filter)]
            
            # Apply other filters
            if min_strike_price > 0:
                chain = chain[chain["strike"] >= min_strike_price]
            if max_strike_price > 0:
                chain = chain[chain["strike"] <= max_strike_price]
            if min_premium > 0:
                chain = chain[chain["premium"] >= min_premium]
            if max_premium > 0:
                chain = chain[chain["premium"] <= max_premium]
            if min_aarr > 0:
                chain = chain[chain["aarr"] >= min_aarr]
            if max_aarr > 0:
                chain = chain[chain["aarr"] <= max_aarr]
            
            # Sort
            if sort_by == "AARR (Highest)":
                chain = chain.sort_values("aarr", ascending=False)
            elif sort_by == "AARR (Lowest)":
                chain = chain.sort_values("aarr", ascending=True)
            elif sort_by == "Premium (Highest)":
                chain = chain.sort_values("premium", ascending=False)
            elif sort_by == "Days to Expiry (Soonest)":
                chain = chain.sort_values("days_to_expiration", ascending=True)
            elif sort_by == "Safety Score (Safest First)":
                chain = chain.sort_values("safety_score", ascending=False)

            chain.reset_index(drop=True, inplace=True)
            st.session_state["options_chain"] = chain
            st.session_state["ticker"] = ticker
            st.session_state["stock_price"] = market_price
            st.session_state["volatility"] = volatility

            st.success(f"✅ Found {len(chain)} covered calls")

        except Exception as e:
            st.error(f"❌ Error fetching options: {e}")

# Render results
if "options_chain" in st.session_state:
    chain = st.session_state["options_chain"]
    ticker = st.session_state["ticker"]
    
    st.divider()
    
    # Summary stats
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Results", len(chain))
    with col2:
        st.metric("Avg AARR", f"{chain['aarr'].mean():.1f}%")
    with col3:
        st.metric("Avg Premium", f"${chain['premium'].mean():.2f}")
    with col4:
        st.metric("Avg Days", f"{chain['days_to_expiration'].mean():.0f}")
    
    st.divider()
    
    # Export button
    csv = chain.to_csv(index=False)
    st.download_button(
        label="📥 Download Results as CSV",
        data=csv,
        file_name=f"{ticker}_covered_calls.csv",
        mime="text/csv",
    )
    
    st.markdown("### Results")
    
    # Results list
    for idx, row in chain.iterrows():
        strike = row["strike"]
        premium = row["premium"]
        exp = row["expiration"].date()
        aarr = row["aarr"]
        days = row["days_to_expiration"]
        call_type = row["call_type"]
        safety_score = row.get("safety_score", 0)
        
        # Badge color based on call type
        if call_type == "🔴 Deep ITM":
            badge_color = "#ff4444"
        elif call_type == "🟠 ITM":
            badge_color = "#ff8800"
        elif call_type == "🟡 ATM":
            badge_color = "#ffbb00"
        elif call_type == "🟢 OTM":
            badge_color = "#44ff44"
        else:  # Deep OTM
            badge_color = "#00ff88"
        
        with st.container():
            st.markdown(f"""
                <div style="
                    border: 1px solid rgba(255, 255, 255, 0.15);
                    border-radius: 12px;
                    padding: 16px 24px;
                    margin-bottom: 12px;
                    background: linear-gradient(135deg, rgba(255, 255, 255, 0.02), rgba(255, 255, 255, 0.01));
                ">
            """, unsafe_allow_html=True)
            
            cols = st.columns([1, 3, 2, 2, 2, 3, 1.5])
            with cols[0]:
                st.markdown(f"<span style='color: {badge_color}; font-weight: bold;'>{call_type}</span>", unsafe_allow_html=True)
            with cols[1]:
                st.markdown(f"**Strike:** ${strike:.2f}")
            with cols[2]:
                st.markdown(f"**Premium:** ${premium:.2f}")
            with cols[3]:
                st.markdown(f"**Days:** {days}")
            with cols[4]:
                st.markdown(f"**Expires:** {exp}")
            with cols[5]:
                aarr_color = "#44ff44" if aarr >= 20 else "#ffbb00" if aarr >= 10 else "#ffffff"
                st.markdown(f"<span style='color: {aarr_color}; font-weight: bold;'>AARR: {aarr:.1f}%</span><br><span style='color: #888; font-size: 0.85em;'>Safety: {safety_score:.1f}</span>", unsafe_allow_html=True)
            with cols[6]:
                if st.button("View 📊", key=f"btn_{idx}", use_container_width=True):
                    st.session_state["selected_call"] = row.to_dict()
                    st.switch_page(AARR_PAGE)
            
            st.markdown("</div>", unsafe_allow_html=True)