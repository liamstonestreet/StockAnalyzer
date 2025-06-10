from llm import *
from options import *
from utils import *
from prompt import *


def main():
	expert = LLM()
	ticker = "NVDA"  # You can prompt user later or pass as arg
	strategy = "In between conservative and aggressive"
	expiration = 30 * 3 # 3 months

	try:
		chain = fetch_options_chain(ticker, first_expiration=expiration)
	except Exception as e:
		print(f"Error fetching options: {e}")
		return

	filtered = filter_conservative_calls(chain)

	if filtered.empty:
		print("No conservative covered calls found.")
		return
	
	stock_fundamentals = get_stock_fundamentals(ticker, text_format=True)
	
	prompt = suggestion_prompt.format(ticker=ticker, 
								   options_chain=filtered.to_string(index=False), 
								   stock_fundamentals=stock_fundamentals,
								   stragety=strategy)
	response = expert.ask(prompt)
	utils.pretty_print("Stock Analysis", response)

def test():
	expert = LLM()
	# 1: Load & filter options
	ticker = "AAPL"  # Example ticker
	chain = fetch_options_chain(ticker, first_expiration=30, last_expiration=90)
	filtered = filter_conservative_calls(chain)
	prompt = suggestion_prompt.format(options_chain=filtered.to_string(index=False))
	# 2: Get LLM output
	response = expert.ask(prompt)
	print("\n=== LLM Suggestion ===")
	print(response)

def compute_returns():
	ticker = "AEM"
	first_exp = 24 
	last_exp = 24
	# num_shares = 100
	num_contracts = 1
	# initial_market_price = utils.get_market_price(ticker)
	initial_market_price = 117.78
	strike_price = 116 
	final_market_price = None  # Assume shares are called away at this price
	chain = fetch_options_chain(ticker, first_expiration=first_exp, last_expiration=last_exp)
	filtered = filter_calls(chain, strike_price=strike_price)
	covered_call = filtered.iloc[0]  # Just take the first one for testing
	# strike_price = covered_call['strike']
	# premium = covered_call['premium']
	premium = 5.44
	aarr, gain, start, end = utils.compute_aarr(num_shares=num_contracts * 100,
												 initial_market_price=initial_market_price,
												 strike_price=strike_price,
												 premium=premium,
												 expiry=covered_call['days_to_expiration'],
												 final_market_price=None,  # Assume shares are called away
												 strike_out=True)
	# Print all the results
	print(f"Ticker: {ticker}")
	print(f"Covered Call: ${covered_call['strike']} strike, ${covered_call['premium']} premium")
	print(f"Shares: {num_contracts * 100} ({num_contracts} contract = {num_contracts * 100} shares)")
	print(f"Expiry: {covered_call['days_to_expiration']} days")
	print(f"Strike Out: {'Yes' if final_market_price is None else 'No'}")
	print(f"Start Money: ${start:.2f}")
	print(f"End Money: ${end:.2f}")
	print(f"Gain: ${gain:.2f}")
	print(f"AARR: {aarr:.2f}%")
	


if __name__ == "__main__":
	# test()
	# main()
	compute_returns()