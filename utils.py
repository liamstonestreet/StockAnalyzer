
from rich.console import Console
from rich.markdown import Markdown
from scipy.stats import norm
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

    