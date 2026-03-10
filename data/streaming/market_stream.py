"""
Market Data Streaming for AFC3 Data Infrastructure.

Real-time streaming interface for market updates.

Author: AFC3 Data Infrastructure
"""

from typing import Dict, Any, List, Callable, Set
from dataclasses import dataclass
from datetime import datetime
import asyncio
import random

from data.schemas.market_data import MarketData
from core.event_bus import get_event_bus


@dataclass
class PriceUpdate:
    """Price update event."""
    symbol: str
    price: float
    volume: float
    timestamp: str


class MarketStream:
    """
    Market data streaming service.
    Broadcasts price updates to subscribers.
    """
    
    def __init__(self):
        self._subscribers: Dict[str, Set[Callable]] = {}
        self._running = False
        self._symbols: List[str] = []
        self.event_bus = get_event_bus()
    
    def subscribe(self, symbol: str, callback: Callable) -> None:
        if symbol not in self._subscribers:
            self._subscribers[symbol] = set()
        self._subscribers[symbol].add(callback)
    
    def unsubscribe(self, symbol: str, callback: Callable) -> None:
        if symbol in self._subscribers:
            self._subscribers[symbol].discard(callback)
    
    async def start_streaming(self, symbols: List[str], interval: float = 1.0) -> None:
        self._symbols = symbols
        self._running = True
        
        base_prices = {"SPY": 450.0, "QQQ": 380.0, "BTC": 45000.0, "ETH": 2500.0}
        current_prices = {s: base_prices.get(s, 100.0) for s in symbols}
        
        while self._running:
            for symbol in self._symbols:
                change = random.uniform(-0.005, 0.005)
                current_prices[symbol] *= (1 + change)
                
                update = PriceUpdate(symbol=symbol, price=current_prices[symbol],
                                   volume=random.uniform(1000, 10000),
                                   timestamp=datetime.utcnow().isoformat())
                
                if symbol in self._subscribers:
                    for callback in self._subscribers[symbol]:
                        try:
                            if asyncio.iscoroutinefunction(callback):
                                await callback(update)
                            else:
                                callback(update)
                        except Exception as e:
                            print(f"Error in subscriber: {e}")
                
                if self.event_bus:
                    from core.event_bus import Event
                    event = Event(event_type="market.price_update", source="market_stream",
                                payload=update.__dict__)
                    await self.event_bus.publish(event)
            
            await asyncio.sleep(interval)
    
    def stop_streaming(self) -> None:
        self._running = False
    
    def get_status(self) -> Dict[str, Any]:
        return {"running": self._running, "symbols": self._symbols,
                "subscribers": {s: len(cbs) for s, cbs in self._subscribers.items()}}


_market_stream = None

def get_market_stream() -> MarketStream:
    global _market_stream
    if _market_stream is None:
        _market_stream = MarketStream()
    return _market_stream
