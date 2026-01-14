"""
Run this file to debug stuff!
"""

import options
import utils
import numpy as np

# Debug options chain
# ticker = "AEM"
# chain = options.fetch_options_chain(ticker, first_expiration=30, expiration_range=45)
# filtered = options.filter_conservative_calls(chain)
# fundamentals = options.get_stock_fundamentals(ticker)

# print("Length:", len(chain))

# print("Current AEM Market Price:", utils.get_market_price(ticker))

# print(filtered)
# print()
# print(fundamentals)

arr = np.linspace(1, 10, 30)
print(arr)

