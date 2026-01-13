import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import utils
import streamlit as st

@st.cache_data(ttl=300)  # Cache for 5 minutes
def fetch_options_chain(ticker: str, first_expiration, last_expiration=None, expiration_range=30):
	"""
	Fetch call options for a stock across all expiration dates within the given range [first,last].

	Arguments:
	- ticker: str, stock ticker
	- first_expiration: str | int | None, earliest expiration date (e.g. '2024-06-15' or 30 for 30 days from today)
	- last_expiration: str | int | None, latest expiration date (e.g. '2024-09-01' or 90 for 90 days from today)

	Returns:
	- DataFrame of call options within the expiration range
	"""
	stock = yf.Ticker(ticker)
	available_dates = stock.options
	if not available_dates:
		raise ValueError("No options available for this ticker.")

	# Convert to datetime for filtering
	available_dates_dt = [pd.to_datetime(d).date() for d in available_dates]

	# Set last_expiration to first_expiration if not provided
	if last_expiration is None:
		last_expiration = first_expiration + timedelta(days=expiration_range)

	# Convert int-based expirations to actual dates
	today = datetime.today().date()
	if isinstance(first_expiration, int):
		first_expiration = today + timedelta(days=first_expiration)
	if isinstance(last_expiration, int):
		last_expiration = today + timedelta(days=last_expiration)

	# Default to full available range if None
	first_expiration = pd.to_datetime(first_expiration).date() if first_expiration else available_dates_dt[0]
	last_expiration = pd.to_datetime(last_expiration).date() if last_expiration else available_dates_dt[-1]

	# Filter expiration dates in range
	expirations_in_range = [
		str(date) for date in available_dates_dt
		if first_expiration <= date <= last_expiration
	]

	if len(expirations_in_range) == 0 or not expirations_in_range:
		raise ValueError("No expirations found in the specified range.")

	all_calls = []
	for exp in expirations_in_range:
		try:
			opt_chain = stock.option_chain(exp)
			calls = opt_chain.calls
			calls["expiration"] = pd.to_datetime(exp)
			calls["days_to_expiration"] = (calls["expiration"] - pd.Timestamp.now()).dt.days
			all_calls.append(calls)
		except Exception as e:
			print(f"Skipping {exp} due to error: {e}")

	if not all_calls:
		raise ValueError("Failed to retrieve any call data.")

	result = pd.concat(all_calls, ignore_index=True)
	
	# Get current market price once
	market_price = utils.get_market_price(ticker)
	
	# Add AARR column
	result["aarr"] = result.apply(
		lambda row: utils.compute_aarr(
			num_shares=100,
			initial_market_price=market_price,
			strike_price=row["strike"],
			premium=row["lastPrice"],
			expiry=row["days_to_expiration"],
			final_market_price=None,
			strike_out=True
		)[0], axis=1
	)

	# Add Expected AARR (probability-weighted)
	result["expected_aarr"] = result.apply(
		lambda row: utils.calculate_expected_aarr_for_call(
			strike=row["strike"],
			premium=row["lastPrice"],
			days_to_expiry=row["days_to_expiration"],
			market_price=market_price,
			# volatility=utils.get_implied_volatility_from_options(ticker, days_to_expiry=row["days_to_expiration"])
			volatility=utils.get_historical_volatility(ticker, days=row["days_to_expiration"])
		), axis=1
	)

	return result[["strike", "lastPrice", "expiration", "days_to_expiration", "aarr", "expected_aarr"]].rename(columns={
		"lastPrice": "premium"
	})


def filter_conservative_calls(df, min_premium=0.5, max_days=6 * 30):
	"""Filter calls based on conservative rules."""
	return df[
		(df["premium"] >= min_premium) &
		(df["days_to_expiration"] <= max_days)
	].sort_values(by="premium", ascending=False).reset_index(drop=True)


def filter_calls(df, strike_price, expiration_date=None):
	"""Filter calls based on strike price and expiration date."""
	if strike_price is not None:
		df = df[df["strike"] >= strike_price]
	if expiration_date is not None:
		df = df[df["expiration"] == pd.to_datetime(expiration_date)]
	return df

@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_stock_fundamentals(ticker: str, text_format=True):
	"""Get fundamental data for a stock."""
	stock = yf.Ticker(ticker)
	info = stock.info
	fundamentals = {
		"ticker": ticker.upper(),
		"price": info.get("currentPrice"),
		"market_cap": info.get("marketCap"),
		"pe_ratio": info.get("trailingPE"),
		"dividend_yield": info.get("dividendYield", 0) / 100 if info.get("dividendYield") else 0,
		"beta": info.get("beta"),
		"52_week_high": info.get("fiftyTwoWeekHigh"),
		"52_week_low": info.get("fiftyTwoWeekLow"),
		"short_percent": info.get("shortPercentOfFloat"),
		"earnings_date": info.get("earningsDate"),
	}
	if text_format:
		return get_fundamentals_text(fundamentals, ticker)
	else:
		return fundamentals

def get_fundamentals_text(fundamentals: dict, ticker: str):
	"""Format fundamentals as readable text."""
	return f"""
Stock Fundamentals for {ticker.upper()}:
- Current Price: ${fundamentals['price']:,}
- Market Cap: ${fundamentals['market_cap']:,}
- P/E Ratio: {fundamentals['pe_ratio']}
- Dividend Yield: {fundamentals['dividend_yield'] * 100:.2f}% (annual)
- Beta: {fundamentals['beta']}
- 52-Week Range: ${fundamentals['52_week_low']} - ${fundamentals['52_week_high']}
- Short % of Float: {fundamentals['short_percent'] * 100:.2f}%
- Earnings Date: {fundamentals['earnings_date']}
"""