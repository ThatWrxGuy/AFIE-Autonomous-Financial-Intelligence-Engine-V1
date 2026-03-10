"""
Broker Interface for AFC3 Broker Integration.

Abstract base class for broker adapters.

Author: AFC3 Broker Integration
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum


class OrderType(Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


class OrderSide(Enum):
    BUY = "buy"
    SELL = "sell"


class OrderStatus(Enum):
    PENDING = "pending"
    SUBMITTED = "submitted"
    FILLED = "filled"
    PARTIAL = "partial"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


@dataclass
class BrokerOrder:
    """Order structure for broker."""
    order_id: str
    symbol: str
    side: str
    quantity: float
    order_type: str
    limit_price: Optional[float] = None
    stop_price: Optional[float] = None
    status: str = "pending"
    filled_quantity: float = 0.0
    average_fill_price: float = 0.0


@dataclass
class Position:
    """Position structure."""
    symbol: str
    quantity: float
    average_price: float
    market_value: float
    unrealized_pnl: float


@dataclass
class AccountState:
    """Account state."""
    cash: float
    buying_power: float
    equity: float
    portfolio_value: float


class BrokerInterface(ABC):
    """Abstract broker interface."""
    
    def __init__(self, name: str, mode: str = "paper"):
        self.name = name
        self.mode = mode  # simulation, paper, live
        self.connected = False
    
    @abstractmethod
    async def connect(self) -> bool:
        """Connect to broker."""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from broker."""
        pass
    
    @abstractmethod
    async def submit_order(self, order: BrokerOrder) -> BrokerOrder:
        """Submit an order."""
        pass
    
    @abstractmethod
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel an order."""
        pass
    
    @abstractmethod
    async def get_positions(self) -> List[Position]:
        """Get current positions."""
        pass
    
    @abstractmethod
    async def get_account_state(self) -> AccountState:
        """Get account state."""
        pass
    
    @abstractmethod
    async def get_market_data(self, symbol: str) -> Dict[str, Any]:
        """Get market data for symbol."""
        pass
    
    def is_connected(self) -> bool:
        """Check if connected."""
        return self.connected


"""
Interactive Brokers Adapter for AFC3.

Note: This is a simulated adapter for testing.
Real IB integration would use the ib_async library.

Author: AFC3 Broker Integration
"""

import random
from datetime import datetime


class InteractiveBrokersAdapter(BrokerInterface):
    """Interactive Brokers adapter (simulated)."""
    
    def __init__(self, mode: str = "paper"):
        super().__init__("Interactive Brokers", mode)
        self.orders: Dict[str, BrokerOrder] = {}
        self.positions: Dict[str, Position] = {}
        self.account = AccountState(cash=100000, buying_power=200000, equity=100000, portfolio_value=100000)
    
    async def connect(self) -> bool:
        """Connect to IB."""
        # Simulate connection
        self.connected = True
        return True
    
    async def disconnect(self) -> None:
        """Disconnect from IB."""
        self.connected = False
    
    async def submit_order(self, order: BrokerOrder) -> BrokerOrder:
        """Submit an order."""
        if not self.connected:
            raise Exception("Not connected to broker")
        
        # Simulate order execution in paper mode
        order.status = OrderStatus.SUBMITTED.value
        
        if self.mode == "paper" or self.mode == "simulation":
            # Simulate fill
            order.status = OrderStatus.FILLED.value
            order.filled_quantity = order.quantity
            order.average_fill_price = random.uniform(95, 105)
        
        self.orders[order.order_id] = order
        return order
    
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel an order."""
        if order_id in self.orders:
            self.orders[order_id].status = OrderStatus.CANCELLED.value
            return True
        return False
    
    async def get_positions(self) -> List[Position]:
        """Get positions."""
        return list(self.positions.values())
    
    async def get_account_state(self) -> AccountState:
        """Get account state."""
        return self.account
    
    async def get_market_data(self, symbol: str) -> Dict[str, Any]:
        """Get market data."""
        return {
            "symbol": symbol,
            "bid": random.uniform(100, 200),
            "ask": random.uniform(100, 200),
            "last": random.uniform(100, 200),
            "volume": random.randint(1000000, 10000000)
        }


"""
Schwab Adapter for AFC3.

Simulated adapter for Schwab/Thinkorswim.

Author: AFC3 Broker Integration
"""

from typing import Dict, Any


class SchwabAdapter(BrokerInterface):
    """Schwab adapter (simulated)."""
    
    def __init__(self, mode: str = "paper"):
        super().__init__("Schwab", mode)
        self.orders: Dict[str, BrokerOrder] = {}
        self.positions: Dict[str, Position] = {}
        self.account = AccountState(cash=100000, buying_power=200000, equity=100000, portfolio_value=100000)
    
    async def connect(self) -> bool:
        self.connected = True
        return True
    
    async def disconnect(self) -> None:
        self.connected = False
    
    async def submit_order(self, order: BrokerOrder) -> BrokerOrder:
        if not self.connected:
            raise Exception("Not connected")
        
        order.status = OrderStatus.SUBMITTED.value
        
        if self.mode == "paper":
            order.status = OrderStatus.FILLED.value
            order.filled_quantity = order.quantity
            order.average_fill_price = random.uniform(100, 150)
        
        self.orders[order.order_id] = order
        return order
    
    async def cancel_order(self, order_id: str) -> bool:
        if order_id in self.orders:
            self.orders[order_id].status = OrderStatus.CANCELLED.value
            return True
        return False
    
    async def get_positions(self) -> List[Position]:
        return list(self.positions.values())
    
    async def get_account_state(self) -> AccountState:
        return self.account
    
    async def get_market_data(self, symbol: str) -> Dict[str, Any]:
        return {
            "symbol": symbol,
            "bid": random.uniform(150, 200),
            "ask": random.uniform(150, 200),
            "last": random.uniform(150, 200),
            "volume": random.randint(500000, 5000000)
        }


