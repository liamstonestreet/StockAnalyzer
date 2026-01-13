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
# col_ticker, col_price, col_vol = st.columns([2, 1, 1])
# with col_ticker:
#     ticker = st.text_input("Stock Ticker", value="AAPL", key="ticker_input")
# Ticker input
col_ticker, col_price, col_vol = st.columns([2, 1, 1])
with col_ticker:
    # Initialize session state for ticker if not exists
    if "saved_ticker" not in st.session_state:
        st.session_state.saved_ticker = "AAPL"
    
    ticker = st.text_input("Stock Ticker", 
                          value=st.session_state.saved_ticker, 
                          key="ticker_input",
                          on_change=lambda: st.session_state.update({"saved_ticker": st.session_state.ticker_input}))

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

# Historical volatility
with col_vol:
    if ticker:
        with st.spinner("Loading..."):
            volatility = utils.get_historical_volatility(ticker)
        if volatility:
            st.metric("30d Volatility", f"{volatility*100:.1f}%")
        else:
            st.info("No volatility data")

# Implied volatility (commented out for now)
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

# Initialize filter defaults in session state
if "saved_first_exp" not in st.session_state:
    st.session_state["saved_first_exp"] = 30
if "saved_last_exp" not in st.session_state:
    st.session_state["saved_last_exp"] = 90
if "min_strike_price" not in st.session_state:
    st.session_state["min_strike_price"] = 0.0
if "max_strike_price" not in st.session_state:
    st.session_state["max_strike_price"] = 99999.0
if "min_premium" not in st.session_state:
    st.session_state["min_premium"] = 0.0
if "max_premium" not in st.session_state:
    st.session_state["max_premium"] = 99999.0
if "min_aarr" not in st.session_state:
    st.session_state["min_aarr"] = 15.0
if "max_aarr" not in st.session_state:
    st.session_state["max_aarr"] = 200.0
if "call_type_filter" not in st.session_state:
    st.session_state["call_type_filter"] = ["🔴 Deep ITM", "🟠 ITM", "🟡 ATM", "🟢 OTM", "🟢 Deep OTM"]
if "sort_by" not in st.session_state:
    st.session_state["sort_by"] = "AARR (Highest)"

col1, col2 = st.columns(2)
with col1:
    first_exp = st.slider("First Expiration (days)", 0, 180, 
                         st.session_state["saved_first_exp"],
                         key="first_exp_slider",
                         on_change=lambda: st.session_state.update({"saved_first_exp": st.session_state["first_exp_slider"]}))
with col2:
    last_exp = st.slider("Last Expiration (days)", first_exp, 365, 
                        st.session_state["saved_last_exp"],
                        key="last_exp_slider",
                        on_change=lambda: st.session_state.update({"saved_last_exp": st.session_state["last_exp_slider"]}))

with st.expander("Advanced Filters", expanded=False):
    col3, col4 = st.columns(2)
    with col3:
        st.markdown("**Minimum Values**")
        min_strike_price = st.number_input("Min Strike Price", 
                                           value=st.session_state["min_strike_price"], 
                                           format="%.2f",
                                           key="min_strike_price_input",
                                           on_change=lambda: st.session_state.update({"min_strike_price": st.session_state["min_strike_price_input"]}))
        min_premium = st.number_input("Min Premium", 
                                      value=st.session_state["min_premium"], 
                                      format="%.2f",
                                      key="min_premium_input",
                                      on_change=lambda: st.session_state.update({"min_premium": st.session_state["min_premium_input"]}))
        min_aarr = st.number_input("Min AARR %", 
                                   value=st.session_state["min_aarr"], 
                                   format="%.2f",
                                   key="min_aarr_input",
                                   on_change=lambda: st.session_state.update({"min_aarr": st.session_state["min_aarr_input"]}))
    with col4:
        st.markdown("**Maximum Values**")
        max_strike_price = st.number_input("Max Strike Price", 
                                           value=st.session_state["max_strike_price"], 
                                           format="%.2f",
                                           key="max_strike_price_input",
                                           on_change=lambda: st.session_state.update({"max_strike_price": st.session_state["max_strike_price_input"]}))
        max_premium = st.number_input("Max Premium", 
                                      value=st.session_state["max_premium"], 
                                      format="%.2f",
                                      key="max_premium_input",
                                      on_change=lambda: st.session_state.update({"max_premium": st.session_state["max_premium_input"]}))
        max_aarr = st.number_input("Max AARR %", 
                                   value=st.session_state["max_aarr"], 
                                   format="%.2f",
                                   key="max_aarr_input",
                                   on_change=lambda: st.session_state.update({"max_aarr": st.session_state["max_aarr_input"]}))

    st.divider()
    
    # Call type filter
    st.markdown("**Filter by Call Type**")
    call_type_filter = st.multiselect(
        "Show only these types:", 
        ["🔴 Deep ITM", "🟠 ITM", "🟡 ATM", "🟢 OTM", "🟢 Deep OTM"],
        default=st.session_state["call_type_filter"],
        key="call_type_filter_input",
        on_change=lambda: st.session_state.update({"call_type_filter": st.session_state["call_type_filter_input"]})
    )

