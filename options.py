# options.py
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta


def fetch_options_chain(ticker: str, expiration: str = None):
	"""Fetches call options for a stock and expiration date from Yahoo."""
	"""Finds the call options that expire at given expiration date or soonest afterwards."""
	stock = yf.Ticker(ticker)
	available_dates = stock.options
	if not available_dates:
		raise ValueError("No options available for this ticker.")

	# Handle expiration as int (days from today)
	if isinstance(expiration, int):
		target_date = (datetime.today() + timedelta(days=expiration)).date()
		# Choose the next available expiration on or after that date
		expiration = next((d for d in available_dates if pd.to_datetime(d).date() >= target_date), available_dates[-1])

	# Use soonest expiration if none provided
	expiration = expiration or available_dates[0]

	opt_chain = stock.option_chain(expiration)
	calls = opt_chain.calls

	# Add rough delta estimate (mock for now)
	calls["delta"] = calls["inTheMoney"].apply(lambda itm: 0.6 if itm else 0.2)
	calls["expiration"] = pd.to_datetime(expiration)
	calls["days_to_expiration"] = (calls["expiration"] - pd.Timestamp.now()).dt.days

	return calls[["strike", "lastPrice", "delta", "expiration", "days_to_expiration"]].rename(columns={
		"lastPrice": "premium"
	})

def filter_conservative_calls(df, min_premium=0.5, max_delta=1, max_days=6 * 30):
	"""Filter calls based on Dad's rules! (Conservative, for the most part)"""
	"""For now, we ignore filtering on delta by using max_delta=1. We can add it once we scrape the delta data."""
	return df[
		(df["premium"] >= min_premium) &
		(df["delta"] <= max_delta) &
		(df["days_to_expiration"] <= max_days)
	].sort_values(by="delta").drop(["delta"], axis=1)

# options.py

def get_stock_fundamentals(ticker: str, text_format=True):
	stock = yf.Ticker(ticker)
	info = stock.info
	fundamentals = {
		"ticker": ticker.upper(),
		"price": info.get("currentPrice"),
		"market_cap": info.get("marketCap"),
		"pe_ratio": info.get("trailingPE"),
		"dividend_yield": info.get("dividendYield") / 100,
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

def get_fundamentals_text(fundamentals: dict,ticker: str):
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

