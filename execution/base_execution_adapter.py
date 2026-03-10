"""
Execution Adapter Base Class for AFC3.

This module defines the abstract base class for execution adapters.

Subclasses:
- SimulatedExecutionAdapter: Simulates execution with slippage
- PaperExecutionAdapter: Paper trading simulation

Author: AFC3 Capital Deployment Layer
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import random
import uuid
from datetime import datetime

from core.data_contracts import (
    ExecutionOrder,
    FillReport,
    ExecutionSummary
)


class BaseExecutionAdapter(ABC):
    """
    Abstract base class for execution adapters.
    
    All adapters must implement:
    - submit_order
    - cancel_order
    - get_order_status
    """
    
    def __init__(self, name: str, mode: str = "simulation"):
        self.name = name
        self.mode = mode  # simulation, paper, live
        self.orders: Dict[str, ExecutionOrder] = {}
        self.fills: Dict[str, List[FillReport]] = {}
    
    @abstractmethod
    async def submit_order(self, order: ExecutionOrder) -> ExecutionOrder:
        """
        Submit an order for execution.
        
        Args:
            order: ExecutionOrder to submit
            
        Returns:
            Updated order with status
        """
        pass
    
    @abstractmethod
    async def cancel_order(self, order_id: str) -> bool:
        """
        Cancel an order.
        
        Args:
            order_id: Order ID to cancel
            
        Returns:
            True if cancelled successfully
        """
        pass
    
    @abstractmethod
    async def get_order_status(self, order_id: str) -> Optional[ExecutionOrder]:
        """
        Get current order status.
        
        Args:
            order_id: Order ID
            
        Returns:
            ExecutionOrder or None
        """
        pass
    
    def get_fills(self, order_id: str) -> List[FillReport]:
        """Get fills for an order."""
        return self.fills.get(order_id, [])
    
    def generate_fill_report(
        self,
        order: ExecutionOrder,
        simulated_price: float,
        slippage_bps: float = 5.0,
        commission: float = 0.001
    ) -> FillReport:
        """
        Generate a fill report from a simulated execution.
        
        Args:
            order: Execution order
            simulated_price: Simulated market price
            slippage_bps: Slippage in basis points
            commission: Commission rate
            
        Returns:
            FillReport
        """
        # Calculate slippage
        slippage_multiplier = slippage_bps / 10000
        price_adjustment = simulated_price * slippage_multiplier
        
        # Apply slippage based on side
        if order.side == "buy":
            fill_price = simulated_price + price_adjustment
        else:
            fill_price = simulated_price - price_adjustment
        
        # Calculate costs
        cost = order.quantity * fill_price
        commission_cost = cost * commission
        
        # Create fill report
        fill = FillReport(
            fill_id=str(uuid.uuid4()),
            order_id=order.order_id,
            filled_quantity=order.quantity,
            average_fill_price=fill_price,
            slippage_realized=order.quantity * price_adjustment,
            cost_realized=commission_cost,
            status="filled"
        )
        
        return fill
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert adapter state to dict."""
        return {
            "name": self.name,
            "mode": self.mode,
            "orders_count": len(self.orders),
            "fills_count": sum(len(f) for f in self.fills.values())
        }


