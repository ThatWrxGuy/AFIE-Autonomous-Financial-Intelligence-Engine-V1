"""
Base Data Connector for AFC3 Data Infrastructure.

Abstract base class for all data connectors.

Author: AFC3 Data Infrastructure
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import random
from datetime import datetime, timedelta

from data.schemas.market_data import MarketData, OHLCVData


class BaseDataConnector(ABC):
    """Abstract base class for data connectors."""
    
    def __init__(self, name: str, asset_type: str):
        self.name = name
        self.asset_type = asset_type
        self.connected = False
    
    @abstractmethod
    async def fetch_historical(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        interval: str = "1d"
    ) -> List[OHLCVData]:
        """Fetch historical OHLCV data."""
        pass
    
    @abstractmethod
    async def fetch_latest(self, symbol: str) -> MarketData:
        """Fetch latest market data."""
        pass
    
    async def connect(self) -> bool:
        """Establish connection."""
        self.connected = True
        return True
    
    async def disconnect(self) -> None:
        """Close connection."""
        self.connected = False
    
    def is_connected(self) -> bool:
        """Check if connected."""
        return self.connected


class SimulatedDataConnector(BaseDataConnector):
    """Simulated data connector for testing without API keys."""
    
    def __init__(self, name: str, asset_type: str):
        super().__init__(name, asset_type)
        # Base prices for simulation
        self.base_prices = {
            # Equities
            "SPY": 450.0, "QQQ": 380.0, "IWM": 200.0,
            "AAPL": 175.0, "MSFT": 380.0, "GOOGL": 140.0,
            "AMZN": 180.0, "NVDA": 480.0,
            # Crypto
            "BTC": 45000.0, "ETH": 2500.0, "SOL": 100.0,
            "XRP": 0.55, "ADA": 0.45,
            # ETFs
            "TNA": 45.0, "TECL": 40.0, "SOXL": 35.0,
            "TQQQ": 55.0, "SPXL": 55.0
        }
    
    def _generate_price(self, symbol: str) -> float:
        """Generate realistic price."""
        base = self.base_prices.get(symbol, 100.0)
        # Add some randomness
        return base * random.uniform(0.95, 1.05)
    
    async def fetch_historical(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        interval: str = "1d"
    ) -> List[OHLCVData]:
        """Generate simulated historical data."""
        # Parse dates
        start = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
        end = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
        
        # Determine number of bars
        if interval == "1d":
            num_bars = (end - start).days
        elif interval == "1h":
            num_bars = int((end - start).total_seconds() / 3600)
        else:
            num_bars = 100  # Default
        
        num_bars = min(num_bars, 500)  # Cap at 500 bars
        
        bars = []
        current_price = self._generate_price(symbol)
        
        for i in range(num_bars):
            # Generate OHLCV
            bar = OHLCVData(
                timestamp=(start + timedelta(days=i) if interval == "1d" else start + timedelta(hours=i)).isoformat(),
                asset_symbol=symbol,
                open=current_price,
                high=current_price * random.uniform(1.0, 1.02),
                low=current_price * random.uniform(0.98, 1.0),
                close=current_price * random.uniform(0.98, 1.02),
                volume=random.uniform(1000000, 10000000),
                interval=interval
            )
            bars.append(bar)
            
            # Update price for next bar
            current_price = bar.close
        
        return bars
    
    async def fetch_latest(self, symbol: str) -> MarketData:
        """Generate simulated latest data."""
        price = self._generate_price(symbol)
        
        return MarketData(
            timestamp=datetime.utcnow().isoformat(),
            asset_symbol=symbol,
            price=price,
            volume=random.uniform(1000000, 5000000),
            bid=price * 0.999,
            ask=price * 1.001,
            open=price * random.uniform(0.98, 1.0),
            high=price * random.uniform(1.0, 1.02),
            low=price * random.uniform(0.98, 1.0),
            close=price,
            data_source=self.name
        )


class EquitiesConnector(SimulatedDataConnector):
    """Connector for equity market data."""
    
    def __init__(self):
        super().__init__("EquitiesConnector", "equities")
        self.supported_symbols = [
            "SPY", "QQQ", "IWM", "AAPL", "MSFT", 
            "GOOGL", "AMZN", "NVDA", "META", "TSLA"
        ]
    
    async def fetch_historical(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        interval: str = "1d"
    ) -> List[OHLCVData]:
        """Fetch equity historical data."""
        return await super().fetch_historical(symbol, start_date, end_date, interval)
    
    async def fetch_latest(self, symbol: str) -> MarketData:
        """Fetch latest equity data."""
        return await super().fetch_latest(symbol)


class CryptoConnector(SimulatedDataConnector):
    """Connector for cryptocurrency market data."""
    
    def __init__(self):
        super().__init__("CryptoConnector", "crypto")
        self.supported_symbols = ["BTC", "ETH", "SOL", "XRP", "ADA", "DOGE", "AVAX"]
    
    async def fetch_historical(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        interval: str = "1h"
    ) -> List[OHLCVData]:
        """Fetch crypto historical data."""
        return await super().fetch_historical(symbol, start_date, end_date, interval)
    
    async def fetch_latest(self, symbol: str) -> MarketData:
        """Fetch latest crypto data."""
        return await super().fetch_latest(symbol)


class MacroConnector(BaseDataConnector):
    """Connector for macro economic indicators."""
    
    def __init__(self):
        super().__init__("MacroConnector", "macro")
        self.indicators = ["SPX", "VIX", "DXY", "TNX", "Gold"]
    
    async def fetch_historical(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        interval: str = "1d"
    ) -> List[OHLCVData]:
        """Fetch macro indicator data."""
        # Generate simulated macro data
        bars = []
        base_values = {"SPX": 4500.0, "VIX": 18.0, "DXY": 103.0, "TNX": 4.5, "Gold": 2000.0}
        base = base_values.get(symbol, 1000.0)
        
        start = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
        
        for i in range(30):
            price = base * random.uniform(0.98, 1.02)
            bars.append(OHLCVData(
                timestamp=(start + timedelta(days=i)).isoformat(),
                asset_symbol=symbol,
                open=price,
                high=price * 1.01,
                low=price * 0.99,
                close=price,
                volume=random.uniform(10000, 100000),
                interval=interval
            ))
        
        return bars
    
    async def fetch_latest(self, symbol: str) -> MarketData:
        """Fetch latest macro indicator."""
        base_values = {"SPX": 4500.0, "VIX": 18.0, "DXY": 103.0, "TNX": 4.5, "Gold": 2000.0}
        base = base_values.get(symbol, 1000.0)
        price = base * random.uniform(0.98, 1.02)
        
        return MarketData(
            timestamp=datetime.utcnow().isoformat(),
            asset_symbol=symbol,
            price=price,
            volume=random.uniform(10000, 100000),
            data_source=self.name
        )


def create_connector(asset_type: str) -> BaseDataConnector:
    """Factory function to create data connectors."""
    if asset_type == "equities":
        return EquitiesConnector()
    elif asset_type == "crypto":
        return CryptoConnector()
    elif asset_type == "macro":
        return MacroConnector()
    else:
        return SimulatedDataConnector(f"{asset_type}Connector", asset_type)