"""
Paper Trading Engine for AFC3.

Simulates broker execution using real market data.

Author: AFC3 Broker Integration
"""

from typing import Dict, Any, List
import random


class PaperTradingEngine:
    """Paper trading engine."""
    
    def __init__(self, initial_capital: float = 100000):
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.positions: Dict[str, Position] = {}
        self.orders: Dict[str, BrokerOrder] = {}
        self.order_id_counter = 0
    
    def create_order(self, symbol: str, side: str, quantity: float, 
                   order_type: str = "market", limit_price: float = None) -> BrokerOrder:
        """Create a paper trade order."""
        self.order_id_counter += 1
        order = BrokerOrder(
            order_id=f"PAPER_{self.order_id_counter}",
            symbol=symbol,
            side=side,
            quantity=quantity,
            order_type=order_type,
            limit_price=limit_price,
            status=OrderStatus.PENDING.value
        )
        return order
    
    def execute_order(self, order: BrokerOrder, market_price: float) -> BrokerOrder:
        """Execute a paper trade order."""
        # Apply slippage
        slippage = random.uniform(-0.001, 0.001)
        fill_price = market_price * (1 + slippage)
        
        # Calculate commission (0.1%)
        commission = order.quantity * fill_price * 0.001
        
        if order.side == OrderSide.BUY.value:
            cost = order.quantity * fill_price + commission
            if cost > self.cash:
                order.status = OrderStatus.REJECTED.value
                return order
            
            self.cash -= cost
            
            # Update position
            if order.symbol in self.positions:
                pos = self.positions[order.symbol]
                new_qty = pos.quantity + order.quantity
                pos.average_price = (pos.quantity * pos.average_price + order.quantity * fill_price) / new_qty
                pos.quantity = new_qty
            else:
                self.positions[order.symbol] = Position(
                    symbol=order.symbol,
                    quantity=order.quantity,
                    average_price=fill_price,
                    market_value=order.quantity * fill_price,
                    unrealized_pnl=0
                )
        else:  # SELL
            proceeds = order.quantity * fill_price - commission
            self.cash += proceeds
            
            if order.symbol in self.positions:
                self.positions[order.symbol].quantity -= order.quantity
                if self.positions[order.symbol].quantity <= 0:
                    del self.positions[order.symbol]
        
        order.status = OrderStatus.FILLED.value
        order.filled_quantity = order.quantity
        order.average_fill_price = fill_price
        
        self.orders[order.order_id] = order
        
        return order
    
    def get_portfolio_value(self) -> float:
        """Get total portfolio value."""
        positions_value = sum(p.market_value for p in self.positions.values())
        return self.cash + positions_value
    
    def get_positions(self) -> List[Position]:
        """Get current positions."""
        return list(self.positions.values())
    
    def get_account_state(self) -> AccountState:
        """Get account state."""
        portfolio_value = self.get_portfolio_value()
        return AccountState(
            cash=self.cash,
            buying_power=self.cash * 2,
            equity=portfolio_value,
            portfolio_value=portfolio_value
        )


"""
Order Router for AFC3.

Routes orders to selected broker.

Author: AFC3 Broker Integration
"""

from typing import Dict, Any, Optional


class OrderRouter:
    """Routes orders to brokers."""
    
    def __init__(self):
        self.brokers: Dict[str, BrokerInterface] = {}
        self.default_broker: Optional[str] = None
        self.mode = "paper"  # simulation, paper, live
    
    def register_broker(self, broker_id: str, broker: BrokerInterface) -> None:
        """Register a broker."""
        self.brokers[broker_id] = broker
        if self.default_broker is None:
            self.default_broker = broker_id
    
    def set_default_broker(self, broker_id: str) -> bool:
        """Set default broker."""
        if broker_id in self.brokers:
            self.default_broker = broker_id
            return True
        return False
    
    def set_mode(self, mode: str) -> None:
        """Set execution mode."""
        if mode in ["simulation", "paper", "live"]:
            self.mode = mode
    
    async def route_order(self, order: BrokerOrder, broker_id: str = None) -> BrokerOrder:
        """Route order to broker."""
        target = broker_id or self.default_broker
        
        if target not in self.brokers:
            raise Exception(f"Broker {target} not found")
        
        broker = self.brokers[target]
        
        if not broker.is_connected():
            await broker.connect()
        
        return await broker.submit_order(order)
    
    def get_broker_status(self) -> Dict[str, Any]:
        """Get broker status."""
        return {
            mode: self.mode,
            default_broker: self.default_broker,
            brokers: {bid: b.is_connected() for bid, b in self.brokers.items()}
        }


def create_broker_adapter(broker_type: str, mode: str = "paper") -> BrokerInterface:
    """Factory to create broker adapters."""
    if broker_type == "ib":
        return InteractiveBrokersAdapter(mode)
    elif broker_type == "schwab":
        return SchwabAdapter(mode)
    else:
        raise ValueError(f"Unknown broker type: {broker_type}")
