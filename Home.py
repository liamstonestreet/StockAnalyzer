
# app.py
import streamlit as st
import pandas as pd
import yfinance as yf
import options
import utils

HOME_PAGE = "Home.py"
AARR_PAGE = "pages/Final Market Price vs AARR.py"

st.set_page_config(page_title="Covered Call Viewer", layout="wide")

st.title("\U0001F4C8 Covered Call Viewer")

# User inputs
ticker = st.text_input("Stock Ticker", value="AAPL")
col1, col2 = st.columns(2)
with col1:
    first_exp = st.number_input("First Expiration (days from now)", min_value=0, value=30)
with col2:
    last_exp = st.number_input("Last Expiration (days from now)", min_value=first_exp, value=90)
# Additional filters
col3, col4 = st.columns(2)
with col3:
    min_strike_price = st.number_input("Minimum Strike Price (optional)", value=0.0, format="%.2f")
    min_premium = st.number_input("Minimum Premium (optional)", value=0.0, format="%.2f")
    min_aarr = st.number_input("Minimum AARR % (optional)", value=0.0, format="%.2f")
with col4:
    max_strike_price = st.number_input("Maximum Strike Price (optional)", value=0.0, format="%.2f")
    max_premium = st.number_input("Maximum Premium (optional)", value=0.0, format="%.2f")
    max_aarr = st.number_input("Maximum AARR % (optional)", value=0.0, format="%.2f")

# Fetch options chain
if st.button("Fetch Covered Calls"):
    try:
        chain = options.fetch_options_chain(ticker, first_expiration=first_exp, last_expiration=last_exp)
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


        chain.reset_index(drop=True, inplace=True)
        st.session_state["options_chain"] = chain
        st.session_state["ticker"] = ticker
        st.session_state["stock_price"] = yf.Ticker(ticker).info["currentPrice"]

    except Exception as e:
        st.error(f"Error fetching options: {e}")

# Render saved data
if "options_chain" in st.session_state:
    chain = st.session_state["options_chain"]
    ticker = st.session_state["ticker"]
    st.subheader(f"Showing {len(chain)} results")

    for idx, row in chain.iterrows():
        strike = row["strike"]
        premium = row["premium"]
        exp = row["expiration"].date()
        aarr = row["aarr"]

        with st.container():
            # st.markdown("""
            #     <div style="
            #         border: 1px solid rgba(255, 255, 255, 0.15);
            #         border-radius: 12px;
            #         padding: 16px 24px;
            #         margin-bottom: 12px;
            #         background-color: rgba(255, 255, 255, 0.03);
            #     ">
            # """, unsafe_allow_html=True)

            cols = st.columns([4, 3, 3, 6, 2])
            with cols[0]:
                st.markdown(f"**Strike:** ${strike:.2f}")
            with cols[1]:
                st.markdown(f"**Premium:** ${premium:.2f}")
            with cols[2]:
                st.markdown(f"**Expires:** {exp}")
            with cols[3]:
                st.markdown(f"**AARR (Market @ Expiry = ${strike:.2f}):** {aarr:.2f}%")
            with cols[4]:
                if st.button("View", key=f"btn_{idx}"):
                    st.session_state["selected_call"] = row.to_dict()
                    st.switch_page(f"{AARR_PAGE}")

            st.markdown("</div>", unsafe_allow_html=True)
