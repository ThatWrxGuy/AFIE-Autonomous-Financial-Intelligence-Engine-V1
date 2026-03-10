"""
Execution Intelligence Agent for AFC3.

This agent is responsible for turning allocation outputs into executable orders
and routing them in paper/simulated mode.

Responsibilities:
- convert portfolio order intents into executable orders
- choose execution style
- estimate slippage
- estimate transaction cost
- simulate fills or route through a paper-trading adapter
- track order state
- track execution quality
- publish execution events back into AFC3

Actions:
- validate_order_intents
- generate_orders
- estimate_slippage
- estimate_transaction_cost
- simulate_execution
- route_paper_orders
- track_order_status
- summarize_execution_quality

Author: AFC3 Capital Deployment Layer
"""

from typing import Dict, Any, List, Optional
import asyncio
import time
from datetime import datetime

from agents.base_agent import BaseAgent, AgentResult
from core.data_contracts import (
    OrderIntent,
    ExecutionOrder,
    FillReport,
    ExecutionSummary
)
from execution.base_execution_adapter import (
    BaseExecutionAdapter,
    SimulatedExecutionAdapter,
    PaperExecutionAdapter,
    create_execution_adapter
)
from core.event_bus import EventBus, get_event_bus


class ExecutionIntelligenceAgent(BaseAgent):
    """
    Execution Intelligence AI Agent for order execution.
    
    Converts order intents into executable orders and routes them
    through paper/simulated execution.
    """
    
    def __init__(self, name: str, execution_mode: str = "simulation"):
        super().__init__(name, "execution_intelligence")
        
        # Execution adapter (default to simulation)
        self.execution_adapter: BaseExecutionAdapter = create_execution_adapter(
            mode=execution_mode,
            slippage_bps=5.0,
            commission=0.001
        )
        
        # Order tracking
        self.active_orders: Dict[str, ExecutionOrder] = {}
        self.order_intents: Dict[str, OrderIntent] = {}
        self.execution_summaries: Dict[str, ExecutionSummary] = {}
        
        # Memory references
        self.short_term_memory = None
        self.long_term_memory = None
        self.event_bus: Optional[EventBus] = None
    
    def set_short_term_memory(self, memory):
        """Set short-term memory reference."""
        self.short_term_memory = memory
    
    def set_long_term_memory(self, memory):
        """Set long-term memory reference."""
        self.long_term_memory = memory
    
    def set_event_bus(self, bus: EventBus):
        """Set event bus reference."""
        self.event_bus = bus
    
    def set_execution_mode(self, mode: str):
        """Set execution mode (simulation or paper)."""
        self.execution_adapter = create_execution_adapter(
            mode=mode,
            slippage_bps=5.0,
            commission=0.001
        )
    
    async def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processes execution intelligence tasks.
        Returns standardized result envelope.
        """
        action = task.get("action")
        data = task.get("data", {})
        task_id = task.get("id", "unknown")
        
        start_time = time.time()
        
        print(f"Agent {self.name} (ID: {self.id}) processing {action} task.")
        
        try:
            if action == "validate_order_intents":
                result = await self.validate_order_intents(data)
            elif action == "generate_orders":
                result = await self.generate_orders(data)
            elif action == "estimate_slippage":
                result = await self.estimate_slippage(data)
            elif action == "estimate_transaction_cost":
                result = await self.estimate_transaction_cost(data)
            elif action == "simulate_execution":
                result = await self.simulate_execution(data)
            elif action == "route_paper_orders":
                result = await self.route_paper_orders(data)
            elif action == "track_order_status":
                result = await self.track_order_status(data)
            elif action == "summarize_execution_quality":
                result = await self.summarize_execution_quality(data)
            else:
                raise ValueError(f"Unknown action: {action}")
            
            duration = time.time() - start_time
            
            # Return standardized success envelope
            return AgentResult.success(
                agent_id=self.id,
                agent_type=self.agent_type,
                action=action,
                task_id=task_id,
                result=result,
                duration_seconds=duration
            )
            
        except Exception as e:
            # Return standardized error envelope
            return AgentResult.error(
                agent_id=self.id,
                agent_type=self.agent_type,
                action=action,
                task_id=task_id,
                error=str(e)
            )
    
    async def handle_message(self, message: Dict[str, Any]) -> None:
        """Handles incoming messages."""
        print(f"Agent {self.name} (ID: {self.id}) received message: {message.get('content')}")
    
    async def validate_order_intents(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate order intents before execution.
        
        Performs strict validation:
        - Must have asset
        - Must have side (buy/sell)
        - Quantity must be > 0
        """
        order_intents_data = data.get("order_intents", [])
        
        validated_intents = []
        validation_errors = []
        
        for intent_data in order_intents_data:
            errors = []
            
            # Parse order intent
            intent = OrderIntent(**intent_data)
            
            # Validate required fields
            if not intent.asset:
                errors.append("Missing asset")
            
            if not intent.side:
                errors.append("Missing side (buy/sell)")
            elif intent.side not in ["buy", "sell"]:
                errors.append(f"Invalid side: {intent.side}")
            
            if intent.quantity <= 0:
                errors.append(f"Quantity must be > 0, got {intent.quantity}")
            
            if not intent.order_type:
                errors.append("Missing order_type")
            elif intent.order_type not in ["market", "limit", "vwap", "twap"]:
                errors.append(f"Invalid order_type: {intent.order_type}")
            
            if errors:
                validation_errors.append({
                    "order_intent_id": intent.order_intent_id,
                    "errors": errors
                })
            else:
                validated_intents.append(intent_data)
        
        result = {
            "validated": len(validated_intents),
            "rejected": len(validation_errors),
            "valid_intents": validated_intents,
            "validation_errors": validation_errors
        }
        
        return result
    
    async def generate_orders(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate executable orders from order intents.
        """
        order_intents_data = data.get("order_intents", [])
        
        orders = []
        
        for intent_data in order_intents_data:
            intent = OrderIntent(**intent_data)
            
            # Store order intent
            self.order_intents[intent.order_intent_id] = intent
            
            # Create execution order
            order = ExecutionOrder(
                order_intent_id=intent.order_intent_id,
                asset=intent.asset,
                side=intent.side,
                execution_mode=self.execution_adapter.mode,
                order_type=intent.order_type,
                route="default",
                quantity=intent.quantity,
                status="pending"
            )
            
            # Add limit price for limit orders
            if intent.order_type == "limit":
                order.limit_price = data.get("default_price", 100.0)
            
            # Store order
            self.active_orders[order.order_id] = order
            orders.append(order.to_dict())
            
            # Emit event
            if self.event_bus:
                from core.event_bus import Event
                event = Event(
                    event_type="order.generated",
                    source=self.agent_type,
                    payload=order.to_dict()
                )
                await self.event_bus.publish(event)
        
        result = {
            "orders": orders,
            "total_orders": len(orders)
        }
        
        # Store in memory
        if self.short_term_memory:
            self.short_term_memory.set("active_orders", [o.to_dict() for o in self.active_orders.values()])
        
        return result
    
    async def estimate_slippage(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Estimate slippage for an order.
        """
        order_type = data.get("order_type", "market")
        quantity = data.get("quantity", 0)
        urgency = data.get("urgency", "medium")
        
        # Slippage estimates (in basis points)
        slippage_estimates = {
            "market": {"low": 2.0, "medium": 5.0, "high": 10.0},
            "limit": {"low": 0.5, "medium": 1.0, "high": 2.0},
            "vwap": {"low": 3.0, "medium": 7.0, "high": 15.0},
            "twap": {"low": 4.0, "medium": 8.0, "high": 12.0}
        }
        
        bps = slippage_estimates.get(order_type, {}).get(urgency, 5.0)
        
        # Estimate dollar slippage
        price = data.get("estimated_price", 100.0)
        estimated_slippage = price * (bps / 10000) * quantity
        
        result = {
            "order_type": order_type,
            "urgency": urgency,
            "estimated_slippage_bps": bps,
            "estimated_slippage_dollars": estimated_slippage
        }
        
        return result
    
    async def estimate_transaction_cost(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Estimate total transaction cost.
        """
        quantity = data.get("quantity", 0)
        price = data.get("price", 100.0)
        order_type = data.get("order_type", "market")
        
        # Commission rate (0.1% = 0.001)
        commission_rate = 0.001
        
        # SEC fee (for sells only)
        sec_fee_rate = 0.0000278
        
        # Calculate costs
        gross_notional = quantity * price
        commission = gross_notional * commission_rate
        sec_fee = gross_notional * sec_fee_rate if data.get("side") == "sell" else 0
        
        # Estimated slippage
        slippage_result = await self.estimate_slippage(data)
        
        total_cost = commission + sec_fee + slippage_result["estimated_slippage_dollars"]
        
        result = {
            "gross_notional": gross_notional,
            "commission": commission,
            "sec_fee": sec_fee,
            "estimated_slippage": slippage_result["estimated_slippage_dollars"],
            "total_cost": total_cost,
            "cost_bps": (total_cost / gross_notional * 10000) if gross_notional > 0 else 0
        }
        
        return result
    
    async def simulate_execution(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simulate execution of orders.
        """
        orders_data = data.get("orders", [])
        
        fill_reports = []
        
        for order_data in orders_data:
            # Get or create order
            if "order_id" in order_data and order_data["order_id"] in self.active_orders:
                order = self.active_orders[order_data["order_id"]]
            else:
                order = ExecutionOrder(**order_data)
                self.active_orders[order.order_id] = order
            
            # Submit to execution adapter
            executed_order = await self.execution_adapter.submit_order(order)
            
            # Get fill reports
            fills = self.execution_adapter.get_fills(executed_order.order_id)
            
            for fill in fills:
                fill_reports.append(fill.to_dict())
            
            # Emit execution event
            if self.event_bus:
                from core.event_bus import Event
                event = Event(
                    event_type="order.executed" if executed_order.status == "filled" else "order.failed",
                    source=self.agent_type,
                    payload={
                        "order": executed_order.to_dict(),
                        "fills": [f.to_dict() for f in fills]
                    }
                )
                await self.event_bus.publish(event)
        
        result = {
            "orders_executed": len(orders_data),
            "fill_reports": fill_reports
        }
        
        # Update memory
        if self.short_term_memory:
            self.short_term_memory.set("recent_fills", fill_reports)
        
        return result
    
    async def route_paper_orders(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Route orders through paper trading adapter.
        """
        # Ensure we're in paper mode
        self.set_execution_mode("paper")
        
        # Generate orders first
        orders_result = await self.generate_orders(data)
        
        # Then simulate execution
        execution_result = await self.simulate_execution({
            "orders": orders_result["orders"]
        })
        
        result = {
            "orders": orders_result["orders"],
            "execution_result": execution_result,
            "mode": "paper"
        }
        
        # Get paper portfolio state if available
        if hasattr(self.execution_adapter, "get_paper_portfolio_state"):
            portfolio_state = self.execution_adapter.get_paper_portfolio_state()
            result["paper_portfolio"] = portfolio_state
        
        return result
    
    async def track_order_status(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Track status of active orders.
        """
        order_id = data.get("order_id")
        
        if order_id:
            # Track specific order
            if order_id in self.active_orders:
                order = self.active_orders[order_id]
                fills = self.execution_adapter.get_fills(order_id)
                
                return {
                    "order": order.to_dict(),
                    "fills": [f.to_dict() for f in fills]
                }
            else:
                return {"error": f"Order {order_id} not found"}
        
        # Return all active orders
        active = [
            {
                "order": o.to_dict(),
                "fills": [f.to_dict() for f in self.execution_adapter.get_fills(o.order_id)]
            }
            for o in self.active_orders.values()
        ]
        
        return {
            "active_orders": active,
            "total_active": len(active)
        }
    
    async def summarize_execution_quality(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate execution quality summary.
        """
        order_intent_id = data.get("order_intent_id")
        
        if not order_intent_id:
            return {"error": "order_intent_id required"}
        
        # Get execution summary from adapter
        summary = self.execution_adapter.get_execution_summary(order_intent_id)
        
        if not summary:
            return {"error": f"No execution found for order_intent {order_intent_id}"}
        
        # Store in memory
        self.execution_summaries[summary.summary_id] = summary
        
        # Store in long-term memory
        if self.long_term_memory:
            self.long_term_memory.store_model_output(
                f"execution_{summary.summary_id}",
                summary.to_dict()
            )
        
        # Emit event
        if self.event_bus:
            from core.event_bus import Event
            event = Event(
                event_type="execution.summary_generated",
                source=self.agent_type,
                payload=summary.to_dict()
            )
            await self.event_bus.publish(event)
        
        return summary.to_dict()
    
    def get_active_orders(self) -> List[Dict[str, Any]]:
        """Get all active orders."""
        return [o.to_dict() for o in self.active_orders.values()]
    
    def get_execution_summaries(self) -> List[Dict[str, Any]]:
        """Get all execution summaries."""
        return [s.to_dict() for s in self.execution_summaries.values()]
