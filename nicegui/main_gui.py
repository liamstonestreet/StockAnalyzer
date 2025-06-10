# nicegui_app/main_gui.py

import pandas as pd
import yfinance as yf
from nicegui import ui
import os, sys


# Add parent directory to path for utils/options access
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import utils
import options
import aarr_graph

# App state (TODO Define defaults!)
app_state = {
    'chain': pd.DataFrame(),
    'ticker': 'AAPL',
    'price': 0.0,
}

def fetch_calls():
    ticker = ticker_input.value.strip().upper()

    try:
        chain = options.fetch_options_chain(ticker, first_exp.value, last_exp.value)

        if min_strike.value > 0:
            chain = chain[chain["strike"] >= min_strike.value]
        if max_strike.value > 0:
            chain = chain[chain["strike"] <= max_strike.value]
        if min_premium.value > 0:
            chain = chain[chain["premium"] >= min_premium.value]
        if max_premium.value > 0:
            chain = chain[chain["premium"] <= max_premium.value]
        if min_aarr.value > 0:
            chain = chain[chain["aarr"] >= min_aarr.value]
        if max_aarr.value > 0:
            chain = chain[chain["aarr"] <= max_aarr.value]

        chain.reset_index(drop=True, inplace=True)
        app_state['chain'] = chain
        app_state['ticker'] = ticker
        display_calls()

    except Exception as e:
        results_container.clear()
        ui.notify(f"Error fetching data: {e}", color='negative')

def display_calls():
    results_container.clear()
    chain = app_state['chain']
    if chain.empty:
        ui.notify('No results found.')
        return

    ui.label(f'Showing {len(chain)} results').classes('text-xl font-semibold')

    for idx, row in chain.iterrows():
        with results_container:
            with ui.row().classes('items-center border rounded-lg p-3 bg-gray-100'):
                ui.label(f'Strike: ${row["strike"]:.2f}').classes('w-1/5')
                ui.label(f'Premium: ${row["premium"]:.2f}').classes('w-1/5')
                ui.label(f'Expires: {row["expiration"].date()}').classes('w-1/5')
                ui.label(f'AARR (Market @ Exp: ${row["strike"]:.2f}): {row["aarr"]:.2f}%').classes('w-2/5')
                ui.button('View', on_click=lambda r=row: aarr_graph.show_graph(r, app_state['ticker'], app_state['price'])).props('color=primary')

############# UI STUFF #############

ui.label('📈 Covered Call Viewer').classes('text-2xl font-bold')

# --- Input row ---
with ui.row().classes('items-center'):
    ticker_input = ui.input('Stock Ticker', value=app_state['ticker']).props('outlined dense').style('width: 120px')
    price_label = ui.label('Fetching price...').classes('text-lg')
    price = utils.get_market_price(app_state['ticker'])
    app_state['price'] = price
    price_label.text = f'Current Price: ${price:.2f}'

# --- Filter inputs ---
with ui.row():
    with ui.column():
        first_exp = ui.number('First Expiration (days)', value=30)
        last_exp = ui.number('Last Expiration (days)', value=90)
        min_strike = ui.number('Min Strike Price', value=110)
        min_premium = ui.number('Min Premium', value=0.0)
        min_aarr = ui.number('Min AARR (%)', value=0.0)
    with ui.column():
        max_strike = ui.number('Max Strike Price', value=250.0)
        max_premium = ui.number('Max Premium', value=0.0)
        max_aarr = ui.number('Max AARR (%)', value=0.0)

results_container = ui.column().classes('w-full')
# --- Fetch button ---
ui.button('Fetch Covered Calls', on_click=fetch_calls).props('color=primary').classes('mt-4')

ui.run()