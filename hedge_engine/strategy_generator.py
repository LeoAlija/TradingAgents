"""
Strategy Generator for TradingAgents Hedge Engine
Generates specific trading strategies based on market regime and analysis
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from market_regime_detector import MarketRegime, RegimeMetrics

@dataclass
class TradingStrategy:
    name: str
    description: str
    direction: str  # "long", "short", "hedge", "straddle", "wait"
    entry_price: float
    stop_loss: float
    take_profit_1: float
    take_profit_2: Optional[float]
    position_size: float
    leverage: float
    confidence: float
    risk_reward_ratio: float
    strategy_type: str

class StrategyGenerator:
    """
    Generates trading strategies based on market regime and analysis
    """
    
    def __init__(self, config: Dict):
        self.config = config
        self.strategy_templates = config.get("strategy_templates", {})
        self.risk_params = config.get("risk_management", {})
    
    def generate_strategies(
        self, 
        regime_metrics: RegimeMetrics,
        analysis_data: Dict,
        current_price: float,
        capital: float
    ) -> List[TradingStrategy]:
        """
        Generate 2-3 strategy options based on market regime
        """
        strategies = []
        
        if regime_metrics.regime == MarketRegime.STRONG_BULL:
            strategies.extend(self._generate_bull_strategies(
                analysis_data, current_price, capital, regime_metrics.confidence
            ))
        
        elif regime_metrics.regime == MarketRegime.WEAK_BULL:
            strategies.extend(self._generate_weak_bull_strategies(
                analysis_data, current_price, capital, regime_metrics.confidence
            ))
        
        elif regime_metrics.regime == MarketRegime.SIDEWAYS:
            strategies.extend(self._generate_sideways_strategies(
                analysis_data, current_price, capital, regime_metrics.confidence
            ))
        
        elif regime_metrics.regime == MarketRegime.WEAK_BEAR:
            strategies.extend(self._generate_weak_bear_strategies(
                analysis_data, current_price, capital, regime_metrics.confidence
            ))
        
        elif regime_metrics.regime == MarketRegime.STRONG_BEAR:
            strategies.extend(self._generate_bear_strategies(
                analysis_data, current_price, capital, regime_metrics.confidence
            ))
        
        elif regime_metrics.regime == MarketRegime.HIGH_VOLATILITY:
            strategies.extend(self._generate_volatility_strategies(
                analysis_data, current_price, capital, regime_metrics.confidence
            ))
        
        return strategies[:3]  # Return top 3 strategies
    
    def _generate_bull_strategies(
        self, analysis_data: Dict, current_price: float, capital: float, confidence: float
    ) -> List[TradingStrategy]:
        """Generate strategies for strong bull market"""
        strategies = []
        
        # Strategy 1: Directional Long
        template = self.strategy_templates.get("directional_long", {})
        stop_loss_pct = template.get("stop_loss_pct", 0.05)
        tp1_pct, tp2_pct = template.get("take_profit_levels", [0.10, 0.18])
        
        strategies.append(TradingStrategy(
            name="Directional Long",
            description="Pure long position capitalizing on bull momentum",
            direction="long",
            entry_price=current_price,
            stop_loss=current_price * (1 - stop_loss_pct),
            take_profit_1=current_price * (1 + tp1_pct),
            take_profit_2=current_price * (1 + tp2_pct),
            position_size=0.0,  # To be calculated by position sizer
            leverage=1.0,
            confidence=confidence * 0.9,
            risk_reward_ratio=tp1_pct / stop_loss_pct,
            strategy_type="directional_long"
        ))
        
        # Strategy 2: Momentum Breakout
        strategies.append(TradingStrategy(
            name="Momentum Breakout",
            description="Breakout strategy with tight stops",
            direction="long",
            entry_price=current_price * 1.02,  # Enter on 2% breakout
            stop_loss=current_price * 0.97,
            take_profit_1=current_price * 1.12,
            take_profit_2=current_price * 1.20,
            position_size=0.0,
            leverage=1.5,
            confidence=confidence * 0.8,
            risk_reward_ratio=2.0,
            strategy_type="momentum_breakout"
        ))
        
        return strategies
    
    def _generate_weak_bull_strategies(
        self, analysis_data: Dict, current_price: float, capital: float, confidence: float
    ) -> List[TradingStrategy]:
        """Generate strategies for weak bull market"""
        strategies = []
        
        # Strategy 1: Long with hedge
        strategies.append(TradingStrategy(
            name="Long with Hedge",
            description="Long position with partial short hedge for protection",
            direction="hedge",
            entry_price=current_price,
            stop_loss=current_price * 0.96,
            take_profit_1=current_price * 1.08,
            take_profit_2=current_price * 1.12,
            position_size=0.0,
            leverage=1.0,
            confidence=confidence * 0.8,
            risk_reward_ratio=2.0,
            strategy_type="long_short_hedge"
        ))
        
        # Strategy 2: Conservative Long
        strategies.append(TradingStrategy(
            name="Conservative Long",
            description="Lower risk long position with tight management",
            direction="long",
            entry_price=current_price * 0.99,  # Buy slight dip
            stop_loss=current_price * 0.95,
            take_profit_1=current_price * 1.06,
            take_profit_2=current_price * 1.10,
            position_size=0.0,
            leverage=1.0,
            confidence=confidence * 0.85,
            risk_reward_ratio=1.5,
            strategy_type="conservative_long"
        ))
        
        return strategies
    
    def _generate_sideways_strategies(
        self, analysis_data: Dict, current_price: float, capital: float, confidence: float
    ) -> List[TradingStrategy]:
        """Generate strategies for sideways market"""
        strategies = []
        
        # Strategy 1: Range Trading
        strategies.append(TradingStrategy(
            name="Range Trading",
            description="Buy support, sell resistance in range-bound market",
            direction="range",
            entry_price=current_price * 0.98,  # Buy near support
            stop_loss=current_price * 0.95,
            take_profit_1=current_price * 1.04,  # Sell near resistance
            take_profit_2=None,
            position_size=0.0,
            leverage=1.0,
            confidence=confidence * 0.7,
            risk_reward_ratio=1.3,
            strategy_type="range_trading"
        ))
        
        # Strategy 2: Wait Signal
        strategies.append(TradingStrategy(
            name="Wait for Breakout",
            description="Wait for clear directional break from range",
            direction="wait",
            entry_price=0.0,
            stop_loss=0.0,
            take_profit_1=0.0,
            take_profit_2=None,
            position_size=0.0,
            leverage=0.0,
            confidence=0.9,
            risk_reward_ratio=0.0,
            strategy_type="wait"
        ))
        
        return strategies
    
    def _generate_weak_bear_strategies(
        self, analysis_data: Dict, current_price: float, capital: float, confidence: float
    ) -> List[TradingStrategy]:
        """Generate strategies for weak bear market"""
        strategies = []
        
        # Strategy 1: Short with hedge
        strategies.append(TradingStrategy(
            name="Short with Hedge",
            description="Short position with limited long hedge",
            direction="short_hedge",
            entry_price=current_price,
            stop_loss=current_price * 1.04,
            take_profit_1=current_price * 0.92,
            take_profit_2=current_price * 0.85,
            position_size=0.0,
            leverage=1.0,
            confidence=confidence * 0.75,
            risk_reward_ratio=2.0,
            strategy_type="short_hedge"
        ))
        
        # Strategy 2: Wait for Clarity
        strategies.append(TradingStrategy(
            name="Wait for Bear Confirmation",
            description="Wait for stronger bearish signals",
            direction="wait",
            entry_price=0.0,
            stop_loss=0.0,
            take_profit_1=0.0,
            take_profit_2=None,
            position_size=0.0,
            leverage=0.0,
            confidence=0.8,
            risk_reward_ratio=0.0,
            strategy_type="wait"
        ))
        
        return strategies
    
    def _generate_bear_strategies(
        self, analysis_data: Dict, current_price: float, capital: float, confidence: float
    ) -> List[TradingStrategy]:
        """Generate strategies for strong bear market"""
        strategies = []
        
        # Strategy 1: Directional Short
        template = self.strategy_templates.get("directional_short", {})
        stop_loss_pct = template.get("stop_loss_pct", 0.06)
        tp1_pct, tp2_pct = template.get("take_profit_levels", [0.08, 0.15])
        
        strategies.append(TradingStrategy(
            name="Directional Short",
            description="Pure short position capitalizing on bear momentum",
            direction="short",
            entry_price=current_price,
            stop_loss=current_price * (1 + stop_loss_pct),
            take_profit_1=current_price * (1 - tp1_pct),
            take_profit_2=current_price * (1 - tp2_pct),
            position_size=0.0,
            leverage=1.0,
            confidence=confidence * 0.85,
            risk_reward_ratio=tp1_pct / stop_loss_pct,
            strategy_type="directional_short"
        ))
        
        # Strategy 2: Bear Spread
        strategies.append(TradingStrategy(
            name="Bear Put Spread",
            description="Limited risk bear strategy",
            direction="short",
            entry_price=current_price * 1.01,  # Enter on bounce
            stop_loss=current_price * 1.05,
            take_profit_1=current_price * 0.90,
            take_profit_2=current_price * 0.82,
            position_size=0.0,
            leverage=1.2,
            confidence=confidence * 0.8,
            risk_reward_ratio=2.5,
            strategy_type="bear_spread"
        ))
        
        return strategies
    
    def _generate_volatility_strategies(
        self, analysis_data: Dict, current_price: float, capital: float, confidence: float
    ) -> List[TradingStrategy]:
        """Generate strategies for high volatility market"""
        strategies = []
        
        # Strategy 1: Straddle Strategy
        strategies.append(TradingStrategy(
            name="Volatility Straddle",
            description="Profit from large moves in either direction",
            direction="straddle",
            entry_price=current_price,
            stop_loss=current_price * 0.95,  # Tight stop for volatility
            take_profit_1=current_price * 1.15,
            take_profit_2=current_price * 0.85,  # Profit in either direction
            position_size=0.0,
            leverage=1.0,
            confidence=confidence * 0.8,
            risk_reward_ratio=3.0,
            strategy_type="straddle"
        ))
        
        # Strategy 2: Wait Strategy
        strategies.append(TradingStrategy(
            name="Wait for Clarity",
            description="Avoid trading in extreme volatility",
            direction="wait",
            entry_price=0.0,
            stop_loss=0.0,
            take_profit_1=0.0,
            take_profit_2=None,
            position_size=0.0,
            leverage=0.0,
            confidence=0.95,
            risk_reward_ratio=0.0,
            strategy_type="wait"
        ))
        
        # Strategy 3: Volatility Breakout
        strategies.append(TradingStrategy(
            name="Volatility Breakout",
            description="Trade breakouts from volatility compression",
            direction="breakout",
            entry_price=current_price * 1.03,  # 3% breakout level
            stop_loss=current_price * 0.98,
            take_profit_1=current_price * 1.12,
            take_profit_2=current_price * 1.20,
            position_size=0.0,
            leverage=1.5,
            confidence=confidence * 0.7,
            risk_reward_ratio=2.4,
            strategy_type="volatility_breakout"
        ))
        
        return strategies