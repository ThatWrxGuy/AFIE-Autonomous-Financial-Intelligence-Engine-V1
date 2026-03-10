"""
Data Service for AFC3 Data Infrastructure.

Unified interface for retrieving market data and features.

Author: AFC3 Data Infrastructure
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from data.ingestion.base_connector import create_connector, BaseDataConnector
from data.storage.market_data_store import get_market_data_store, get_feature_store
from data.features.feature_engine import get_feature_engine
from data.streaming.market_stream import get_market_stream


class DataService:
    """
    Unified data service interface.
    
    Provides access to market data, features, and streaming.
    """
    
    def __init__(self):
        # Connectors
        self._connectors: Dict[str, BaseDataConnector] = {}
        
        # Stores
        self.market_store = get_market_data_store()
        self.feature_store = get_feature_store()
        
        # Feature engine
        self.feature_engine = get_feature_engine()
        
        # Stream
        self.stream = get_market_stream()
    
    def get_connector(self, asset_type: str) -> BaseDataConnector:
        """Get or create connector for asset type."""
        if asset_type not in self._connectors:
            self._connectors[asset_type] = create_connector(asset_type)
        return self._connectors[asset_type]
    
    async def get_historical_data(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        interval: str = "1d",
        asset_type: str = "equities"
    ) -> List[Dict[str, Any]]:
        """Get historical OHLCV data."""
        # Try to get from store first
        stored = self.market_store.get_ohlcv(symbol, interval, start_date, end_date)
        
        if stored:
            return stored
        
        # Fetch from connector
        connector = self.get_connector(asset_type)
        bars = await connector.fetch_historical(symbol, start_date, end_date, interval)
        
        # Store in market data store
        self.market_store.store_ohlcv(bars)
        
        return [bar.to_dict() for bar in bars]
    
    async def get_latest_price(
        self,
        symbol: str,
        asset_type: str = "equities"
    ) -> Optional[Dict[str, Any]]:
        """Get latest price for symbol."""
        # Try store first
        latest = self.market_store.get_latest(symbol)
        
        if latest:
            return latest
        
        # Fetch from connector
        connector = self.get_connector(asset_type)
        quote = await connector.fetch_latest(symbol)
        
        # Store and return
        self.market_store.store_quote(quote)
        
        return quote.to_dict()
    
    async def get_feature_set(
        self,
        symbol: str,
        feature_names: List[str],
        period: int = 100,
        asset_type: str = "equities"
    ) -> Dict[str, Any]:
        """Get computed features for symbol."""
        # Try feature store first
        cached = self.feature_store.get_features(symbol)
        
        if cached:
            return {"cached": True, "features": cached}
        
        # Get historical data
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=period)
        
        bars = await self.get_historical_data(
            symbol,
            start_date.isoformat(),
            end_date.isoformat(),
            "1d",
            asset_type
        )
        
        if not bars:
            return {"error": "No data available"}
        
        # Convert to OHLCV objects
        from data.schemas.market_data import OHLCVData
        ohlcv_bars = [OHLCVData.from_dict(b) for b in bars]
        
        # Compute features
        features = self.feature_engine.compute_features_for_bars(ohlcv_bars, feature_names)
        
        # Store in feature store
        feature_dicts = [f.to_dict() for f in features]
        self.feature_store.store_feature(symbol, ",".join(feature_names), feature_dicts)
        
        return {"cached": False, "features": feature_dicts}
    
    def get_available_symbols(self, asset_type: str = "equities") -> List[str]:
        """Get available symbols for asset type."""
        connector = self.get_connector(asset_type)
        
        if hasattr(connector, "supported_symbols"):
            return connector.supported_symbols
        
        return self.market_store.get_symbols()
    
    def get_market_snapshot(self) -> Dict[str, Any]:
        """Get current market snapshot."""
        return {
            "latest_prices": self.market_store.get_all_latest(),
            "symbols": self.market_store.get_symbols(),
            "stats": self.market_store.get_stats()
        }
    
    def get_feature_stats(self) -> Dict[str, Any]:
        """Get feature store statistics."""
        return self.feature_store.get_stats()
    
    def get_stream_status(self) -> Dict[str, Any]:
        """Get streaming status."""
        return self.stream.get_status()


# Global data service
_data_service = None


def get_data_service() -> DataService:
    """Get global data service."""
    global _data_service
    if _data_service is None:
        _data_service = DataService()
    return _data_service


# Convenience functions
async def get_historical_data(symbol: str, start_date: str, end_date: str, 
                            interval: str = "1d") -> List[Dict[str, Any]]:
    """Get historical data."""
    service = get_data_service()
    return await service.get_historical_data(symbol, start_date, end_date, interval)


async def get_latest_price(symbol: str) -> Optional[Dict[str, Any]]:
    """Get latest price."""
    service = get_data_service()
    return await service.get_latest_price(symbol)


async def get_feature_set(symbol: str, feature_names: List[str],
                         period: int = 100) -> Dict[str, Any]:
    """Get feature set."""
    service = get_data_service()
    return await service.get_feature_set(symbol, feature_names, period)
