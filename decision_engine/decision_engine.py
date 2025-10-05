from .regime import detect_regime
from .risk import calc_position_size

def recommend(agent_signals, prices, config):
    """
    Generate a trade recommendation based on agent signals, price history, and config.
    """
    regime = detect_regime(prices)
    consensus = sum(agent_signals) / len(agent_signals) if agent_signals else 0
    entry = float(prices[-1])

    if regime == "Strong Bull" and consensus > 0.5:
        action = "LONG"
        stop = entry * 0.95
        tps = [entry * 1.05, entry * 1.10]
    elif regime == "Strong Bear" and consensus < -0.5:
        action = "SHORT"
        stop = entry * 1.05
        tps = [entry * 0.95, entry * 0.90]
    elif regime == "High Volatility":
        action = "STRADDLE"
        stop = None
        tps = []
    else:
        action = "WAIT"
        stop = None
        tps = []

    size = calc_position_size(entry, stop, config["account_size"], config["risk"]) if action in ("LONG", "SHORT") else 0.0

    return {
        "action": action,
        "entry": entry,
        "stop": stop,
        "tp1": tps[0] if tps else None,
        "tp2": tps[1] if len(tps) > 1 else None,
        "size": size,
        "regime": regime,
        "consensus": round(consensus, 3),
    }