"""
Market Data Schema for AFC3 Data Infrastructure.

Standardized market data structure for all connectors.

Author: AFC3 Data Infrastructure
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import uuid


@dataclass
class MarketData:
    """
    Standardized market data structure.
    
    Fields:
    - timestamp: Data timestamp
    - asset_symbol: Asset identifier (e.g., SPY, BTC)
    - price: Current price
    - volume: Trading volume
    - bid: Bid price
    - ask: Ask price
    - open: Open price
    - high: High price
    - low: Low price
    - close: Close price
    - data_source: Source of data
    """
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    asset_symbol: str = ""
    price: float = 0.0
    volume: float = 0.0
    bid: Optional[float] = None
    ask: Optional[float] = None
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    close: Optional[float] = None
    data_source: str = "unknown"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "asset_symbol": self.asset_symbol,
            "price": self.price,
            "volume": self.volume,
            "bid": self.bid,
            "ask": self.ask,
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "data_source": self.data_source
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MarketData':
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class OHLCVData:
    """
    OHLCV (Open, High, Low, Close, Volume) bar data.
    
    Fields:
    - timestamp: Bar timestamp
    - asset_symbol: Asset identifier
    - open: Open price
    - high: High price
    - low: Low price
    - close: Close price
    - volume: Volume
    - interval: Bar interval (1m, 5m, 1h, 1d)
    """
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    asset_symbol: str = ""
    open: float = 0.0
    high: float = 0.0
    low: float = 0.0
    close: float = 0.0
    volume: float = 0.0
    interval: str = "1d"  # 1m, 5m, 15m, 1h, 4h, 1d
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "asset_symbol": self.asset_symbol,
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volume": self.volume,
            "interval": self.interval
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'OHLCVData':
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class FeatureData:
    """
    Computed feature data.
    
    Fields:
    - timestamp: Feature timestamp
    - asset_symbol: Asset identifier
    - feature_name: Feature name
    - value: Feature value
    - parameters: Feature parameters
    """
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    asset_symbol: str = ""
    feature_name: str = ""
    value: float = 0.0
    parameters: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "asset_symbol": self.asset_symbol,
            "feature_name": self.feature_name,
            "value": self.value,
            "parameters": self.parameters
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FeatureData':
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


# Asset types
ASSET_TYPES = {
    "equities": ["SPY", "QQQ", "IWM", "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA"],
    "crypto": ["BTC", "ETH", "SOL", "XRP", "ADA"],
    "etfs": ["TNA", "TECL", "SOXL", "TQQQ", "SPXL"],
    "forex": ["EURUSD", "GBPUSD", "USDJPY"]
}

# Supported intervals
INTERVALS = ["1m", "5m", "15m", "30m", "1h", "4h", "1d", "1w"]
