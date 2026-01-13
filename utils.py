from rich.console import Console
from rich.markdown import Markdown
from scipy.stats import norm
import yfinance as yf
import numpy as np
import streamlit as st
from datetime import datetime, timedelta
import pandas as pd

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

@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_market_price(ticker):
    """Fetch the current market price of a stock."""
    try:
        stock = yf.Ticker(ticker)
        return stock.history(period="1d")['Close'].iloc[-1]
    except Exception as e:
        st.error(f"Error fetching market price for {ticker}: {e}")
        return None

@st.cache_data(ttl=300)
def get_historical_volatility(ticker, days=30):
    """Calculate historical volatility (annualized) from recent price data."""
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period=f"{days}d")
        if len(hist) < 2:
            return None
        
        # Calculate daily returns
        returns = hist['Close'].pct_change().dropna()
        
        # Annualize volatility (252 trading days per year)
        volatility = returns.std() * np.sqrt(252)
        return volatility
    except Exception as e:
        print(f"Error calculating volatility: {e}")
        return None
    
def get_implied_volatility_from_options(ticker, days_to_expiry):
    """
    Estimate implied volatility from ATM options.
    More accurate than historical volatility for pricing.
    """
    try:
        stock = yf.Ticker(ticker)
        current_price = stock.history(period="1d")['Close'].iloc[-1]
        
        # Find closest expiration
        expirations = stock.options
        target_date = datetime.today() + timedelta(days=days_to_expiry)
        closest_exp = min(expirations, 
                         key=lambda x: abs((pd.to_datetime(x) - target_date).days))
        
        # Get ATM call options
        chain = stock.option_chain(closest_exp)
        calls = chain.calls
        
        # Find ATM option (strike closest to current price)
        atm_call = calls.iloc[(calls['strike'] - current_price).abs().argsort()[:1]]
        
        # Get implied volatility
        iv = atm_call['impliedVolatility'].values[0]
        
        return iv if iv and iv > 0 else None
    except:
        return None

# def calculate_price_probabilities(current_price, target_prices, days_to_expiry, volatility):
#     """
#     Calculate probability of stock being at each target price at expiration.
#     Uses log-normal distribution assumption.
    
#     Returns array of probabilities (as percentages) for each target price.
#     """
#     if volatility is None or volatility <= 0:
#         # Return uniform distribution if no volatility data
#         return np.ones(len(target_prices)) * (100.0 / len(target_prices))
    
#     # Time in years
#     t = days_to_expiry / 365.0
    
#     # Log-normal parameters
#     mu = np.log(current_price)
#     sigma = volatility * np.sqrt(t)
    
#     # Calculate probability density at each price point
#     probabilities = []
#     for price in target_prices:
#         if price <= 0:
#             probabilities.append(0)
#             continue
        
#         # Log-normal PDF
#         log_price = np.log(price)
#         prob = (1 / (price * sigma * np.sqrt(2 * np.pi))) * \
#                np.exp(-((log_price - mu) ** 2) / (2 * sigma ** 2))
#         probabilities.append(prob)
    
#     # Normalize to percentage (approximate by area under curve)
#     probs_array = np.array(probabilities)
#     if probs_array.sum() > 0:
#         probs_array = (probs_array / probs_array.sum()) * 100
    
#     return probs_array

def calculate_price_probabilities(current_price, target_prices, days_to_expiry, volatility):
    """
    Calculate probability of stock being within a small range around each target price.
    Uses log-normal distribution (Black-Scholes assumption).
    
    Returns array of probabilities (as percentages) for each target price.
    """
    if volatility is None or volatility <= 0:
        # Return uniform distribution if no volatility data
        return np.ones(len(target_prices)) / len(target_prices) * 100
    
    # Time in years
    t = days_to_expiry / 365.0
    
    # Expected log return (drift term, assuming risk-free rate ≈ 0 for simplicity)
    mu = -0.5 * volatility**2 * t  # Drift-adjusted mean for log-normal
    sigma = volatility * np.sqrt(t)
    
    # Calculate probability for small price ranges around each point
    probabilities = []
    price_step = target_prices[1] - target_prices[0] if len(target_prices) > 1 else 1
    
    for price in target_prices:
        if price <= 0:
            probabilities.append(0)
            continue
        
        # Convert to log returns
        log_return = np.log(price / current_price)
        
        # Calculate probability density using normal distribution
        # (log returns are normally distributed)
        prob_density = norm.pdf(log_return, loc=mu, scale=sigma)
        
        # Convert density to probability over the price interval
        # Multiply by price_step to get probability mass
        probability = prob_density * price_step / price
        
        probabilities.append(probability)
    
    # Normalize to sum to 100%
    probs_array = np.array(probabilities)
    if probs_array.sum() > 0:
        probs_array = (probs_array / probs_array.sum()) * 100
    
    return probs_array

def compute_aarr(num_shares, initial_market_price, strike_price, premium, expiry, strike_out=None, final_market_price=None):
    """Calculate annualized rate of return for a covered call position."""
    if num_shares % 100 != 0:
        raise ValueError("Number of shares must be a multiple of 100 for AARR calculation.")

    start_money = initial_market_price * num_shares

    # Set strike-out condition based on final_market_price
    if final_market_price is not None:
        strike_out = final_market_price >= strike_price
    else:
        strike_out = True  # Default to True if final_market_price is not provided

    if strike_out:
        # Shares are called away at strike price
        end_money = (strike_price + premium) * num_shares
    else:
        if final_market_price is None:
            final_market_price = initial_market_price
        end_money = (final_market_price + premium) * num_shares

    net_gain = end_money - start_money

    # Annualized return using compound formula
    # Add 3 days for settlement (calls expire Friday, cash on Monday)
    total_days = expiry + 3
    aarr_compound = ((end_money / start_money) ** (365 / total_days) - 1) * 100
    
    return aarr_compound, net_gain, start_money, end_money

def compute_hold_aarr(num_shares, initial_market_price, final_market_price, days):
    """Calculate AARR for simply holding the stock."""
    start_money = initial_market_price * num_shares
    end_money = final_market_price * num_shares
    net_gain = end_money - start_money
    
    aarr = ((end_money / start_money) ** (365 / days) - 1) * 100
    return aarr, net_gain