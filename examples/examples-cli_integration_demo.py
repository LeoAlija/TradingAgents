"""
CLI Integration Demo for TradingAgents Hedge Engine
Shows how to add hedge command to existing TradingAgents CLI
"""

import sys
import os
import json
import argparse

# Add the parent directory to the path so we can import hedge_engine
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.progress import track
    console = Console()
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    console = None

def create_mock_console():
    """Create a mock console for when rich is not available"""
    class MockConsole:
        def print(self, *args, **kwargs):
            # Remove style formatting for plain print
            text = str(args[0]) if args else ""
            # Remove rich formatting tags
            import re
            clean_text = re.sub(r'\[.*?\]', '', text)
            print(clean_text)
    return MockConsole()

if not RICH_AVAILABLE:
    console = create_mock_console()

def load_hedge_config():
    """Load hedge configuration from file or return default"""
    config_path = os.path.join(os.path.dirname(__file__), '..', 'configs', 'hedge_config.json')
    
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        console.print("⚠️  Config file not found, using default configuration...")
        return get_default_config()

def get_default_config():
    """Return default hedge configuration"""
    return {
        "market_regimes": {
            "strong_bull": {
                "criteria": {"trend_strength": "> 0.7", "volatility": "< 0.3"},
                "strategies": ["directional_long"]
            },
            "weak_bull": {
                "criteria": {"trend_strength": "0.3 to 0.7", "volatility": "< 0.5"},
                "strategies": ["long_short_hedge"]
            },
            "sideways": {
                "criteria": {"trend_strength": "< 0.3", "volatility": "< 0.4"},
                "strategies": ["range_trading", "wait"]
            }
        },
        "risk_management": {
            "max_risk_per_trade": 0.02,
            "max_portfolio_risk": 0.15
        },
        "strategy_templates": {
            "directional_long": {
                "stop_loss_pct": 0.05,
                "take_profit_levels": [0.10, 0.18],
                "risk_reward_ratio": 2.5
            },
            "long_short_hedge": {
                "stop_loss_pct": 0.04,
                "take_profit_levels": [0.08, 0.12],
                "risk_reward_ratio": 2.0
            },
            "range_trading": {
                "stop_loss_pct": 0.03,
                "take_profit_levels": [0.04, 0.06],
                "risk_reward_ratio": 1.5
            }
        }
    }

def run_hedge_demo(ticker: str, capital: float, quick: bool = False):
    """Run hedge engine demonstration"""
    
    if RICH_AVAILABLE:
        console.print(Panel.fit("🏦 TradingAgents Hedge Engine Demo", style="bold blue"))
        console.print(f"Ticker: [cyan]{ticker}[/cyan] | Capital: [green]${capital:,.2f}[/green]")
    else:
        console.print("=" * 60)
        console.print("🏦 TradingAgents Hedge Engine Demo")
        console.print("=" * 60)
        console.print(f"Ticker: {ticker} | Capital: ${capital:,.2f}")
    
    try:
        # Import hedge engine
        from hedge_engine.decision_engine import HedgeDecisionEngine
        
        # Load configuration
        config = load_hedge_config()
        
        # Initialize decision engine
        engine = HedgeDecisionEngine(config)
        
        # Simulate TradingAgents analysis
        console.print("\n🔍 Running Multi-Agent Analysis...")
        analysis_phases = [
            "📈 Technical Analysis...",
            "📰 News Analysis...", 
            "😊 Sentiment Analysis...",
            "💰 Fundamental Analysis...",
            "🤔 Researcher Debate...",
            "⚖️ Risk Assessment..."
        ]
        
        if RICH_AVAILABLE:
            for phase in track(analysis_phases, description="Processing..."):
                console.print(f"  {phase}", style="dim")
        else:
            for phase in analysis_phases:
                console.print(f"  {phase}")
        
        # Create mock analysis data based on ticker
        ticker_data = {
            "BTCUSDT": {"price": 64350.0, "sentiment": 0.72, "trend": "bullish"},
            "BTC": {"price": 64350.0, "sentiment": 0.72, "trend": "bullish"},
            "NVDA": {"price": 140.50, "sentiment": 0.78, "trend": "bullish"},
            "TSLA": {"price": 248.75, "sentiment": 0.65, "trend": "neutral"},
            "AAPL": {"price": 185.20, "sentiment": 0.70, "trend": "bullish"}
        }
        
        ticker_upper = ticker.upper()
        data = ticker_data.get(ticker_upper, ticker_data["BTC"])
        
        mock_analysis_data = {
            "technical_analysis": {
                "current_price": data["price"],
                "trend": data["trend"],
                "support_levels": [data["price"] * 0.95, data["price"] * 0.90],
                "resistance_levels": [data["price"] * 1.05, data["price"] * 1.10],
                "rsi": 65.2 if data["trend"] == "bullish" else 45.8,
                "summary": f"Strong {data['trend']} momentum with good support"
            },
            "sentiment_analysis": {
                "overall_score": data["sentiment"],
                "summary": "Generally positive sentiment" if data["sentiment"] > 0.6 else "Mixed sentiment"
            },
            "fundamental_analysis": {
                "score": data["trend"],
                "summary": "Strong fundamental backdrop" if data["trend"] == "bullish" else "Neutral fundamentals"
            }
        }
        
        # Generate hedge recommendations
        console.print("\n🧠 Generating Hedge Strategies...")
        recommendation = engine.process_trading_decision(
            ticker=ticker,
            capital=capital,
            analysis_data=mock_analysis_data
        )
        
        # Display results
        display_hedge_results(recommendation)
        
        # Export option
        export_file = engine.export_recommendation(recommendation)
        console.print(f"\n📄 Report exported to: [cyan]{export_file}[/cyan]")
        
    except ImportError as e:
        console.print(f"\n❌ Import Error: {str(e)}")
        console.print("Make sure all hedge engine files are in the correct locations:")
        console.print("  hedge_engine/market_regime_detector.py")
        console.print("  hedge_engine/strategy_generator.py") 
        console.print("  hedge_engine/position_sizer.py")
        console.print("  hedge_engine/decision_engine.py")
        console.print("  hedge_engine/__init__.py")
    except Exception as e:
        console.print(f"\n❌ Error: {str(e)}")

