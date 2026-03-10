"""
Market Data Store for AFC3 Data Infrastructure.

In-memory storage for historical market data.

Author: AFC3 Data Infrastructure
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import json
import uuid

from data.schemas.market_data import OHLCVData, MarketData


class MarketDataStore:
    """
    In-memory store for historical market data.
    
    Stores OHLCV bars and tick data with fast retrieval.
    """
    
    def __init__(self):
        # Store OHLCV data: {symbol: {interval: [bars]}}
        self._ohlcv_data: Dict[str, Dict[str, List[OHLCVData]]] = {}
        
        # Store latest quotes: {symbol: MarketData}
        self._latest_quotes: Dict[str, MarketData] = {}
        
        # Metadata
        self._metadata: Dict[str, Any] = {}
    
    def store_ohlcv(self, bars: List[OHLCVData]) -> int:
        """Store OHLCV bars."""
        stored = 0
        
        for bar in bars:
            symbol = bar.asset_symbol
            interval = bar.interval
            
            if symbol not in self._ohlcv_data:
                self._ohlcv_data[symbol] = {}
            
            if interval not in self._ohlcv_data[symbol]:
                self._ohlcv_data[symbol][interval] = []
            
            self._ohlcv_data[symbol][interval].append(bar)
            stored += 1
        
        return stored
    
    def get_ohlcv(
        self,
        symbol: str,
        interval: str = "1d",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """Retrieve OHLCV data."""
        if symbol not in self._ohlcv_data:
            return []
        
        if interval not in self._ohlcv_data[symbol]:
            return []
        
        bars = self._ohlcv_data[symbol][interval]
        
        # Filter by date range
        if start_date or end_date:
            filtered = []
            for bar in bars:
                ts = bar.timestamp
                if start_date and ts < start_date:
                    continue
                if end_date and ts > end_date:
                    continue
                filtered.append(bar)
            bars = filtered
        
        # Apply limit
        return [bar.to_dict() for bar in bars[-limit:]]
    
    def store_quote(self, quote: MarketData) -> None:
        """Store latest quote."""
        self._latest_quotes[quote.asset_symbol] = quote
    
    def get_latest(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get latest quote for symbol."""
        if symbol in self._latest_quotes:
            return self._latest_quotes[symbol].to_dict()
        return None
    
    def get_all_latest(self) -> List[Dict[str, Any]]:
        """Get all latest quotes."""
        return [q.to_dict() for q in self._latest_quotes.values()]
    
    def get_symbols(self) -> List[str]:
        """Get all stored symbols."""
        return list(self._ohlcv_data.keys())
    
    def get_stats(self) -> Dict[str, Any]:
        """Get store statistics."""
        total_bars = sum(
            len(bars)
            for intervals in self._ohlcv_data.values()
            for bars in intervals.values()
        )
        
        return {
            "total_symbols": len(self._ohlcv_data),
            "total_bars": total_bars,
            "latest_quotes": len(self._latest_quotes)
        }
    
    def clear(self) -> None:
        """Clear all data."""
        self._ohlcv_data.clear()
        self._latest_quotes.clear()


class FeatureStore:
    """
    Store for computed features.
    
    Caches feature calculations for reuse.
    """
    
    def __init__(self):
        # Store features: {symbol: {feature_name: [values]}}
        self._features: Dict[str, Dict[str, List[Dict[str, Any]]]] = {}
        
        # Feature definitions
        self._definitions: Dict[str, Dict[str, Any]] = {}
    
    def store_feature(
        self,
        symbol: str,
        feature_name: str,
        values: List[Dict[str, Any]]
    ) -> int:
        """Store computed features."""
        if symbol not in self._features:
            self._features[symbol] = {}
        
        if feature_name not in self._features[symbol]:
            self._features[symbol][feature_name] = []
        
        self._features[symbol][feature_name].extend(values)
        return len(values)
    
    def get_features(
        self,
        symbol: str,
        feature_name: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get features for symbol."""
        if symbol not in self._features:
            return []
        
        if feature_name:
            if feature_name in self._features[symbol]:
                return self._features[symbol][feature_name][-limit:]
            return []
        
        # Return all features
        result = []
        for fname, values in self._features[symbol].items():
            result.extend(values[-limit:])
        return result
    
    def get_available_features(self, symbol: str) -> List[str]:
        """Get available features for symbol."""
        if symbol in self._features:
            return list(self._features[symbol].keys())
        return []
    
    def register_feature(
        self,
        name: str,
        description: str,
        parameters: Dict[str, Any]
    ) -> None:
        """Register a feature definition."""
        self._definitions[name] = {
            "name": name,
            "description": description,
            "parameters": parameters
        }
    
    def get_definitions(self) -> List[Dict[str, Any]]:
        """Get all feature definitions."""
        return list(self._definitions.values())
    
    def get_stats(self) -> Dict[str, Any]:
        """Get store statistics."""
        total_features = sum(
            len(values)
            for features in self._features.values()
            for values in features.values()
        )
        
        return {
            "total_symbols": len(self._features),
            "total_features": total_features,
            "feature_types": len(self._definitions)
        }
    
    def clear(self) -> None:
        """Clear all features."""
        self._features.clear()


# Global stores
_market_data_store = None
_feature_store = None


def get_market_data_store() -> MarketDataStore:
    """Get global market data store."""
    global _market_data_store
    if _market_data_store is None:
        _market_data_store = MarketDataStore()
    return _market_data_store


def get_feature_store() -> FeatureStore:
    """Get global feature store."""
    global _feature_store
    if _feature_store is None:
        _feature_store = FeatureStore()
    return _feature_store
