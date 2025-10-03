"""
Decision Engine for TradingAgents Hedge Engine
Main orchestrator that coordinates all components
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import json
from datetime import datetime

from market_regime_detector import MarketRegimeDetector, RegimeMetrics
from strategy_generator import StrategyGenerator, TradingStrategy
from position_sizer import PositionSizer

@dataclass
class HedgeRecommendation:
    ticker: str
    timestamp: datetime
    current_price: float
    capital: float
    market_regime: str
    regime_confidence: float
    strategies: List[TradingStrategy]
    recommended_strategy: TradingStrategy
    risk_summary: Dict
    execution_plan: Dict

class HedgeDecisionEngine:
    """
    Main decision engine that coordinates all hedge components
    """
    
    def __init__(self, config: Dict):
        self.config = config
        self.regime_detector = MarketRegimeDetector(config)
        self.strategy_generator = StrategyGenerator(config)
        self.position_sizer = PositionSizer(config)
    
    def process_trading_decision(
        self,
        ticker: str,
        capital: float,
        analysis_data: Dict,
        current_price: Optional[float] = None
    ) -> HedgeRecommendation:
        """
        Main method to process TradingAgents analysis into hedge recommendations
        """
        
        # Extract current price from analysis if not provided
        if current_price is None:
            current_price = self._extract_current_price(analysis_data)
        
        # Step 1: Detect Market Regime
        regime_metrics = self.regime_detector.detect_regime(analysis_data)
        
        # Step 2: Generate Strategies
        strategies = self.strategy_generator.generate_strategies(
            regime_metrics, analysis_data, current_price, capital
        )
        
        # Step 3: Calculate Position Sizes
        for strategy in strategies:
            if strategy.direction != "wait":
                strategy.position_size = self.position_sizer.calculate_position_size(
                    strategy, capital, current_price
                )
                strategy.position_size = self.position_sizer.validate_position_size(
                    strategy.position_size, strategy.entry_price, capital
                )
        
        # Step 4: Apply Portfolio Risk Limits
        strategies = self.position_sizer.apply_portfolio_risk_limits(strategies, capital)
        
        # Step 5: Select Recommended Strategy
        recommended_strategy = self._select_best_strategy(strategies, regime_metrics)
        
        # Step 6: Create Risk Summary
        risk_summary = self._create_risk_summary(recommended_strategy, capital)
        
        # Step 7: Create Execution Plan
        execution_plan = self._create_execution_plan(recommended_strategy, analysis_data)
        
        return HedgeRecommendation(
            ticker=ticker,
            timestamp=datetime.now(),
            current_price=current_price,
            capital=capital,
            market_regime=regime_metrics.regime.value,
            regime_confidence=regime_metrics.confidence,
            strategies=strategies,
            recommended_strategy=recommended_strategy,
            risk_summary=risk_summary,
            execution_plan=execution_plan
        )
    
    def _extract_current_price(self, analysis_data: Dict) -> float:
        """Extract current price from TradingAgents analysis data"""
        # Try multiple possible locations for price data
        technical_data = analysis_data.get("technical_analysis", {})
        if "current_price" in technical_data:
            return float(technical_data["current_price"])
        
        # Try to get from price data
        if "price_data" in technical_data:
            price_data = technical_data["price_data"]
            if isinstance(price_data, (list, tuple)) and len(price_data) > 0:
                return float(price_data[-1])
        
        # Try sentiment or other sections
        sentiment_data = analysis_data.get("sentiment_analysis", {})
        if "current_price" in sentiment_data:
            return float(sentiment_data["current_price"])
        
        # Fallback based on ticker for demo
        ticker_prices = {
            "BTCUSDT": 64350.0,
            "BTC": 64350.0,
            "NVDA": 140.50,
            "TSLA": 248.75,
            "AAPL": 185.20,
            "MSFT": 420.85
        }
        
        # Try to extract ticker from analysis data
        ticker = analysis_data.get("ticker", "BTC")
        return ticker_prices.get(ticker.upper(), 64350.0)
    
    def _select_best_strategy(
        self, 
        strategies: List[TradingStrategy], 
        regime_metrics: RegimeMetrics
    ) -> TradingStrategy:
        """Select the best strategy based on confidence and risk-reward"""
        if not strategies:
            # Create a default wait strategy
            return TradingStrategy(
                name="No Clear Signal",
                description="Market conditions unclear, wait for better setup",
                direction="wait",
                entry_price=0.0,
                stop_loss=0.0,
                take_profit_1=0.0,
                take_profit_2=None,
                position_size=0.0,
                leverage=0.0,
                confidence=0.5,
                risk_reward_ratio=0.0,
                strategy_type="wait"
            )
        
        # Filter out strategies with zero position size (unless they're wait strategies)
        viable_strategies = [s for s in strategies if s.direction == "wait" or s.position_size > 0]
        
        if not viable_strategies:
            viable_strategies = strategies  # Fallback to all strategies
        
        # Score strategies based on multiple factors
        scored_strategies = []
        for strategy in viable_strategies:
            # Base score from confidence
            confidence_score = strategy.confidence * 0.4
            
            # Risk-reward score (normalized to 0-1, cap at 3.0 ratio)
            rr_score = min(strategy.risk_reward_ratio / 3.0, 1.0) * 0.3
            
            # Action bias (prefer actionable strategies over wait)
            action_score = 0.3 if strategy.direction != "wait" else 0.1
            
            # Position size viability (prefer strategies with reasonable position sizes)
            size_score = 0.1 if strategy.position_size > 0 or strategy.direction == "wait" else 0.0
            
            total_score = confidence_score + rr_score + action_score + size_score
            scored_strategies.append((total_score, strategy))
        
        # Return highest scoring strategy
        scored_strategies.sort(key=lambda x: x[0], reverse=True)
        return scored_strategies[0][1]
    
    def _create_risk_summary(self, strategy: TradingStrategy, capital: float) -> Dict:
        """Create risk summary for the recommended strategy"""
        if strategy.direction == "wait" or strategy.position_size <= 0:
            return {
                "risk_per_trade": 0.0,
                "risk_percentage": 0.0,
                "position_value": 0.0,
                "max_loss": 0.0,
                "risk_reward_ratio": 0.0,
                "capital_allocation": 0.0,
                "potential_profit_1": 0.0,
                "potential_profit_2": 0.0
            }
        
        # Use position sizer to get comprehensive metrics
        metrics = self.position_sizer.calculate_position_metrics(strategy, capital)
        
        return {
            "risk_per_trade": metrics["risk_amount"],
            "risk_percentage": metrics["risk_percentage"],
            "position_value": metrics["position_value"],
            "max_loss": metrics["risk_amount"],  # Same as risk_amount
            "risk_reward_ratio": strategy.risk_reward_ratio,
            "capital_allocation": metrics["capital_allocation"],
            "potential_profit_1": metrics["potential_profit_1"],
            "potential_profit_2": metrics["potential_profit_2"]
        }
    
    def _create_execution_plan(self, strategy: TradingStrategy, analysis_data: Dict) -> Dict:
        """Create detailed execution plan"""
        if strategy.direction == "wait":
            return {
                "action": "WAIT",
                "reason": strategy.description,
                "next_review": "Monitor for regime change or clearer signals",
                "conditions_to_watch": [
                    "Trend strength improvement",
                    "Volatility normalization", 
                    "Volume confirmation",
                    "Sentiment shift"
                ],
                "risk_management": {
                    "stop_loss_type": "N/A",
                    "position_monitoring": "Market observation"
                }
            }
        
        # Extract key insights from analysis
        sentiment_summary = analysis_data.get("sentiment_analysis", {}).get("summary", "Mixed sentiment")
        technical_summary = analysis_data.get("technical_analysis", {}).get("summary", "Technical analysis pending")
        news_summary = analysis_data.get("news_analysis", {}).get("summary", "No significant news")
        
        execution_plan = {
            "action": strategy.direction.upper(),
            "entry_method": "Market order" if strategy.confidence > 0.8 else "Limit order",
            "position_details": {
                "size": f"{strategy.position_size:.6f} units",
                "value": f"${strategy.position_size * strategy.entry_price:,.2f}",
                "leverage": f"{strategy.leverage}x"
            },
            "risk_management": {
                "stop_loss_type": "Hard stop",
                "stop_loss_level": f"${strategy.stop_loss:,.2f}",
                "take_profit_method": "Scaled exit",
                "position_monitoring": "Continuous"
            },
            "market_conditions": {
                "sentiment": sentiment_summary,
                "technical": technical_summary,
                "news": news_summary,
                "regime_confidence": f"{strategy.confidence:.1%}"
            },
            "exit_strategy": {
                "stop_loss_trigger": f"Price reaches ${strategy.stop_loss:,.2f}",
                "take_profit_1": f"Take 50% profit at ${strategy.take_profit_1:,.2f}",
                "take_profit_2": f"Take remaining profit at ${strategy.take_profit_2:,.2f}" if strategy.take_profit_2 else "N/A",
                "trailing_stop": "Consider implementing after TP1 hit"
            },
            "review_schedule": {
                "immediate": "Monitor for first 30 minutes after entry",
                "short_term": "Review position every 4 hours",
                "daily": "Comprehensive review at market close",
                "triggers": ["10% adverse move", "regime change", "significant news"]
            }
        }
        
        return execution_plan
    
    def export_recommendation(self, recommendation: HedgeRecommendation, output_dir: str = "hedge_results") -> str:
        """Export recommendation to markdown file"""
        import os
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate filename
        timestamp = recommendation.timestamp.strftime("%Y%m%d_%H%M%S")
        filename = f"{output_dir}/hedge_recommendation_{recommendation.ticker}_{timestamp}.md"
        
        # Generate markdown content
        content = self._generate_markdown_report(recommendation)
        
        # Write to file
        with open(filename, 'w') as f:
            f.write(content)
        
        return filename
    
    def _generate_markdown_report(self, rec: HedgeRecommendation) -> str:
        """Generate detailed markdown report"""
        
        report = f"""# TradingAgents Hedge Recommendation Report

