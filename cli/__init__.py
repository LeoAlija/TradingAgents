"""
TradingAgents Hedge Engine
A comprehensive hedge fund style enhancement for TradingAgents

This module provides:
- Market regime detection
- Strategy generation  
- Position sizing
- Risk management
- Decision orchestration
"""

from .market_regime_detector import MarketRegimeDetector, MarketRegime
from .strategy_generator import StrategyGenerator, TradingStrategy
from .position_sizer import PositionSizer
from .decision_engine import HedgeDecisionEngine, HedgeRecommendation

__version__ = "1.0.0"
__author__ = "TradingAgents Team"

__all__ = [
    "MarketRegimeDetector",
    "MarketRegime", 
    "StrategyGenerator",
    "TradingStrategy",
    "PositionSizer",
    "HedgeDecisionEngine",
    "HedgeRecommendation"
]
