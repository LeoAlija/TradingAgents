"""
Market Regime Detector for TradingAgents Hedge Engine
Identifies market conditions to inform trading strategies
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple, List
from dataclasses import dataclass
from enum import Enum

class MarketRegime(Enum):
    STRONG_BULL = "strong_bull"
    WEAK_BULL = "weak_bull"
    SIDEWAYS = "sideways"
    WEAK_BEAR = "weak_bear"
    STRONG_BEAR = "strong_bear"
    HIGH_VOLATILITY = "high_volatility"

@dataclass
class RegimeMetrics:
    trend_strength: float
    volatility: float
    momentum: float
    volume_trend: float
    regime: MarketRegime
    confidence: float

class MarketRegimeDetector:
    """
    Detects market regimes using multiple technical indicators
    """

    def __init__(self, config: Dict):
        self.config = config
        self.regime_criteria = config.get("market_regimes", {})

    def calculate_trend_strength(self, prices: pd.Series, period: int = 20) -> float:
        """
        Calculate trend strength using ADX-like methodology
        Returns value between -1 (strong bear) to 1 (strong bull)
        """
        if len(prices) < period:
            return 0.0

        # Simple trend strength calculation
        sma_short = prices.rolling(period//2).mean()
        sma_long = prices.rolling(period).mean()

        # Normalize trend strength
        trend_direction = np.where(sma_short > sma_long, 1, -1)
        price_position = (prices - sma_long) / sma_long

        # Combine direction with strength
        trend_strength = trend_direction * np.abs(price_position)
        return np.clip(trend_strength.iloc[-1] if not pd.isna(trend_strength.iloc[-1]) else 0.0, -1, 1)

    def calculate_volatility(self, prices: pd.Series, period: int = 20) -> float:
        """
        Calculate normalized volatility
        """
        if len(prices) < period:
            return 0.3

        returns = prices.pct_change().dropna()
        if len(returns) < period:
            return 0.3

        volatility = returns.rolling(period).std() * np.sqrt(252)  # Annualized

        # Normalize to 0-1 scale (0.6+ is high volatility for crypto)
        normalized_vol = np.clip(volatility.iloc[-1] / 0.8 if not pd.isna(volatility.iloc[-1]) else 0.3, 0, 1)
        return normalized_vol

    def calculate_momentum(self, prices: pd.Series, period: int = 14) -> float:
        """
        Calculate price momentum using RSI-like calculation
        Returns value between -1 (oversold) to 1 (overbought)
        """
        if len(prices) < period:
            return 0.0

        delta = prices.diff()
        gain = delta.where(delta > 0, 0).rolling(period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(period).mean()

        # Avoid division by zero
        rs = gain / loss.replace(0, 0.001)
        rsi = 100 - (100 / (1 + rs))

        # Convert RSI to momentum (-1 to 1)
        momentum = (rsi.iloc[-1] - 50) / 50 if not pd.isna(rsi.iloc[-1]) else 0.0
        return np.clip(momentum, -1, 1)

    def detect_regime(self, analysis_data: Dict) -> RegimeMetrics:
        """
        Main method to detect market regime from TradingAgents analysis
        """
        # Extract price data from analysis
        current_price = self._extract_current_price(analysis_data)
        price_data = self._extract_price_series(analysis_data, current_price)

        # Calculate regime metrics
        trend_strength = self.calculate_trend_strength(price_data)
        volatility = self.calculate_volatility(price_data)
        momentum = self.calculate_momentum(price_data)

        # Determine regime based on criteria
        regime, confidence = self._classify_regime(trend_strength, volatility, momentum)

        return RegimeMetrics(
            trend_strength=trend_strength,
            volatility=volatility,
            momentum=momentum,
            volume_trend=0.0,  # To be implemented
            regime=regime,
            confidence=confidence
        )

    def _extract_current_price(self, analysis_data: Dict) -> float:
        """Extract current price from TradingAgents analysis"""
        # Try multiple possible locations
        technical_data = analysis_data.get("technical_analysis", {})
        if "current_price" in technical_data:
            return float(technical_data["current_price"])

        # Check if there's price data in the analysis
        if "price_data" in technical_data:
            price_series = technical_data["price_data"]
            if isinstance(price_series, (list, pd.Series)) and len(price_series) > 0:
                return float(price_series[-1])

        # Fallback to a reasonable default for demo
        return 64350.0

    def _extract_price_series(self, analysis_data: Dict, current_price: float) -> pd.Series:
        """Extract or create price series for analysis"""
        technical_data = analysis_data.get("technical_analysis", {})

        if "price_data" in technical_data:
            price_data = technical_data["price_data"]
            if isinstance(price_data, pd.Series):
                return price_data
            elif isinstance(price_data, list):
                return pd.Series(price_data)

        # Create mock price series for demo purposes
        # In production, this would extract real price history
        np.random.seed(42)  # For consistent demo results
        price_changes = np.random.normal(0, 0.02, 50)  # 50 days of 2% daily volatility
        prices = [current_price * 0.95]  # Start 5% below current

        for change in price_changes:
            prices.append(prices[-1] * (1 + change))

        return pd.Series(prices)

    def _classify_regime(self, trend: float, vol: float, momentum: float) -> Tuple[MarketRegime, float]:
        """
        Classify regime based on calculated metrics
        """
        # Strong Bull: Strong uptrend, low volatility, positive momentum
        if trend > 0.7 and vol < 0.3 and momentum > 0.6:
            return MarketRegime.STRONG_BULL, 0.9

        # Weak Bull: Moderate uptrend, moderate volatility
        elif 0.3 < trend <= 0.7 and vol < 0.5 and 0.2 < momentum <= 0.6:
            return MarketRegime.WEAK_BULL, 0.7

        # Strong Bear: Strong downtrend, high momentum down
        elif trend < -0.7 and momentum < -0.6:
            return MarketRegime.STRONG_BEAR, 0.85

        # Weak Bear: Moderate downtrend
        elif -0.7 <= trend < -0.3 and -0.6 <= momentum < -0.2:
            return MarketRegime.WEAK_BEAR, 0.7

        # High Volatility: Very high volatility regardless of trend
        elif vol > 0.6:
            return MarketRegime.HIGH_VOLATILITY, 0.8

        # Sideways: Low trend strength, low volatility
        else:
            return MarketRegime.SIDEWAYS, 0.6