## Executive Summary
**Ticker:** {rec.ticker}  
**Date:** {rec.timestamp.strftime("%Y-%m-%d %H:%M:%S")}  
**Current Price:** ${rec.current_price:,.2f}  
**Available Capital:** ${rec.capital:,.2f}  

**Market Regime:** {rec.market_regime.replace('_', ' ').title()} (Confidence: {rec.regime_confidence:.1%})

## Recommended Strategy: {rec.recommended_strategy.name}

{rec.recommended_strategy.description}

### Trade Details
- **Direction:** {rec.recommended_strategy.direction.upper()}
- **Entry Price:** ${rec.recommended_strategy.entry_price:,.2f}
- **Stop Loss:** ${rec.recommended_strategy.stop_loss:,.2f}
- **Take Profit 1:** ${rec.recommended_strategy.take_profit_1:,.2f}
- **Take Profit 2:** {f"${rec.recommended_strategy.take_profit_2:,.2f}" if rec.recommended_strategy.take_profit_2 else "N/A"}
- **Position Size:** {rec.recommended_strategy.position_size:.6f} units
- **Position Value:** ${rec.recommended_strategy.position_size * rec.recommended_strategy.entry_price:,.2f}
- **Leverage:** {rec.recommended_strategy.leverage}x
- **Confidence:** {rec.recommended_strategy.confidence:.1%}

