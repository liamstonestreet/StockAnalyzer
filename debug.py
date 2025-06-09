"""
Run this file to debug stuff!
"""

import options

# Debug options chain
ticker = "AAPL"
chain = options.fetch_options_chain(ticker, first_expiration=30, last_expiration=90)
filtered = options.filter_conservative_calls(chain)
fundamentals = options.get_stock_fundamentals(ticker)

print("Length:", len(chain))

# print(filtered)
# print()
# print(fundamentals)