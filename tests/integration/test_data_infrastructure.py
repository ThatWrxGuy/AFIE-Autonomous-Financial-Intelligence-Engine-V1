"""Tests for Data Infrastructure"""
import pytest
import asyncio
import sys
sys.path.insert(0, '.')

from data.schemas.market_data import MarketData, OHLCVData
from data.ingestion.base_connector import EquitiesConnector, CryptoConnector
from data.storage.market_data_store import MarketDataStore, FeatureStore
from data.features.feature_engine import FeatureEngine
from data.data_service import DataService

class TestMarketDataSchema:
    def test_market_data_to_dict(self):
        md = MarketData(asset_symbol="SPY", price=100.0)
        d = md.to_dict()
        assert d["asset_symbol"] == "SPY"
        assert d["price"] == 100.0
    
    def test_ohlcv_to_dict(self):
        bar = OHLCVData(asset_symbol="SPY", close=100.0, open=99.0, high=101.0, low=98.0, volume=1000)
        d = bar.to_dict()
        assert d["asset_symbol"] == "SPY"
        assert d["close"] == 100.0

class TestDataConnectors:
    @pytest.mark.asyncio
    async def test_equities_connector(self):
        conn = EquitiesConnector()
        bars = await conn.fetch_historical("SPY", "2024-01-01", "2024-01-10", "1d")
        assert len(bars) > 0
        assert bars[0].asset_symbol == "SPY"
    
    @pytest.mark.asyncio
    async def test_crypto_connector(self):
        conn = CryptoConnector()
        quote = await conn.fetch_latest("BTC")
        assert quote.asset_symbol == "BTC"
        assert quote.price > 0

class TestDataStore:
    def test_market_data_store(self):
        store = MarketDataStore()
        bar = OHLCVData(asset_symbol="SPY", close=100.0, volume=1000, interval="1d")
        store.store_ohlcv([bar])
        
        result = store.get_ohlcv("SPY", "1d")
        assert len(result) == 1
        assert result[0]["close"] == 100.0
    
    def test_feature_store(self):
        store = FeatureStore()
        store.store_feature("SPY", "sma", [{"value": 100.0}])
        
        result = store.get_features("SPY", "sma")
        assert len(result) > 0

class TestFeatureEngine:
    def test_compute_sma(self):
        engine = FeatureEngine()
        prices = [100, 102, 101, 103, 104, 105, 106, 107, 108, 109,
                  110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120]
        sma = engine.compute_sma(prices, 20)
        assert sma is not None
        assert sma > 0
    
    def test_compute_rsi(self):
        engine = FeatureEngine()
        prices = [100 + i for i in range(30)]
        rsi = engine.compute_rsi(prices, 14)
        assert rsi is not None
        assert 0 <= rsi <= 100
    
    def test_compute_zscore(self):
        engine = FeatureEngine()
        prices = [100] * 30
        zscore = engine.compute_zscore(prices, 20)
        assert zscore is not None

class TestDataService:
    @pytest.mark.asyncio
    async def test_get_historical(self):
        service = DataService()
        bars = await service.get_historical_data("SPY", "2024-01-01", "2024-02-01", "1d")
        assert len(bars) > 0
    
    @pytest.mark.asyncio
    async def test_get_latest(self):
        service = DataService()
        price = await service.get_latest_price("AAPL")
        assert price is not None
        assert price["price"] > 0
    
    @pytest.mark.asyncio
    async def test_get_features(self):
        service = DataService()
        features = await service.get_feature_set("SPY", ["sma", "zscore"], period=100)
        assert "features" in features

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