### Risk Management
- **Risk per Trade:** ${rec.risk_summary.get('risk_per_trade', 0):,.2f}
- **Risk Percentage:** {rec.risk_summary.get('risk_percentage', 0):.2f}%
- **Capital Allocation:** {rec.risk_summary.get('capital_allocation', 0):.1f}%
- **Risk/Reward Ratio:** 1:{rec.recommended_strategy.risk_reward_ratio:.1f}
- **Potential Profit 1:** ${rec.risk_summary.get('potential_profit_1', 0):,.2f}
- **Potential Profit 2:** ${rec.risk_summary.get('potential_profit_2', 0):,.2f}

## All Strategy Options

"""
        
        for i, strategy in enumerate(rec.strategies, 1):
            if strategy.direction == "wait":
                report += f"### Option {i}: {strategy.name}\n"
                report += f"**Action:** {strategy.description}\n"
                report += f"**Confidence:** {strategy.confidence:.1%}\n\n"
            else:
                report += f"### Option {i}: {strategy.name}\n"
                report += f"- **Direction:** {strategy.direction.upper()}\n"
                report += f"- **Entry:** ${strategy.entry_price:,.2f}\n"
                report += f"- **Stop Loss:** ${strategy.stop_loss:,.2f}\n"
                report += f"- **Take Profit:** ${strategy.take_profit_1:,.2f}\n"
                report += f"- **Position Size:** {strategy.position_size:.6f} units\n"
                report += f"- **Confidence:** {strategy.confidence:.1%}\n"
                report += f"- **Description:** {strategy.description}\n\n"
        
        exec_plan = rec.execution_plan
        report += f"""## Execution Plan

