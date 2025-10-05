# cli/hedge.py

import sys, os
import click

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from decision_engine.decision_engine import recommend
from decision_engine.finnhub_feed import get_historical_prices, get_latest_price
from decision_engine.agent_signals import aggregate_news_signal

@click.command()
@click.option('--asset', required=True, help='Asset symbol (e.g. BTCUSD)')
@click.option('--account_size', required=True, type=float, help='Account size in USD')
@click.option('--risk', default=0.02, show_default=True, type=float, help='Max % risk per trade')
@click.option('--export_md', default=None, help='If set, export recommendations to this Markdown file')
def hedge(asset, account_size, risk, export_md):
    """Actionable trade recommendation engine with live data & agent scoring."""
    print(f"Fetching live {asset} candles from Finnhub...")
    try:
        prices = get_historical_prices(asset, lookback=60, interval='D')
    except Exception as e:
        print(f"Error fetching prices: {e}"); return
    print("Scoring current agent signals (news-sentiment + OpenAI)...")
    agent_signals = aggregate_news_signal()

    cfg = {"account_size": account_size, "risk": risk}
    reco = recommend(agent_signals, prices, cfg)
    display_recommendation(reco)
    if export_md:
        export_markdown(reco, export_md)
        print(f"✓ Exported markdown to {export_md}")

def display_recommendation(reco):
    if reco["action"] == "WAIT":
        print(f"\n[Market Regime: {reco['regime']}] Agents consensus: {reco['consensus']} → No Trade Signal (WAIT)\n")
    elif reco["action"] == "STRADDLE":
        print(f"\n[Regime: {reco['regime']}] Market is highly volatile. Consider straddling.\n")
    else:
        print(f"\nREGIME: {reco['regime']}, Consensus: {reco['consensus']}")
        print(f"ACTION: {reco['action']} {reco['size']} units")
        print(f"Entry: ${reco['entry']:.2f} ● Stop: ${reco['stop']:.2f}")
        if reco['tp1']: print(f"Take Profit 1: ${reco['tp1']:.2f}")
        if reco['tp2']: print(f"Take Profit 2: ${reco['tp2']:.2f}")
        print()

def export_markdown(reco, filename):
    with open(filename, "w") as f:
        f.write("# Trade Recommendation\n\n")
        f.write(f"**Market Regime:** {reco['regime']}\n\n")
        f.write(f"**Action:** {reco['action']}\n")
        if reco["action"] in ("LONG", "SHORT"):
            f.write(f"- Entry: `${reco['entry']:.2f}`\n")
            f.write(f"- Stop: `${reco['stop']:.2f}`\n")
            if reco['tp1']: f.write(f"- Take Profit 1: `${reco['tp1']:.2f}`\n")
            if reco['tp2']: f.write(f"- Take Profit 2: `${reco['tp2']:.2f}`\n")
            f.write(f"- Position Size: `{reco['size']}` units\n\n")
        f.write(f"**Agent Consensus:** {reco['consensus']}\n")

if __name__ == "__main__":
    hedge()