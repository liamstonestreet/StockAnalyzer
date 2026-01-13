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

def calculate_safety_score(strike, premium, market_price, days_to_expiry, volatility):
    """
    Calculate safety score for a covered call based on probability-weighted outcomes.
    Higher score = safer position.
    
    Logic:
    - Deep ITM: Penalized because you're guaranteed to sell at below-market price
    - ATM: Rewarded because outcome is in high-probability region
    - OTM: Scored based on risk/reward tradeoff of premium vs potential missed gains
    """
    
    # Generate price distribution
    if volatility is None or volatility <= 0:
        # Without volatility, use simple distance metric
        distance_penalty = 1 / (1 + abs(strike - market_price) / market_price)
        premium_yield = (premium / market_price) * 100
        return premium_yield * distance_penalty
    
    # Create price range around strike
    price_range = np.linspace(market_price * 0.5, market_price * 2, 200)
    probabilities = calculate_price_probabilities(market_price, price_range, days_to_expiry, volatility)
    
    # Find probability mass in different regions
    prob_below_strike = sum(probabilities[price_range < strike])
    prob_at_strike = sum(probabilities[(price_range >= strike * 0.98) & (price_range <= strike * 1.02)])
    prob_above_strike = sum(probabilities[price_range > strike])
    
    premium_yield = (premium / market_price) * 100
    
    # Case 1: Deep ITM (strike < 95% of current)
    if strike < market_price * 0.95:
        # Penalty: You're selling at a loss
        locked_loss_pct = (market_price - strike) / market_price * 100
        # Even with premium, if you're giving up >5% in stock value, that's bad
        net_position = premium_yield - locked_loss_pct
        safety = max(0, net_position) * 0.5  # Heavy penalty for deep ITM
        
    # Case 2: ITM (95% <= strike < 100%)
    elif strike < market_price:
        # Moderate penalty but not as bad
        locked_loss_pct = (market_price - strike) / market_price * 100
        net_position = premium_yield - locked_loss_pct
        safety = max(0, net_position) * 0.8
        
    # Case 3: ATM (100% <= strike <= 105%)
    elif strike <= market_price * 1.05:
        # Reward: You're in the high-probability region
        # Safety = premium yield × probability of being near strike
        safety = premium_yield * (prob_at_strike / 10) * 2.0  # Bonus for ATM
        
    # Case 4: OTM (105% < strike <= 115%)
    elif strike <= market_price * 1.15:
        # Calculate risk/reward
        # If it executes: you get premium + gain to strike
        # If it doesn't: you just get premium
        potential_gain_pct = (strike - market_price) / market_price * 100
        total_return = premium_yield + potential_gain_pct
        
        # Weight by probability of execution
        expected_return = (prob_above_strike / 100) * total_return + (prob_below_strike / 100) * premium_yield
        safety = expected_return * 1.2  # Slight bonus for OTM
        
    # Case 5: Deep OTM (strike > 115%)
    else:
        # Low probability of execution = just collecting small premium
        # Safety is just premium yield, heavily discounted
        safety = premium_yield * (prob_above_strike / 100) * 0.5
    
    return max(0, safety)  # Ensure non-negative

def normalize_safety_score(raw_score, all_scores):
    """
    Normalize safety scores to 0-10 scale.
    Uses percentile-based normalization so scores are relative to the dataset.
    
    10 = top 10% safest
    5 = median
    0 = bottom 10% (dangerous)
    """
    if len(all_scores) == 0:
        return 5.0
    
    # Use percentile ranking
    percentile = (all_scores < raw_score).sum() / len(all_scores) * 100
    
    # Map percentile to 0-10 scale
    if percentile >= 90:
        score = 9 + (percentile - 90) / 10  # 9-10 range
    elif percentile >= 75:
        score = 7.5 + (percentile - 75) / 15 * 1.5  # 7.5-9 range
    elif percentile >= 50:
        score = 5 + (percentile - 50) / 25 * 2.5  # 5-7.5 range
    elif percentile >= 25:
        score = 2.5 + (percentile - 25) / 25 * 2.5  # 2.5-5 range
    elif percentile >= 10:
        score = 1 + (percentile - 10) / 15 * 1.5  # 1-2.5 range
    else:
        score = percentile / 10  # 0-1 range
    
    return round(score, 1)

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