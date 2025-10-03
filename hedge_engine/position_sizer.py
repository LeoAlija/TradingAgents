"""
Position Sizer for TradingAgents Hedge Engine
Calculates optimal position sizes based on risk management rules
"""

import numpy as np
from typing import Dict
from strategy_generator import TradingStrategy

class PositionSizer:
    """
    Calculates position sizes using various methodologies
    """
    
    def __init__(self, config: Dict):
        self.config = config
        self.risk_params = config.get("risk_management", {})
        self.max_risk_per_trade = self.risk_params.get("max_risk_per_trade", 0.02)
        self.max_portfolio_risk = self.risk_params.get("max_portfolio_risk", 0.15)
        self.position_size_method = self.risk_params.get("position_size_method", "fixed_risk")
    
    def calculate_position_size(
        self,
        strategy: TradingStrategy,
        capital: float,
        current_price: float
    ) -> float:
        """
        Calculate position size based on risk management rules
        """
        if strategy.direction == "wait":
            return 0.0
        
        # Calculate risk per trade
        entry_price = strategy.entry_price or current_price
        stop_loss = strategy.stop_loss
        
        if stop_loss == 0 or entry_price == 0:
            return 0.0
        
        # Calculate risk per unit based on direction
        if strategy.direction in ["long", "hedge"]:
            risk_per_unit = abs(entry_price - stop_loss)
        elif strategy.direction == "short":
            risk_per_unit = abs(stop_loss - entry_price)
        else:  # straddle or other complex strategies
            risk_per_unit = abs(entry_price - stop_loss)
        
        if risk_per_unit <= 0:
            return 0.0
        
        # Calculate maximum position based on risk
        max_risk_amount = capital * self.max_risk_per_trade
        max_position_value = max_risk_amount / (risk_per_unit / entry_price)
        
        # Convert to position size (units/coins)
        position_size = max_position_value / entry_price
        
        # Apply confidence factor (reduce size for lower confidence)
        position_size *= strategy.confidence
        
        # Apply leverage adjustment
        if strategy.leverage > 1.0:
            position_size *= strategy.leverage
        
        # Round to reasonable precision
        return round(position_size, 6)
    
    def calculate_kelly_criterion(
        self,
        win_rate: float,
        avg_win: float,
        avg_loss: float
    ) -> float:
        """
        Calculate Kelly Criterion for position sizing
        """
        if avg_loss == 0 or win_rate <= 0 or win_rate >= 1:
            return 0.0
        
        b = avg_win / avg_loss  # Win/loss ratio
        p = win_rate  # Probability of win
        q = 1 - p  # Probability of loss
        
        kelly_fraction = (b * p - q) / b
        
        # Cap Kelly at 25% for safety and ensure non-negative
        return min(max(kelly_fraction, 0), 0.25)
    
    def validate_position_size(
        self,
        position_size: float,
        entry_price: float,
        capital: float
    ) -> float:
        """
        Validate and adjust position size based on capital constraints
        """
        if position_size <= 0 or entry_price <= 0:
            return 0.0
            
        position_value = position_size * entry_price
        
        # Ensure position doesn't exceed available capital
        max_position_value = capital * 0.8  # Keep 20% cash buffer
        
        if position_value > max_position_value:
            position_size = max_position_value / entry_price
        
        # Minimum position size check (avoid dust trades)
        min_position_value = 100  # Minimum $100 position
        if position_value < min_position_value:
            return 0.0
        
        return round(position_size, 6)
    
    def calculate_position_metrics(
        self,
        strategy: TradingStrategy,
        capital: float
    ) -> Dict[str, float]:
        """
        Calculate comprehensive position metrics
        """
        if strategy.position_size <= 0:
            return {
                "position_value": 0.0,
                "risk_amount": 0.0,
                "risk_percentage": 0.0,
                "potential_profit_1": 0.0,
                "potential_profit_2": 0.0,
                "capital_allocation": 0.0
            }
        
        position_value = strategy.position_size * strategy.entry_price
        
        # Calculate risk amount
        if strategy.direction in ["long", "hedge"]:
            risk_per_unit = abs(strategy.entry_price - strategy.stop_loss)
        else:  # short
            risk_per_unit = abs(strategy.stop_loss - strategy.entry_price)
        
        risk_amount = risk_per_unit * strategy.position_size
        risk_percentage = (risk_amount / capital) * 100
        
        # Calculate potential profits
        if strategy.direction in ["long", "hedge"]:
            potential_profit_1 = (strategy.take_profit_1 - strategy.entry_price) * strategy.position_size
            potential_profit_2 = (strategy.take_profit_2 - strategy.entry_price) * strategy.position_size if strategy.take_profit_2 else 0
        else:  # short
            potential_profit_1 = (strategy.entry_price - strategy.take_profit_1) * strategy.position_size
            potential_profit_2 = (strategy.entry_price - strategy.take_profit_2) * strategy.position_size if strategy.take_profit_2 else 0
        
        return {
            "position_value": position_value,
            "risk_amount": risk_amount,
            "risk_percentage": risk_percentage,
            "potential_profit_1": potential_profit_1,
            "potential_profit_2": potential_profit_2,
            "capital_allocation": (position_value / capital) * 100,
            "risk_reward_1": potential_profit_1 / risk_amount if risk_amount > 0 else 0,
            "risk_reward_2": potential_profit_2 / risk_amount if risk_amount > 0 and potential_profit_2 > 0 else 0
        }
    
    def apply_portfolio_risk_limits(
        self,
        strategies: list,
        capital: float
    ) -> list:
        """
        Apply portfolio-level risk limits across multiple strategies
        """
        total_risk = 0.0
        adjusted_strategies = []
        
        for strategy in strategies:
            if strategy.direction == "wait" or strategy.position_size <= 0:
                adjusted_strategies.append(strategy)
                continue
            
            # Calculate risk for this strategy
            metrics = self.calculate_position_metrics(strategy, capital)
            strategy_risk = metrics["risk_amount"]
            
            # Check if adding this strategy exceeds portfolio risk limit
            if (total_risk + strategy_risk) / capital > self.max_portfolio_risk:
                # Scale down position size to fit within limits
                available_risk = (capital * self.max_portfolio_risk) - total_risk
                if available_risk > 0:
                    scale_factor = available_risk / strategy_risk
                    strategy.position_size *= scale_factor
                    strategy.position_size = round(strategy.position_size, 6)
                    total_risk += available_risk
                else:
                    # Skip this strategy if no risk budget available
                    strategy.position_size = 0.0
            else:
                total_risk += strategy_risk
            
            adjusted_strategies.append(strategy)
        
        return adjusted_strategies