**Primary Action:** {exec_plan.get('action', 'TBD')}

**Entry Method:** {exec_plan.get('entry_method', 'TBD')}

### Position Details
"""
        
        if 'position_details' in exec_plan:
            pd = exec_plan['position_details']
            report += f"- **Size:** {pd.get('size', 'TBD')}\n"
            report += f"- **Value:** {pd.get('value', 'TBD')}\n"
            report += f"- **Leverage:** {pd.get('leverage', 'TBD')}\n\n"
        
        report += f"""### Risk Management
"""
        
        if 'risk_management' in exec_plan:
            rm = exec_plan['risk_management']
            report += f"- **Stop Loss Type:** {rm.get('stop_loss_type', 'TBD')}\n"
            report += f"- **Stop Loss Level:** {rm.get('stop_loss_level', 'TBD')}\n"
            report += f"- **Take Profit Method:** {rm.get('take_profit_method', 'TBD')}\n"
            report += f"- **Position Monitoring:** {rm.get('position_monitoring', 'TBD')}\n\n"
        
        report += f"""### Exit Strategy
"""
        
        if 'exit_strategy' in exec_plan:
            es = exec_plan['exit_strategy']
            for key, value in es.items():
                report += f"- **{key.replace('_', ' ').title()}:** {value}\n"
        
        report += f"""

### Market Conditions Assessment
"""
        
        if 'market_conditions' in exec_plan:
            mc = exec_plan['market_conditions']
            report += f"- **Technical Analysis:** {mc.get('technical', 'TBD')}\n"
            report += f"- **Sentiment Analysis:** {mc.get('sentiment', 'TBD')}\n"
            report += f"- **News Analysis:** {mc.get('news', 'TBD')}\n"
            report += f"- **Regime Confidence:** {mc.get('regime_confidence', 'TBD')}\n\n"
        
        report += f"""## Risk Disclaimer

This recommendation is generated by an AI system for educational and research purposes only. 
It is not financial advice. Trading involves substantial risk and may not be suitable for all investors.
Always conduct your own research and consider consulting with a qualified financial advisor.

---
*Generated by TradingAgents Hedge Engine v1.0*
*Report ID: {rec.ticker}_{rec.timestamp.strftime("%Y%m%d_%H%M%S")}*
"""
        
        return report