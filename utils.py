
from rich.console import Console
from rich.markdown import Markdown
from scipy.stats import norm
import yfinance as yf
import numpy as np

def get_api_key():
    with open("keys.txt", "r") as f:
        return f.read()

def black_scholes_delta(S, K, T, r, sigma, call=True):
    """Estimate delta for an option."""
    d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    if call:
        return norm.cdf(d1)
    else:
        return norm.cdf(d1) - 1
    
def pretty_print(header, text):
    console = Console()
    console.print(f"[bold cyan]📈 {header}[/bold cyan]")
    console.print(Markdown(text))

def get_market_price(ticker):
    """Fetch the current market price of a stock."""
    stock = yf.Ticker(ticker)
    return stock.history(period="1d")['Close'].iloc[-1]

def compute_aarr(num_shares, initial_market_price, strike_price, premium, expiry, strike_out=None, final_market_price=None):
    if num_shares % 100 != 0:
        raise ValueError("Number of shares must be a multiple of 100 for AARR calculation.")

    start_money = initial_market_price * num_shares

    # Set strike-out condition based on final_market_price
    if final_market_price is not None:
        strike_out = final_market_price >= strike_price
    else:
        strike_out = True  # Default to True if final_market_price is not provided

    if strike_out:
        # Shares are called away at strike price; you receive strike + premium
        end_money = (strike_price + premium) * num_shares
    else:
        if final_market_price is None:
            print("Warning: final_market_price is None! Assuming it equals initial_market_price.")
            final_market_price = initial_market_price
        end_money = (final_market_price + premium) * num_shares

    net_gain = end_money - start_money

    # i need 12 / # months taken by: (date the shares were bought (we assume this is the same day as sell date) to date you get your money from the covered call striking out)
    # all (99%) of covered calls expire friday. people get the strike-out money on the next monday, so we add 3 to expiry date.
    months_to_cash = (expiry + 3) / 30  # Convert days to months. +3 accounts for weekend delay in cashing out.
    aarr_simple = (net_gain / start_money * 100) * (12 / (months_to_cash))  # Simple return in %
    aarr_compound = ((end_money / start_money) ** (365 / (expiry + 3)) - 1) * 100
    return aarr_simple, net_gain, start_money, end_money


    