class SimulatedExecutionAdapter(BaseExecutionAdapter):
    """
    Simulated execution adapter.
    
    Simulates fills with realistic slippage and costs.
    Default mode: simulation only (no real money)
    """
    
    def __init__(
        self,
        name: str = "SimulatedExecutionAdapter",
        slippage_bps: float = 5.0,
        commission: float = 0.001,
        latency_ms: float = 100.0
    ):
        super().__init__(name, "simulation")
        
        self.slippage_bps = slippage_bps
        self.commission = commission
        self.latency_ms = latency_ms
    
    async def submit_order(self, order: ExecutionOrder) -> ExecutionOrder:
        """Submit order for simulated execution."""
        order.status = "pending"
        order.execution_mode = "simulation"
        
        # Store order
        self.orders[order.order_id] = order
        
        # Simulate execution
        await self._simulate_execution(order)
        
        return order
    
    async def _simulate_execution(self, order: ExecutionOrder):
        """Simulate order execution."""
        # Generate simulated market price (in production, would fetch real price)
        # Using a random price around $100-$500 for simulation
        simulated_price = random.uniform(100, 500)
        
        # Set estimated values
        order.estimated_slippage = simulated_price * (self.slippage_bps / 10000)
        order.estimated_cost = order.quantity * simulated_price * self.commission
        
        # Generate fill
        fill = self.generate_fill_report(
            order,
            simulated_price,
            self.slippage_bps,
            self.commission
        )
        
        # Store fill
        if order.order_id not in self.fills:
            self.fills[order.order_id] = []
        self.fills[order.order_id].append(fill)
        
        # Update order status
        order.status = "filled"
    
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel an order."""
        if order_id in self.orders:
            order = self.orders[order_id]
            if order.status == "pending":
                order.status = "cancelled"
                return True
        return False
    
    async def get_order_status(self, order_id: str) -> Optional[ExecutionOrder]:
        """Get order status."""
        return self.orders.get(order_id)
    
    def get_execution_summary(self, order_intent_id: str) -> Optional[ExecutionSummary]:
        """Get execution summary for an order intent."""
        # Find orders for this intent
        intent_orders = [o for o in self.orders.values() if o.order_intent_id == order_intent_id]
        
        if not intent_orders:
            return None
        
        # Collect fills
        all_fills = []
        for order in intent_orders:
            all_fills.extend(self.get_fills(order.order_id))
        
        if not all_fills:
            return None
        
        # Calculate summary
        total_qty = sum(f.filled_quantity for f in all_fills)
        total_cost = sum(f.filled_quantity * f.average_fill_price for f in all_fills)
        avg_price = total_cost / total_qty if total_qty > 0 else 0
        
        summary = ExecutionSummary(
            order_intent_id=order_intent_id,
            fill_reports=all_fills,
            total_quantity=total_qty,
            average_price=avg_price,
            total_slippage=sum(f.slippage_realized for f in all_fills),
            total_cost=sum(f.cost_realized for f in all_fills)
        )
        
        return summary


class PaperExecutionAdapter(BaseExecutionAdapter):
    """
    Paper trading execution adapter.
    
    Simulates execution like SimulatedExecutionAdapter but maintains
    a paper portfolio state. Default mode: paper trading (no real money).
    """
    
    def __init__(
        self,
        name: str = "PaperExecutionAdapter",
        slippage_bps: float = 3.0,
        commission: float = 0.0005,
        latency_ms: float = 50.0
    ):
        super().__init__(name, "paper")
        
        self.slippage_bps = slippage_bps
        self.commission = commission
        self.latency_ms = latency_ms
        
        # Paper portfolio state
        self.positions: Dict[str, Dict[str, Any]] = {}
        self.cash = 100000.0  # Starting paper cash
    
    async def submit_order(self, order: ExecutionOrder) -> ExecutionOrder:
        """Submit order for paper execution."""
        order.status = "pending"
        order.execution_mode = "paper"
        
        # Store order
        self.orders[order.order_id] = order
        
        # Simulate execution
        await self._simulate_execution(order)
        
        # Update paper portfolio
        await self._update_paper_portfolio(order)
        
        return order
    
    async def _simulate_execution(self, order: ExecutionOrder):
        """Simulate order execution."""
        # Generate simulated market price
        simulated_price = random.uniform(100, 500)
        
        # Set estimated values
        order.estimated_slippage = simulated_price * (self.slippage_bps / 10000)
        order.estimated_cost = order.quantity * simulated_price * self.commission
        
        # Generate fill
        fill = self.generate_fill_report(
            order,
            simulated_price,
            self.slippage_bps,
            self.commission
        )
        
        # Store fill
        if order.order_id not in self.fills:
            self.fills[order.order_id] = []
        self.fills[order.order_id].append(fill)
        
        # Update order status
        order.status = "filled"
    
    async def _update_paper_portfolio(self, order: ExecutionOrder):
        """Update paper portfolio after fill."""
        asset = order.asset
        
        # Get fill
        fills = self.get_fills(order.order_id)
        if not fills:
            return
        
        fill = fills[0]
        
        # Update position
        if asset not in self.positions:
            self.positions[asset] = {"quantity": 0, "avg_price": 0}
        
        pos = self.positions[asset]
        old_qty = pos["quantity"]
        
        # Update quantity
        if order.side == "buy":
            pos["quantity"] += fill.filled_quantity
        else:
            pos["quantity"] -= fill.filled_quantity
        
        # Update average price
        if pos["quantity"] > 0:
            total_cost = (old_qty * pos["avg_price"]) + (fill.filled_quantity * fill.average_fill_price)
            pos["avg_price"] = total_cost / pos["quantity"] if pos["quantity"] > 0 else 0
        else:
            pos["avg_price"] = 0
        
        # Update cash
        cost = fill.filled_quantity * fill.average_fill_price
        if order.side == "buy":
            self.cash -= cost
        else:
            self.cash += cost
    
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel an order."""
        if order_id in self.orders:
            order = self.orders[order_id]
            if order.status == "pending":
                order.status = "cancelled"
                return True
        return False
    
    async def get_order_status(self, order_id: str) -> Optional[ExecutionOrder]:
        """Get order status."""
        return self.orders.get(order_id)
    
    def get_paper_portfolio_state(self) -> Dict[str, Any]:
        """Get current paper portfolio state."""
        total_value = sum(
            pos["quantity"] * pos["avg_price"]
            for pos in self.positions.values()
        )
        
        return {
            "cash": self.cash,
            "positions": self.positions,
            "total_value": total_value + self.cash
        }


def create_execution_adapter(
    mode: str = "simulation",
    **kwargs
) -> BaseExecutionAdapter:
    """
    Factory function to create execution adapters.
    
    Args:
        mode: Execution mode (simulation, paper)
        **kwargs: Additional adapter-specific parameters
        
    Returns:
        BaseExecutionAdapter instance
    """
    if mode == "simulation":
        return SimulatedExecutionAdapter(**kwargs)
    elif mode == "paper":
        return PaperExecutionAdapter(**kwargs)
    else:
        raise ValueError(f"Unknown execution mode: {mode}")
