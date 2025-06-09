from llm import *
import options
import utils
from prompt import *


def main():
	expert = LLM()
	ticker = "NVDA"  # You can prompt user later or pass as arg
	strategy = "In between conservative and aggressive"
	expiration = 30 * 3 # 3 months

	try:
		chain = options.fetch_options_chain(ticker, first_expiration=expiration)
	except Exception as e:
		print(f"Error fetching options: {e}")
		return

	filtered = options.filter_conservative_calls(chain)

	if filtered.empty:
		print("No conservative covered calls found.")
		return
	
	stock_fundamentals = options.get_stock_fundamentals(ticker, text_format=True)
	
	prompt = suggestion_prompt.format(ticker=ticker, 
								   options_chain=filtered.to_string(index=False), 
								   stock_fundamentals=stock_fundamentals,
								   stragety=strategy)
	response = expert.ask(prompt)
	utils.pretty_print("Stock Analysis", response)

def test():
	expert = LLM()
	# 1: Load & filter options
	chain = options.get_mock_options_chain()
	filtered = options.filter_conservative_calls(chain)
	prompt = suggestion_prompt.format(options_chain=filtered.to_string(index=False))
	# 2: Get LLM output
	response = expert.ask(prompt)
	print("\n=== LLM Suggestion ===")
	print(response)

def test2():
	ticker = "AAPL"
	first_exp = 30 
	last_exp = 90
	num_shares = 100
	market_price = utils.get_market_price(ticker)
	strike_price = 150  
	chain = options.fetch_options_chain(ticker, first_expiration=first_exp, last_expiration=last_exp)
	filtered = options.filter_calls(chain, strike_price=strike_price)
	covered_call = filtered.iloc[0]  # Just take the first one for testing
	premium = covered_call['premium']
	aarr, gain, start, end = utils.compute_aarr(num_shares=num_shares,
												 initial_market_price=market_price,
												 strike_price=covered_call['strike'],
												 premium=premium,
												 expiry=covered_call['days_to_expiration'],
												 final_market_price=None,  # Assume shares are called away
												 strike_out=True)
	# Print all the results
	print(f"Ticker: {ticker}")
	print(f"Covered Call: ${covered_call['strike']} strike, ${covered_call['premium']} premium")
	print(f"Shares: {num_shares}")
	print(f"Expiry: {covered_call['days_to_expiration']} days")
	print(f"Start Money: ${start:.2f}")
	print(f"End Money: ${end:.2f}")
	print(f"Gain: ${gain:.2f}")
	# Print the annualized return
	print(f"AARR: {aarr:.2f}%")
	


if __name__ == "__main__":
	# test()
	# main()
	test2()