def display_hedge_results(rec):
    """Display hedge results in formatted output"""
    
    # Market Regime Panel
    regime_text = f"{rec.market_regime.replace('_', ' ').title()}\nConfidence: {rec.regime_confidence:.1%}"
    
    if RICH_AVAILABLE:
        console.print(Panel(regime_text, title="🎯 Market Regime", style="green"))
    else:
        console.print("\n🎯 Market Regime")
        console.print("-" * 20)
        console.print(regime_text)
    
    # Recommended Strategy
    strategy = rec.recommended_strategy
    
    if strategy.direction == "wait":
        strategy_text = f"⏳ {strategy.name}\n{strategy.description}"
        if RICH_AVAILABLE:
            console.print(Panel(strategy_text, title="💡 Recommended Action", style="yellow"))
        else:
            console.print("\n💡 Recommended Action")
            console.print("-" * 25)
            console.print(strategy_text)
    else:
        strategy_details = [
            f"Direction: {strategy.direction.upper()}",
            f"Entry: ${strategy.entry_price:,.2f}",
            f"Stop Loss: ${strategy.stop_loss:,.2f}",
            f"Take Profit 1: ${strategy.take_profit_1:,.2f}"
        ]
        
        if strategy.take_profit_2:
            strategy_details.append(f"Take Profit 2: ${strategy.take_profit_2:,.2f}")
        
        strategy_details.extend([
            f"Position Size: {strategy.position_size:.6f} units",
            f"Confidence: {strategy.confidence:.1%}"
        ])
        
        if RICH_AVAILABLE:
            console.print(Panel("\n".join(strategy_details), title="💎 Recommended Strategy", style="blue"))
        else:
            console.print("\n💎 Recommended Strategy")
            console.print("-" * 25)
            for detail in strategy_details:
                console.print(detail)
    
    # Risk Summary
    risk_data = [
        ["Risk per Trade", f"${rec.risk_summary.get('risk_per_trade', 0):,.2f}"],
        ["Risk Percentage", f"{rec.risk_summary.get('risk_percentage', 0):.2f}%"],
        ["Capital Allocation", f"{rec.risk_summary.get('capital_allocation', 0):.1f}%"],
        ["Risk/Reward Ratio", f"1:{strategy.risk_reward_ratio:.1f}"]
    ]
    
    if RICH_AVAILABLE:
        risk_table = Table(title="📊 Risk Management Dashboard")
        risk_table.add_column("Metric", style="cyan")
        risk_table.add_column("Value", style="magenta")
        for metric, value in risk_data:
            risk_table.add_row(metric, value)
        console.print(risk_table)
    else:
        console.print("\n📊 Risk Management Dashboard")
        console.print("-" * 30)
        for metric, value in risk_data:
            console.print(f"{metric}: {value}")
    
    # Strategy Options
    console.print(f"\n📋 All Strategy Options ({len(rec.strategies)} options):")
    console.print("-" * 40)
    for i, strat in enumerate(rec.strategies, 1):
        entry_text = f"${strat.entry_price:,.2f}" if strat.entry_price > 0 else "N/A"
        console.print(f"{i}. {strat.name} ({strat.direction.upper()}) - {strat.confidence:.1%} - Entry: {entry_text}")

def main():
    """Main CLI function"""
    parser = argparse.ArgumentParser(description='TradingAgents Hedge Engine CLI Demo')
    parser.add_argument('command', nargs='?', default='hedge', help='Command to run')
    parser.add_argument('--ticker', '-t', default='BTCUSDT', help='Trading ticker (default: BTCUSDT)')
    parser.add_argument('--capital', '-c', type=float, default=26300, help='Available capital (default: 26300)')
    parser.add_argument('--quick', '-q', action='store_true', help='Quick analysis mode')
    
    args = parser.parse_args()
    
    if args.command == 'hedge':
        run_hedge_demo(args.ticker, args.capital, args.quick)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()