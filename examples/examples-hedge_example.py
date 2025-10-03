"""
Enhanced TradingAgents Main File with Hedge Engine Integration
Demonstrates how to use both traditional analysis and hedge recommendations
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG

# Import our hedge engine components
from hedge_engine.decision_engine import HedgeDecisionEngine
import json

def run_traditional_analysis(ticker: str, date: str) -> tuple:
    """Run traditional TradingAgents analysis"""
    # Create a custom config
    config = DEFAULT_CONFIG.copy()
    config["llm_provider"] = "openai"  # Use OpenAI for compatibility
    config["deep_think_llm"] = "gpt-4o-mini"  # Cost-effective for testing
    config["quick_think_llm"] = "gpt-4o-mini"  # Cost-effective for testing
    config["max_debate_rounds"] = 1  # Limit rounds for faster execution
    config["online_tools"] = True  # Use real-time data

    # Initialize with custom config
    ta = TradingAgentsGraph(debug=True, config=config)

    # Forward propagate
    analysis_result, decision = ta.propagate(ticker, date)
    
    return analysis_result, decision

def run_hedge_analysis(ticker: str, capital: float, analysis_data: dict) -> dict:
    """Run hedge engine analysis on top of TradingAgents results"""
    
    # Load hedge configuration
    hedge_config = {
        "market_regimes": {
            "strong_bull": {
                "criteria": {
                    "trend_strength": "> 0.7",
                    "volatility": "< 0.3",
                    "momentum": "> 0.6"
                },
                "strategies": ["directional_long", "momentum_breakout"]
            },
            "weak_bull": {
                "criteria": {
                    "trend_strength": "0.3 to 0.7",
                    "volatility": "< 0.5",
                    "momentum": "0.2 to 0.6"
                },
                "strategies": ["long_bias", "mean_reversion_long"]
            },
            "sideways": {
                "criteria": {
                    "trend_strength": "< 0.3",
                    "volatility": "< 0.4",
                    "momentum": "-0.2 to 0.2"
                },
                "strategies": ["range_trading", "straddle", "wait"]
            }
        },
        "risk_management": {
            "max_risk_per_trade": 0.02,
            "max_portfolio_risk": 0.15,
            "stop_loss_range": [0.03, 0.10],
            "take_profit_multiplier": [2.0, 3.5]
        },
        "strategy_templates": {
            "directional_long": {
                "description": "Pure long position with defined risk management",
                "entry_conditions": ["bullish_signals", "momentum_confirmation"],
                "risk_reward_ratio": 2.5,
                "stop_loss_pct": 0.05,
                "take_profit_levels": [0.10, 0.18]
            },
            "long_short_hedge": {
                "description": "Long primary + short hedge to reduce market risk",
                "entry_conditions": ["mixed_signals", "high_correlation"],
                "hedge_ratio": 0.3,
                "stop_loss_pct": 0.04,
                "take_profit_levels": [0.08, 0.12]
            }
        }
    }
    
    # Initialize hedge engine
    hedge_engine = HedgeDecisionEngine(hedge_config)
    
    # Process the analysis into hedge recommendations
    recommendation = hedge_engine.process_trading_decision(
        ticker=ticker,
        capital=capital,
        analysis_data=analysis_data
    )
    
    return recommendation

def display_comprehensive_results(ticker: str, traditional_decision: str, hedge_recommendation: dict):
    """Display both traditional and hedge results"""
    
    print("\n" + "="*80)
    print(f" 🏦 COMPREHENSIVE TRADING ANALYSIS: {ticker}")
    print("="*80)
    
    # Traditional Analysis Results
    print("\n📊 TRADITIONAL TRADINGAGENTS ANALYSIS:")
    print("-" * 50)
    print(f"Decision: {traditional_decision}")
    
    # Hedge Analysis Results  
    print("\n🎯 HEDGE ENGINE RECOMMENDATIONS:")
    print("-" * 50)
    
    rec = hedge_recommendation
    print(f"Market Regime: {rec.market_regime.replace('_', ' ').title()} (Confidence: {rec.regime_confidence:.1%})")
    print(f"Current Price: ${rec.current_price:,.2f}")
    
    # Recommended Strategy
    strategy = rec.recommended_strategy
    if strategy.direction == "wait":
        print(f"\n⏳ RECOMMENDED ACTION: {strategy.name}")
        print(f"Reason: {strategy.description}")
    else:
        print(f"\n💎 RECOMMENDED STRATEGY: {strategy.name}")
        print(f"Direction: {strategy.direction.upper()}")
        print(f"Entry Price: ${strategy.entry_price:,.2f}")
        print(f"Stop Loss: ${strategy.stop_loss:,.2f}")
        print(f"Take Profit 1: ${strategy.take_profit_1:,.2f}")
        if strategy.take_profit_2:
            print(f"Take Profit 2: ${strategy.take_profit_2:,.2f}")
        print(f"Position Size: {strategy.position_size:.6f} units")
        print(f"Confidence: {strategy.confidence:.1%}")
    
    # Risk Summary
    print("\n📈 RISK MANAGEMENT:")
    print("-" * 30)
    risk = rec.risk_summary
    print(f"Risk per Trade: ${risk.get('risk_per_trade', 0):,.2f}")
    print(f"Risk Percentage: {risk.get('risk_percentage', 0):.2f}%")
    print(f"Capital Allocation: {risk.get('capital_allocation', 0):.1f}%")
    print(f"Risk/Reward Ratio: 1:{strategy.risk_reward_ratio:.1f}")
    
    # All Strategy Options
    print("\n📋 ALL STRATEGY OPTIONS:")
    print("-" * 40)
    for i, strat in enumerate(rec.strategies, 1):
        print(f"{i}. {strat.name} ({strat.direction}) - Confidence: {strat.confidence:.1%}")
    
    print("\n" + "="*80)

def main():
    """Main execution function"""
    
    # Configuration
    TICKER = "NVDA"
    DATE = "2024-12-27" 
    CAPITAL = 26300.0
    
    print("🚀 Starting TradingAgents POC: Hedge-Fund Style Enhancement")
    print(f"Analyzing {TICKER} with ${CAPITAL:,.2f} capital")
    
    try:
        # Step 1: Run Traditional TradingAgents Analysis
        print("\n🔍 Running Traditional Multi-Agent Analysis...")
        # analysis_result, traditional_decision = run_traditional_analysis(TICKER, DATE)
        
        # For demo purposes, simulate traditional analysis
        traditional_decision = "BULLISH - Strong technical momentum with positive sentiment"
        
        # Step 2: Run Hedge Engine Analysis
        print("\n🧠 Processing with Hedge Engine...")
        # Convert traditional analysis to format expected by hedge engine
        mock_analysis_data = {
            "technical_analysis": {
                "current_price": 140.50,  # Example NVDA price
                "trend": "bullish",
                "price_data": [135, 137, 139, 138, 140, 142, 140.5] * 10  # Mock price series
            },
            "sentiment_analysis": {
                "overall_score": 0.75,
                "summary": "Positive sentiment driven by AI developments"
            },
            "fundamental_analysis": {
                "score": "bullish", 
                "summary": "Strong AI growth prospects"
            },
            "decision": traditional_decision
        }
        
        hedge_recommendation = run_hedge_analysis(TICKER, CAPITAL, mock_analysis_data)
        
        # Step 3: Display Comprehensive Results
        display_comprehensive_results(TICKER, traditional_decision, hedge_recommendation)
        
        # Step 4: Export Results (Optional)
        print("\n💾 Exporting detailed report...")
        filename = hedge_recommendation.engine.export_recommendation(hedge_recommendation) if hasattr(hedge_recommendation, 'engine') else None
        if filename:
            print(f"📄 Report saved to: {filename}")
        
        print("\n✅ Analysis Complete!")
        
    except Exception as e:
        print(f"\n❌ Error during analysis: {str(e)}")
        print("This is expected if TradingAgents dependencies are not fully installed.")
        print("The hedge engine code is ready for integration when dependencies are available.")

    # Demonstrate just the hedge engine without TradingAgents
    print("\n" + "="*60)
    print("🧪 HEDGE ENGINE STANDALONE DEMO")
    print("="*60)
    
    try:
        # Load configuration from file
        config_path = os.path.join(os.path.dirname(__file__), '..', 'configs', 'hedge_config.json')
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
        else:
            # Use embedded config if file not found
            config = {
                "market_regimes": {"strong_bull": {"criteria": {}}},
                "risk_management": {"max_risk_per_trade": 0.02},
                "strategy_templates": {"directional_long": {"stop_loss_pct": 0.05}}
            }
        
        # Initialize hedge engine
        hedge_engine = HedgeDecisionEngine(config)
        
        # Mock analysis data for demo
        demo_analysis = {
            "technical_analysis": {"current_price": 64350.0},
            "sentiment_analysis": {"overall_score": 0.7}
        }
        
        # Generate recommendation
        recommendation = hedge_engine.process_trading_decision(
            ticker="BTCUSDT",
            capital=26300,
            analysis_data=demo_analysis
        )
        
        # Display results
        print(f"✅ Hedge Engine Working!")
        print(f"🎯 Market Regime: {recommendation.market_regime}")
        print(f"💡 Recommended: {recommendation.recommended_strategy.name}")
        print(f"📈 Entry: ${recommendation.recommended_strategy.entry_price:,.2f}")
        print(f"🛑 Stop: ${recommendation.recommended_strategy.stop_loss:,.2f}")
        print(f"🎯 Target: ${recommendation.recommended_strategy.take_profit_1:,.2f}")
        
    except Exception as e:
        print(f"❌ Hedge Engine Error: {str(e)}")
        print("Check that all hedge engine files are properly installed.")

if __name__ == "__main__":
    main()