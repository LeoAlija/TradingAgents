import os
import requests
from dotenv import load_dotenv
import pandas as pd
from datetime import datetime, timedelta

load_dotenv()

FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY") 

FINNHUB_BASE = "https://finnhub.io/api/v1"

def get_historical_prices(symbol, lookback=60, interval='D'):
    """
    Fetch last `lookback` candles for symbol from Finnhub. Returns close prices list.
    interval: 'D' for day, '60' for 1 hour, '5' for 5min, etc.
    """
    now = datetime.utcnow()
    if interval == 'D':
        fr = now - timedelta(days=lookback*2)
    else:
        fr = now - timedelta(days=min(lookback*2, 30)) # Finnhub rate limits intraday

    from_unix = int(fr.timestamp())
    to_unix = int(now.timestamp())
    symbol_fx = symbol.upper()
    if symbol_fx == "BTCUSD":
        symbol_fx = "BINANCE:BTCUSDT"
    url = f"{FINNHUB_BASE}/crypto/candle?symbol={symbol_fx}&resolution={interval}&from={from_unix}&to={to_unix}&token={FINNHUB_API_KEY}"
    resp = requests.get(url)
    data = resp.json()
    if data.get("s") != "ok":
        raise Exception(f"Finnhub data error: {data.get('s', '')}")
    closes = data['c'][-lookback:]
    return closes

def get_latest_price(symbol):
    return float(get_historical_prices(symbol, lookback=1)[-1])
