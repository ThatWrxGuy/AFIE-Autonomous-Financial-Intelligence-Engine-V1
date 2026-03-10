"""
Portfolio Intelligence Agent for AFC3.

This agent is responsible for converting approved strategy outputs into capital allocation decisions.

Responsibilities:
- validate approved strategies before allocation
- evaluate risk-adjusted attractiveness
- size positions
- control leverage
- manage concentration limits
- evaluate cross-strategy correlation
- enforce portfolio constraints
- generate allocation decisions

Actions:
- validate_strategy_for_allocation
- score_strategy_for_allocation
- calculate_position_size
- construct_portfolio_allocation
- rebalance_portfolio
- enforce_risk_limits
- evaluate_correlation_exposure
- generate_order_intents

Author: AFC3 Capital Deployment Layer
"""

from typing import Dict, Any, List, Optional
import asyncio
import time
from datetime import datetime

from agents.base_agent import BaseAgent, AgentResult
from core.data_contracts import (
    ApprovedStrategy,
    AllocationDecision,
    OrderIntent,
    PortfolioState,
    PortfolioConstraintSet
)
from core.portfolio_constraints import PortfolioConstraintEngine, create_default_engine
from core.event_bus import EventBus, get_event_bus


class PortfolioIntelligenceAgent(BaseAgent):
    """
    Portfolio Intelligence AI Agent for capital allocation decisions.
    
    Converts approved strategies into allocation decisions and order intents.
    """
    
    def __init__(self, name: str, initial_capital: float = 100000.0):
        super().__init__(name, "portfolio_intelligence")
        
        # Portfolio settings
        self.initial_capital = initial_capital
        self.portfolio_state = PortfolioState(cash_available=initial_capital)
        
        # Constraint engine
        self.constraint_engine = create_default_engine()
        
        # Memory references (set by main.py)
        self.experiment_store = None
        self.short_term_memory = None
        self.long_term_memory = None
        self.event_bus: Optional[EventBus] = None
    
    def set_experiment_store(self, store):
        """Set experiment store reference."""
        self.experiment_store = store
    
    def set_short_term_memory(self, memory):
        """Set short-term memory reference."""
        self.short_term_memory = memory
    
    def set_long_term_memory(self, memory):
        """Set long-term memory reference."""
        self.long_term_memory = memory
    
    def set_event_bus(self, bus: EventBus):
        """Set event bus reference."""
        self.event_bus = bus
    
    async def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processes portfolio intelligence tasks.
        Returns standardized result envelope.
        """
        action = task.get("action")
        data = task.get("data", {})
        task_id = task.get("id", "unknown")
        
        start_time = time.time()
        
        print(f"Agent {self.name} (ID: {self.id}) processing {action} task.")
        
        try:
            if action == "validate_strategy_for_allocation":
                result = await self.validate_strategy_for_allocation(data)
            elif action == "score_strategy_for_allocation":
                result = await self.score_strategy_for_allocation(data)
            elif action == "calculate_position_size":
                result = await self.calculate_position_size(data)
            elif action == "construct_portfolio_allocation":
                result = await self.construct_portfolio_allocation(data)
            elif action == "rebalance_portfolio":
                result = await self.rebalance_portfolio(data)
            elif action == "enforce_risk_limits":
                result = await self.enforce_risk_limits(data)
            elif action == "evaluate_correlation_exposure":
                result = await self.evaluate_correlation_exposure(data)
            elif action == "generate_order_intents":
                result = await self.generate_order_intents(data)
            elif action == "get_portfolio_state":
                result = self.get_portfolio_state()
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
    
    async def validate_strategy_for_allocation(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate approved strategy before allocation.
        
        Performs strict validation gates:
        - Check required fields exist
        - Check approval_status is approved
        - Check risk metrics are present
        """
        strategy_data = data.get("strategy", {})
        
        # Parse strategy into ApprovedStrategy object
        strategy = ApprovedStrategy.from_dict(strategy_data)
        
        # Validate using constraint engine
        is_valid, error_message = self.constraint_engine.validate_strategy_for_allocation(strategy)
        
        # Additional validation
        if strategy.sharpe_ratio is not None and strategy.sharpe_ratio < 0:
            is_valid = False
            error_message = "Sharpe ratio cannot be negative"
        
        if strategy.max_drawdown is not None and strategy.max_drawdown < 0:
            is_valid = False
            error_message = "Max drawdown cannot be negative"
        
        # Get current portfolio state
        portfolio_state = self.portfolio_state
        
        # Check portfolio-level constraints
        if portfolio_state.unrealized_pnl < -portfolio_state.cash_available * 0.2:
            is_valid = False
            error_message = "Portfolio drawdown exceeds 20% - no new allocations allowed"
        
        result = {
            "is_valid": is_valid,
            "strategy_id": strategy.strategy_id,
            "validation_errors": [error_message] if error_message else [],
            "portfolio_state": {
                "cash_available": portfolio_state.cash_available,
                "current_leverage": portfolio_state.leverage,
                "unrealized_pnl": portfolio_state.unrealized_pnl
            }
        }
        
        # Store in experiment store if available
        if self.experiment_store and not is_valid:
            self.experiment_store.update_experiment(
                strategy.pipeline_run_id,
                validation_metrics={"allocation_validation_failed": error_message}
            )
        
        # Emit event
        if self.event_bus:
            from core.event_bus import Event
            event_type = "strategy.approved_for_allocation" if is_valid else "strategy.rejected_for_allocation"
            event = Event(
                event_type=event_type,
                source=self.agent_type,
                payload=result
            )
            await self.event_bus.publish(event)
        
        return result
    
    async def score_strategy_for_allocation(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Score strategy for allocation based on risk-adjusted attractiveness.
        """
        strategy_data = data.get("strategy", {})
        strategy = ApprovedStrategy.from_dict(strategy_data)
        
        # Calculate composite score
        sharpe = strategy.sharpe_ratio or 0
        expected_return = strategy.expected_return or 0
        confidence = strategy.confidence or 0.5
        regime_score = strategy.regime_score or 0.5
        
        # Composite score formula
        score = (sharpe * 0.3 + expected_return * 0.2 + confidence * 0.25 + regime_score * 0.25)
        
        # Normalize to 0-100
        normalized_score = min(max(score * 50, 0), 100)
        
        result = {
            "strategy_id": strategy.strategy_id,
            "composite_score": normalized_score,
            "component_scores": {
                "sharpe_score": sharpe * 30,
                "return_score": expected_return * 20,
                "confidence_score": confidence * 25,
                "regime_score": regime_score * 25
            }
        }
        
        return result
    
    async def calculate_position_size(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate position size based on strategy and constraints.
        """
        strategy_data = data.get("strategy", {})
        strategy = ApprovedStrategy.from_dict(strategy_data)
        
        target_weight = data.get("target_weight", 0.1)  # Default 10%
        max_position = data.get("max_position", self.portfolio_state.cash_available * 0.25)
        
        # Calculate notional
        available_capital = self.portfolio_state.cash_available
        target_notional = available_capital * target_weight
        
        # Apply constraints
        if target_notional > max_position:
            target_notional = max_position
            target_weight = target_notional / available_capital
        
        # Apply regime-based reduction if adverse
        if strategy.regime_score and strategy.regime_score < 0.5:
            reduction = 0.5
            target_notional *= (1 - reduction)
            target_weight *= (1 - reduction)
        
        result = {
            "strategy_id": strategy.strategy_id,
            "target_weight": target_weight,
            "target_notional": target_notional,
            "position_size": target_notional,
            "max_position": max_position,
            "available_capital": available_capital
        }
        
        return result
    
    async def construct_portfolio_allocation(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Construct full portfolio allocation from approved strategies.
        """
        strategies = data.get("strategies", [])
        
        allocation_decisions = []
        
        for strategy_data in strategies:
            strategy = ApprovedStrategy.from_dict(strategy_data)
            
            # Validate
            is_valid, error = self.constraint_engine.validate_strategy_for_allocation(strategy)
            
            if not is_valid:
                # Create rejected decision
                decision = AllocationDecision(
                    strategy_id=strategy.strategy_id,
                    approved=False,
                    rejection_reason=error
                )
            else:
                # Calculate allocation
                position_result = await self.calculate_position_size({
                    "strategy": strategy_data,
                    "target_weight": 1.0 / len(strategies) if strategies else 0.1
                })
                
                # Create approved decision
                decision = AllocationDecision(
                    strategy_id=strategy.strategy_id,
                    approved=True,
                    target_weight=position_result["target_weight"],
                    target_notional=position_result["target_notional"],
                    position_size=position_result["position_size"],
                    leverage=1.0
                )
            
            allocation_decisions.append(decision.to_dict())
            
            # Store in experiment store
            if self.experiment_store:
                self.experiment_store.create_experiment(
                    f"allocation_{decision.decision_id}",
                    f"allocation_{strategy.strategy_id}"
                )
                self.experiment_store.update_experiment(
                    f"allocation_{decision.decision_id}",
                    validation_metrics=decision.to_dict()
                )
                if decision.approved:
                    self.experiment_store.approve_strategy(
                        f"allocation_{decision.decision_id}",
                        "Approved by Portfolio Intelligence"
                    )
                else:
                    self.experiment_store.reject_strategy(
                        f"allocation_{decision.decision_id}",
                        decision.rejection_reason or "Rejected by Portfolio Intelligence"
                    )
        
        result = {
            "allocation_decisions": allocation_decisions,
            "total_strategies": len(strategies),
            "approved_count": sum(1 for d in allocation_decisions if d.get("approved")),
            "rejected_count": sum(1 for d in allocation_decisions if not d.get("approved"))
        }
        
        # Emit allocation events
        if self.event_bus:
            from core.event_bus import Event
            for decision in allocation_decisions:
                event_type = "allocation.created" if decision["approved"] else "allocation.rejected"
                event = Event(
                    event_type=event_type,
                    source=self.agent_type,
                    payload=decision
                )
                await self.event_bus.publish(event)
        
        return result
    
    async def rebalance_portfolio(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Rebalance existing portfolio allocations.
        """
        target_allocations = data.get("target_allocations", {})
        
        rebalance_actions = []
        
        current_positions = self.portfolio_state.current_positions
        
        for strategy_id, target_weight in target_allocations.items():
            current_weight = current_positions.get(strategy_id, {}).get("weight", 0)
            weight_diff = target_weight - current_weight
            
            action = "buy" if weight_diff > 0 else "sell"
            notional_diff = abs(weight_diff) * self.portfolio_state.cash_available
            
            rebalance_actions.append({
                "strategy_id": strategy_id,
                "action": action,
                "weight_change": weight_diff,
                "notional_change": notional_diff
            })
        
        result = {
            "rebalance_actions": rebalance_actions,
            "current_portfolio_state": self.portfolio_state.to_dict()
        }
        
        return result
    
    async def enforce_risk_limits(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enforce all risk limits and constraints.
        """
        strategy_data = data.get("strategy", {})
        allocation_data = data.get("allocation", {})
        
        strategy = ApprovedStrategy.from_dict(strategy_data)
        allocation = AllocationDecision(
            strategy_id=allocation_data.get("strategy_id", ""),
            target_weight=allocation_data.get("target_weight", 0.1)
        )
        
        # Check all constraints
        all_passed, constraint_results = self.constraint_engine.check_all_constraints(
            strategy, allocation, self.portfolio_state
        )
        
        # Get applied constraints
        applied = self.constraint_engine.get_applied_constraints(constraint_results)
        
        result = {
            "all_passed": all_passed,
            "constraints_checked": [r.to_dict() for r in constraint_results],
            "constraints_applied": applied,
            "portfolio_state": self.portfolio_state.to_dict()
        }
        
        # Check kill switch
        if self.constraint_engine.kill_switch_triggered:
            result["kill_switch_triggered"] = True
            result["message"] = "Kill switch triggered - no new allocations"
        
        return result
    
    async def evaluate_correlation_exposure(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate cross-strategy correlation exposure.
        """
        strategy_data = data.get("strategy", {})
        
        # Get current exposures
        current_exposure = self.portfolio_state.exposure_by_strategy
        
        # Simple correlation check (in production, would use actual correlation matrix)
        strategy_id = strategy_data.get("strategy_id", "new_strategy")
        
        # Assume high correlation with similar strategies
        max_correlated_exposure = sum(current_exposure.values()) * 0.8
        
        result = {
            "strategy_id": strategy_id,
            "current_total_exposure": sum(current_exposure.values()),
            "max_correlated_exposure": max_correlated_exposure,
            "would_exceed_limit": max_correlated_exposure > 0.4,
            "correlation_warning": "High correlation with existing strategies" if max_correlated_exposure > 0.3 else None
        }
        
        return result
    
    async def generate_order_intents(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate order intents from allocation decisions.
        """
        allocation_decisions = data.get("allocation_decisions", [])
        
        order_intents = []
        
        for decision_data in allocation_decisions:
            if not decision_data.get("approved"):
                continue
            
            strategy_id = decision_data["strategy_id"]
            target_notional = decision_data.get("target_notional", 0)
            
            # Create order intent for each asset in the strategy
            # In production, would parse signal_payload for actual assets
            intent = OrderIntent(
                asset=data.get("default_asset", "SPY"),
                side="buy",
                quantity=target_notional / 100,  # Simplified: $100 per share
                order_type=data.get("order_type", "market"),
                urgency=data.get("urgency", "medium"),
                strategy_id=strategy_id,
                portfolio_context=self.portfolio_state.to_dict()
            )
            
            order_intents.append(intent.to_dict())
            
            # Emit event
            if self.event_bus:
                from core.event_bus import Event
                event = Event(
                    event_type="order_intent.created",
                    source=self.agent_type,
                    payload=intent.to_dict()
                )
                await self.event_bus.publish(event)
        
        result = {
            "order_intents": order_intents,
            "total_intents": len(order_intents)
        }
        
        # Store in memory
        if self.short_term_memory:
            self.short_term_memory.set("pending_order_intents", order_intents)
        
        return result
    
    def get_portfolio_state(self) -> Dict[str, Any]:
        """Get current portfolio state."""
        return self.portfolio_state.to_dict()
    
    def update_portfolio_state(self, fill_data: Dict[str, Any]) -> None:
        """
        Update portfolio state after execution.
        """
        # Update positions
        asset = fill_data.get("asset", "SPY")
        filled_quantity = fill_data.get("filled_quantity", 0)
        filled_price = fill_data.get("average_fill_price", 0)
        
        if asset not in self.portfolio_state.current_positions:
            self.portfolio_state.current_positions[asset] = {
                "quantity": 0,
                "avg_price": 0,
                "weight": 0
            }
        
        pos = self.portfolio_state.current_positions[asset]
        old_qty = pos["quantity"]
        
        # Update quantity
        pos["quantity"] += filled_quantity
        
        # Update average price
        if filled_quantity > 0:
            total_cost = (old_qty * pos["avg_price"]) + (filled_quantity * filled_price)
            pos["avg_price"] = total_cost / (old_qty + filled_quantity) if (old_qty + filled_quantity) > 0 else 0
        
        # Update weights
        total_value = sum(
            p["quantity"] * p["avg_price"] 
            for p in self.portfolio_state.current_positions.values()
        )
        
        for asset, pos in self.portfolio_state.current_positions.items():
            pos["weight"] = (pos["quantity"] * pos["avg_price"]) / total_value if total_value > 0 else 0
        
        # Update cash
        cost = filled_quantity * filled_price
        self.portfolio_state.cash_available -= cost
        self.portfolio_state.allocated_capital += cost
        
        # Update leverage
        self.portfolio_state.leverage = (
            self.portfolio_state.allocated_capital / self.portfolio_state.cash_available
            if self.portfolio_state.cash_available > 0 else 1.0
        )
        
        # Update exposure
        self.portfolio_state.exposure_by_asset[asset] = filled_quantity * filled_price
