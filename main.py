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
		chain = options.fetch_options_chain(ticker, expiration=expiration)
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


if __name__ == "__main__":
	# test()
	main()