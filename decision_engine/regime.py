# decision_engine/regime.py

import pandas as pd

def detect_regime(prices):
    ser = pd.Series(prices)
    if len(ser) < 50:
        return "Unknown"
    long_ma = ser.rolling(50).mean().iloc[-1]
    short_ma = ser.rolling(10).mean().iloc[-1]
    std_20 = ser.rolling(20).std().iloc[-1]
    rel_vol = std_20 / ser.iloc[-1]

    if short_ma > long_ma * 1.01 and rel_vol < 0.025:
        return "Strong Bull"
    elif short_ma < long_ma * 0.99 and rel_vol < 0.025:
        return "Strong Bear"
    elif rel_vol > 0.04:
        return "High Volatility"
    else:
        return "Sideways"
