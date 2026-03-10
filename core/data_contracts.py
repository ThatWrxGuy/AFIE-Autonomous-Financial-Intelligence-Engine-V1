"""
Capital Deployment Data Contracts for AFC3.

This module defines canonical schemas for the capital deployment layer.

Classes:
- ApprovedStrategy: Strategy approved from research workflow
- AllocationDecision: Capital allocation decision
- PortfolioConstraintSet: Risk constraints
- OrderIntent: Intent to trade
- ExecutionOrder: Executable order
- FillReport: Trade fill report
- ExecutionSummary: Execution quality summary
- PortfolioState: Current portfolio state
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import uuid


@dataclass
class ApprovedStrategy:
    """
    Represents a strategy approved from the research workflow.
    
    Fields:
    - strategy_id: Unique identifier
    - pipeline_run_id: Research pipeline run ID
    - approval_status: approval_status from research
    - signal_payload: Trading signals
    - expected_return: Expected return
    - sharpe_ratio: Risk-adjusted return metric
    - max_drawdown: Maximum drawdown
    - regime_score: Macro regime alignment
    - confidence: Confidence level
    - timestamp: Approval timestamp
    """
    strategy_id: str
    pipeline_run_id: str
    approval_status: str  # "approved"
    signal_payload: Dict[str, Any]
    expected_return: Optional[float] = None
    sharpe_ratio: Optional[float] = None
    max_drawdown: Optional[float] = None
    regime_score: Optional[float] = None
    confidence: Optional[float] = None
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ApprovedStrategy':
        return cls(**data)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "strategy_id": self.strategy_id,
            "pipeline_run_id": self.pipeline_run_id,
            "approval_status": self.approval_status,
            "signal_payload": self.signal_payload,
            "expected_return": self.expected_return,
            "sharpe_ratio": self.sharpe_ratio,
            "max_drawdown": self.max_drawdown,
            "regime_score": self.regime_score,
            "confidence": self.confidence,
            "timestamp": self.timestamp
        }


@dataclass
class AllocationDecision:
    """
    Represents a capital allocation decision.
    
    Fields:
    - decision_id: Unique identifier
    - strategy_id: Associated strategy
    - approved: Whether allocation was approved
    - target_weight: Target portfolio weight
    - target_notional: Target notional value
    - position_size: Position size
    - leverage: Leverage applied
    - constraints_applied: Constraints that were applied
    - rejection_reason: Reason if rejected
    - timestamp: Decision timestamp
    """
    decision_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    strategy_id: str = ""
    approved: bool = False
    target_weight: Optional[float] = None
    target_notional: Optional[float] = None
    position_size: Optional[float] = None
    leverage: float = 1.0
    constraints_applied: List[str] = field(default_factory=list)
    rejection_reason: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "strategy_id": self.strategy_id,
            "approved": self.approved,
            "target_weight": self.target_weight,
            "target_notional": self.target_notional,
            "position_size": self.position_size,
            "leverage": self.leverage,
            "constraints_applied": self.constraints_applied,
            "rejection_reason": self.rejection_reason,
            "timestamp": self.timestamp
        }


@dataclass
class PortfolioConstraintSet:
    """
    Portfolio risk constraints.
    
    Fields:
    - max_allocation_per_strategy: Max % in one strategy
    - max_allocation_per_asset: Max % in one asset
    - max_sector_exposure: Max sector exposure
    - max_portfolio_leverage: Max leverage
    - max_drawdown_threshold: Max drawdown allowed
    - max_concentration: Max concentration
    - max_correlation_exposure: Max correlation cluster
    - min_liquidity: Min liquidity requirement
    - min_sharpe_ratio: Min sharpe for allocation
    - regime_based_reduction: Regime-based exposure reduction
    - kill_switch_drawdown: Kill switch threshold
    """
    max_allocation_per_strategy: float = 0.25  # 25%
    max_allocation_per_asset: float = 0.30  # 30%
    max_sector_exposure: float = 0.50  # 50%
    max_portfolio_leverage: float = 2.0  # 2x
    max_drawdown_threshold: float = 0.20  # 20%
    max_concentration: float = 0.30  # 30%
    max_correlation_exposure: float = 0.40  # 40%
    min_liquidity: float = 10000.0  # $10k minimum
    min_sharpe_ratio: float = 0.5  # Min sharpe
    regime_based_reduction: float = 0.5  # 50% reduction in adverse regime
    kill_switch_drawdown: float = 0.25  # 25%
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "max_allocation_per_strategy": self.max_allocation_per_strategy,
            "max_allocation_per_asset": self.max_allocation_per_asset,
            "max_sector_exposure": self.max_sector_exposure,
            "max_portfolio_leverage": self.max_portfolio_leverage,
            "max_drawdown_threshold": self.max_drawdown_threshold,
            "max_concentration": self.max_concentration,
            "max_correlation_exposure": self.max_correlation_exposure,
            "min_liquidity": self.min_liquidity,
            "min_sharpe_ratio": self.min_sharpe_ratio,
            "regime_based_reduction": self.regime_based_reduction,
            "kill_switch_drawdown": self.kill_switch_drawdown
        }


@dataclass
class OrderIntent:
    """
    Represents an intent to trade.
    
    Fields:
    - order_intent_id: Unique identifier
    - asset: Asset to trade
    - side: buy/sell
    - quantity: Quantity
    - order_type: market/limit/VWAP/TWAP
    - urgency: low/medium/high
    - strategy_id: Source strategy
    - portfolio_context: Portfolio state
    - risk_tags: Risk tags
    - timestamp: Creation timestamp
    """
    order_intent_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    asset: str = ""
    side: str = ""  # "buy" or "sell"
    quantity: float = 0.0
    order_type: str = "market"  # market, limit, vwap, twap
    urgency: str = "medium"  # low, medium, high
    strategy_id: str = ""
    portfolio_context: Dict[str, Any] = field(default_factory=dict)
    risk_tags: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "order_intent_id": self.order_intent_id,
            "asset": self.asset,
            "side": self.side,
            "quantity": self.quantity,
            "order_type": self.order_type,
            "urgency": self.urgency,
            "strategy_id": self.strategy_id,
            "portfolio_context": self.portfolio_context,
            "risk_tags": self.risk_tags,
            "timestamp": self.timestamp
        }


@dataclass
class ExecutionOrder:
    """
    Represents an executable order.
    
    Fields:
    - order_id: Unique identifier
    - order_intent_id: Source order intent
    - asset: Asset to trade
    - side: buy/sell
    - execution_mode: simulation/paper/live
    - order_type: market/limit/VWAP/TWAP
    - route: Execution route
    - limit_price: Limit price (if applicable)
    - quantity: Order quantity
    - status: pending/filled/partial/cancelled/failed
    - estimated_slippage: Estimated slippage
    - estimated_cost: Estimated cost
    - timestamp: Creation timestamp
    """
    order_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    order_intent_id: str = ""
    asset: str = ""
    side: str = ""  # buy or sell
    execution_mode: str = "simulation"  # simulation, paper, live
    order_type: str = "market"
    route: str = "default"
    limit_price: Optional[float] = None
    quantity: float = 0.0
    status: str = "pending"  # pending, filled, partial, cancelled, failed
    estimated_slippage: Optional[float] = None
    estimated_cost: Optional[float] = None
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "order_id": self.order_id,
            "order_intent_id": self.order_intent_id,
            "asset": self.asset,
            "side": self.side,
            "execution_mode": self.execution_mode,
            "order_type": self.order_type,
            "route": self.route,
            "limit_price": self.limit_price,
            "quantity": self.quantity,
            "status": self.status,
            "estimated_slippage": self.estimated_slippage,
            "estimated_cost": self.estimated_cost,
            "timestamp": self.timestamp
        }


@dataclass
class FillReport:
    """
    Represents a trade fill report.
    
    Fields:
    - fill_id: Unique identifier
    - order_id: Source order
    - filled_quantity: Quantity filled
    - average_fill_price: Average fill price
    - slippage_realized: Actual slippage
    - cost_realized: Actual cost
    - status: filled/partial/rejected
    - timestamp: Fill timestamp
    """
    fill_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    order_id: str = ""
    filled_quantity: float = 0.0
    average_fill_price: float = 0.0
    slippage_realized: float = 0.0
    cost_realized: float = 0.0
    status: str = "filled"  # filled, partial, rejected
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "fill_id": self.fill_id,
            "order_id": self.order_id,
            "filled_quantity": self.filled_quantity,
            "average_fill_price": self.average_fill_price,
            "slippage_realized": self.slippage_realized,
            "cost_realized": self.cost_realized,
            "status": self.status,
            "timestamp": self.timestamp
        }


@dataclass
class ExecutionSummary:
    """
    Summary of execution quality.
    
    Fields:
    - summary_id: Unique identifier
    - order_intent_id: Source order intent
    - fill_reports: List of fill reports
    - total_quantity: Total quantity
    - average_price: Average fill price
    - total_slippage: Total slippage
    - total_cost: Total cost
    - execution_duration: Duration
    - timestamp: Summary timestamp
    """
    summary_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    order_intent_id: str = ""
    fill_reports: List[FillReport] = field(default_factory=list)
    total_quantity: float = 0.0
    average_price: float = 0.0
    total_slippage: float = 0.0
    total_cost: float = 0.0
    execution_duration: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "summary_id": self.summary_id,
            "order_intent_id": self.order_intent_id,
            "fill_reports": [fr.to_dict() for fr in self.fill_reports],
            "total_quantity": self.total_quantity,
            "average_price": self.average_price,
            "total_slippage": self.total_slippage,
            "total_cost": self.total_cost,
            "execution_duration": self.execution_duration,
            "timestamp": self.timestamp
        }


@dataclass
class PortfolioState:
    """
    Current portfolio state.
    
    Fields:
    - cash_available: Available cash
    - allocated_capital: Allocated capital
    - reserved_capital: Reserved capital
    - current_positions: Current positions
    - unrealized_pnl: Unrealized P&L
    - realized_pnl: Realized P&L
    - leverage: Current leverage
    - exposure_by_asset: Exposure by asset
    - exposure_by_strategy: Exposure by strategy
    - pending_orders: Pending orders
    - timestamp: State timestamp
    """
    cash_available: float = 100000.0  # $100k default
    allocated_capital: float = 0.0
    reserved_capital: float = 0.0
    current_positions: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0
    leverage: float = 1.0
    exposure_by_asset: Dict[str, float] = field(default_factory=dict)
    exposure_by_strategy: Dict[str, float] = field(default_factory=dict)
    pending_orders: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "cash_available": self.cash_available,
            "allocated_capital": self.allocated_capital,
            "reserved_capital": self.reserved_capital,
            "current_positions": self.current_positions,
            "unrealized_pnl": self.unrealized_pnl,
            "realized_pnl": self.realized_pnl,
            "leverage": self.leverage,
            "exposure_by_asset": self.exposure_by_asset,
            "exposure_by_strategy": self.exposure_by_strategy,
            "pending_orders": self.pending_orders,
            "timestamp": self.timestamp
        }
    
    def get_total_exposure(self) -> float:
        """Get total portfolio exposure."""
        return sum(self.exposure_by_asset.values()) + self.allocated_capital
