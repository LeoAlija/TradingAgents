### `decision_engine/risk.py`

def calc_position_size(entry, stop, account_size, risk):
    if stop is None or entry == stop:
        return 0.0
    risk_amt = float(account_size) * float(risk)
    per_unit = abs(entry - stop)
    if per_unit == 0:
        return 0.0
    contracts = risk_amt / per_unit