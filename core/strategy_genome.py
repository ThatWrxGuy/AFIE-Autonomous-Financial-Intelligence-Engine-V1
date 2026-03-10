"""
Strategy Genome Model for AFC3 Learning Engine.

This module defines the Strategy Genome abstraction for the learning engine.

Each strategy is represented as a genome containing:
- strategy_id
- strategy_family
- parameters
- feature_set
- risk_profile
- target_assets
- expected_return
- expected_volatility

Author: AFC3 Learning Engine
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import uuid
import random


@dataclass
class StrategyGenome:
    """
    Represents a strategy as a genome for evolution.
    
    Fields:
    - strategy_id: Unique identifier
    - strategy_family: Family (mean_reversion, momentum, etc.)
    - parameters: Mutable parameters
    - feature_set: Features used
    - risk_profile: Risk level (low, medium, high)
    - target_assets: Asset universe
    - expected_return: Predicted return
    - expected_volatility: Predicted volatility
    - generation: Evolution generation number
    - parent_id: Parent strategy ID
    - created_at: Creation timestamp
    """
    strategy_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    strategy_family: str = "momentum"  # momentum, mean_reversion, breakout, etc.
    parameters: Dict[str, Any] = field(default_factory=dict)
    feature_set: List[str] = field(default_factory=list)
    risk_profile: str = "medium"  # low, medium, high
    target_assets: List[str] = field(default_factory=list)
    expected_return: Optional[float] = None
    expected_volatility: Optional[float] = None
    generation: int = 0
    parent_id: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "strategy_id": self.strategy_id,
            "strategy_family": self.strategy_family,
            "parameters": self.parameters,
            "feature_set": self.feature_set,
            "risk_profile": self.risk_profile,
            "target_assets": self.target_assets,
            "expected_return": self.expected_return,
            "expected_volatility": self.expected_volatility,
            "generation": self.generation,
            "parent_id": self.parent_id,
            "created_at": self.created_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StrategyGenome':
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
    
    @classmethod
    def create_seed(cls, strategy_family: str = "momentum") -> 'StrategyGenome':
        """Create a seed genome with default parameters."""
        genome = cls(strategy_family=strategy_family)
        
        # Set default parameters based on family
        if strategy_family == "momentum":
            genome.parameters = {
                "lookback_period": 20,
                "entry_threshold": 2.0,
                "exit_threshold": 0.5,
                "stop_loss": 0.02,
                "take_profit": 0.05
            }
            genome.feature_set = ["returns", "volume", "volatility"]
            genome.target_assets = ["SPY", "QQQ", "IWM"]
        elif strategy_family == "mean_reversion":
            genome.parameters = {
                "lookback_period": 30,
                "entry_threshold": 2.5,
                "exit_threshold": 0.3,
                "stop_loss": 0.015,
                "bb_period": 20,
                "bb_std": 2.0
            }
            genome.feature_set = ["zscore", "bollinger_bands", "rsi"]
            genome.target_assets = ["SPY", "EFA", "EEM"]
        elif strategy_family == "breakout":
            genome.parameters = {
                "lookback_period": 50,
                "breakout_threshold": 0.03,
                "volume_confirmation": True,
                "atr_multiplier": 2.0
            }
            genome.feature_set = ["high", "low", "volume", "atr"]
            genome.target_assets = ["TNA", "TECL", "SOXL"]
        
        genome.risk_profile = "medium"
        return genome


# Strategy families
STRATEGY_FAMILIES = [
    "momentum",
    "mean_reversion",
    "breakout",
    "pairs_trading",
    "trend_following",
    "volatility_arbitrage"
]

# Available features
AVAILABLE_FEATURES = [
    "returns",
    "volume",
    "volatility",
    "zscore",
    "bollinger_bands",
    "rsi",
    "macd",
    "high",
    "low",
    "atr",
    "correlation",
    "beta"
]

# Risk profiles
RISK_PROFILES = ["low", "medium", "high"]