# Sort option
sort_by = st.selectbox("Sort by", [
    "AARR (Highest)", 
    "AARR (Lowest)", 
    "Premium (Highest)", 
    "Days to Expiry (Soonest)",
    "Safety Score (Safest First)"
],
    index=["AARR (Highest)", "AARR (Lowest)", "Premium (Highest)", 
           "Days to Expiry (Soonest)", "Safety Score (Safest First)"].index(st.session_state["sort_by"]),
    key="sort_by_input",
    on_change=lambda: st.session_state.update({"sort_by": st.session_state["sort_by_input"]})
)

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
                # Calculate safety score using probability-weighted analysis
                # Calculate raw safety scores
                chain['safety_score_raw'] = chain.apply(
                    lambda row: utils.calculate_safety_score(
                        strike=row['strike'],
                        premium=row['premium'],
                        market_price=market_price,
                        days_to_expiry=row['days_to_expiration'],
                        volatility=volatility
                    ),
                    axis=1
                )
                # Normalize to 0-10 scale
                chain['safety_score'] = chain['safety_score_raw'].apply(
                    lambda x: utils.normalize_safety_score(x, chain['safety_score_raw'].values)
                )

                # Store BOTH raw and normalized
                st.session_state["all_safety_scores_raw"] = chain['safety_score_raw'].values
                st.session_state["all_safety_scores_normalized"] = chain['safety_score'].values  # Add this

            
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
            # if sort_by == "AARR (Highest)":
            #     chain = chain.sort_values("aarr", ascending=False)
            # elif sort_by == "AARR (Lowest)":
            #     chain = chain.sort_values("aarr", ascending=True)
            # Sort
            if sort_by == "AARR (Highest)":
                sort_col = 'expected_aarr' if 'expected_aarr' in chain.columns else 'aarr'
                chain = chain.sort_values(sort_col, ascending=False)
            elif sort_by == "AARR (Lowest)":
                sort_col = 'expected_aarr' if 'expected_aarr' in chain.columns else 'aarr'
                chain = chain.sort_values(sort_col, ascending=True)
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
        # st.metric("Avg AARR", f"{chain['aarr'].mean():.1f}%")
        if 'expected_aarr' in chain.columns:
            st.metric("Avg Expected AARR", f"{chain['expected_aarr'].mean():.1f}%")
        else:
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
                # Use expected AARR if available
                display_aarr = row.get('expected_aarr', row['aarr'])
                aarr_color = "#44ff44" if display_aarr >= 20 else "#ffbb00" if display_aarr >= 10 else "#ffffff"
                
                # Color code safety: green (8-10), yellow (5-7), red (0-4)
                if safety_score >= 8:
                    safety_color = "#44ff44"
                    safety_emoji = "🟢"
                elif safety_score >= 5:
                    safety_color = "#ffbb00"
                    safety_emoji = "🟡"
                else:
                    safety_color = "#ff4444"
                    safety_emoji = "🔴"
                
                st.markdown(f"<span style='color: {aarr_color}; font-weight: bold;'>AARR: {display_aarr:.1f}%</span><br>"
                            f"<span style='color: {safety_color}; font-size: 0.9em;'>{safety_emoji} Safety: {safety_score:.1f}/10</span>", 
                            unsafe_allow_html=True)
            with cols[6]:
                if st.button("View 📊", key=f"btn_{idx}", use_container_width=True):
                    st.session_state["selected_call"] = row.to_dict()
                    st.switch_page(AARR_PAGE)
            
            st.markdown("</div>", unsafe_allow_html=True)