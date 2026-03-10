"""
Risk Limits Configuration for Institutional Risk Governance.

Defines configurable risk limits.

Author: AFC3 Risk Governance
"""

from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class RiskLimits:
    """Configurable risk limits."""
    max_portfolio_leverage: float = 2.0
    max_strategy_allocation: float = 0.25
    max_single_asset_exposure: float = 0.30
    max_drawdown_limit: float = 0.20
    max_daily_loss_limit: float = 0.05
    max_correlation_exposure: float = 0.40
    max_concentration: float = 0.30
    max_pending_orders: int = 100
    min_cash_reserve: float = 10000.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "max_portfolio_leverage": self.max_portfolio_leverage,
            "max_strategy_allocation": self.max_strategy_allocation,
            "max_single_asset_exposure": self.max_single_asset_exposure,
            "max_drawdown_limit": self.max_drawdown_limit,
            "max_daily_loss_limit": self.max_daily_loss_limit,
            "max_correlation_exposure": self.max_correlation_exposure,
            "max_concentration": self.max_concentration,
            "max_pending_orders": self.max_pending_orders,
            "min_cash_reserve": self.min_cash_reserve
        }


class RiskLimitManager:
    """Manages risk limits."""
    
    def __init__(self):
        self.limits = RiskLimits()
        self.overrides: Dict[str, float] = {}
    
    def update_limit(self, name: str, value: float) -> bool:
        """Update a specific limit."""
        if hasattr(self.limits, name):
            setattr(self.limits, name, value)
            return True
        return False
    
    def get_limit(self, name: str) -> float:
        """Get a limit value."""
        if name in self.overrides:
            return self.overrides[name]
        return getattr(self.limits, name, 0)
    
    def override_limit(self, name: str, value: float) -> None:
        """Override a limit temporarily."""
        self.overrides[name] = value
    
    def clear_overrides(self) -> None:
        """Clear all overrides."""
        self.overrides.clear()
    
    def get_all_limits(self) -> Dict[str, Any]:
        """Get all limits as dict."""
        return self.limits.to_dict()


"""
Global Risk Manager for Institutional Risk Governance.

Monitors system-wide risk metrics.

Author: AFC3 Risk Governance
"""

from typing import Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class RiskMetrics:
    """Current risk metrics."""
    timestamp: str
    portfolio_leverage: float = 1.0
    gross_exposure: float = 0.0
    net_exposure: float = 0.0
    max_strategy_allocation: float = 0.0
    max_asset_exposure: float = 0.0
    current_drawdown: float = 0.0
    daily_pnl: float = 0.0
    pending_orders: int = 0
    var_95: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "portfolio_leverage": self.portfolio_leverage,
            "gross_exposure": self.gross_exposure,
            "net_exposure": self.net_exposure,
            "max_strategy_allocation": self.max_strategy_allocation,
            "max_asset_exposure": self.max_asset_exposure,
            "current_drawdown": self.current_drawdown,
            "daily_pnl": self.daily_pnl,
            "pending_orders": self.pending_orders,
            "var_95": self.var_95
        }


class GlobalRiskManager:
    """Manages global risk monitoring."""
    
    def __init__(self, limit_manager):
        self.limit_manager = limit_manager
        self.metrics_history: List[RiskMetrics] = []
    
    def calculate_metrics(self, portfolio_state: Dict, positions: List[Dict]) -> RiskMetrics:
        """Calculate current risk metrics."""
        # Extract metrics
        leverage = portfolio_state.get("leverage", 1.0)
        
        # Calculate exposures
        gross = sum(p.get("value", 0) for p in positions)
        net = sum(p.get("value", 0) if p.get("side") == "long" else -p.get("value", 0) for p in positions)
        
        # Max allocations
        max_strategy = max([p.get("strategy_weight", 0) for p in positions] + [0])
        max_asset = max([p.get("weight", 0) for p in positions] + [0])
        
        # Drawdown
        drawdown = abs(portfolio_state.get("unrealized_pnl", 0)) / portfolio_state.get("cash_available", 1)
        
        metrics = RiskMetrics(
            timestamp=datetime.utcnow().isoformat(),
            portfolio_leverage=leverage,
            gross_exposure=gross,
            net_exposure=net,
            max_strategy_allocation=max_strategy,
            max_asset_exposure=max_asset,
            current_drawdown=drawdown,
            daily_pnl=portfolio_state.get("daily_pnl", 0),
            pending_orders=portfolio_state.get("pending_orders", 0)
        )
        
        self.metrics_history.append(metrics)
        return metrics
    
    def check_limits(self, metrics: RiskMetrics, portfolio_state: Dict = None) -> Dict[str, Any]:
        """Check if metrics violate limits."""
        violations = []
        warnings = []
        
        limits = self.limit_manager.limits
        
        # Check leverage
        if metrics.portfolio_leverage > limits.max_portfolio_leverage:
            violations.append(f"Leverage {metrics.portfolio_leverage:.2f} exceeds limit {limits.max_portfolio_leverage}")
        
        # Check strategy allocation
        if metrics.max_strategy_allocation > limits.max_strategy_allocation:
            violations.append(f"Strategy allocation {metrics.max_strategy_allocation:.1%} exceeds limit")
        
        # Check asset exposure
        if metrics.max_asset_exposure > limits.max_single_asset_exposure:
            warnings.append(f"Asset exposure {metrics.max_asset_exposure:.1%} approaching limit")
        
        # Check drawdown - use portfolio_state if available
        if portfolio_state and "total_value" in portfolio_state:
            initial_capital = getattr(self, 'initial_capital', 100000)
            total_value = portfolio_state.get("total_value", initial_capital)
            if total_value < initial_capital:
                drawdown = (initial_capital - total_value) / initial_capital
                if drawdown > limits.max_drawdown_limit:
                    violations.append(f"Drawdown {drawdown:.1%} exceeds limit")
        elif metrics.current_drawdown > limits.max_drawdown_limit:
            violations.append(f"Drawdown {metrics.current_drawdown:.1%} exceeds limit")
        
        # Check daily loss
        if metrics.daily_pnl < -limits.max_daily_loss_limit:
            violations.append(f"Daily loss {metrics.daily_pnl:.1%} exceeds limit")
        
        return {
            "violations": violations,
            "warnings": warnings,
            "kill_switch_triggered": len(violations) > 0
        }


"""
Kill Switch for Institutional Risk Governance.

Emergency halt system.

Author: AFC3 Risk Governance
"""

from typing import Dict, Any, List
from datetime import datetime


class KillSwitch:
    """Emergency halt system."""
    
    def __init__(self):
        self.triggered = False
        self.trigger_time = None
        self.trigger_reason = None
        self.auto_reset = False
    
    def trigger(self, reason: str) -> None:
        """Trigger kill switch."""
        self.triggered = True
        self.trigger_time = datetime.utcnow().isoformat()
        self.trigger_reason = reason
    
    def reset(self) -> None:
        """Reset kill switch."""
        self.triggered = False
        self.trigger_time = None
        self.trigger_reason = None
    
    def is_active(self) -> bool:
        """Check if kill switch is active."""
        return self.triggered
    
    def get_status(self) -> Dict[str, Any]:
        """Get kill switch status."""
        return {
            "active": self.triggered,
            "trigger_time": self.trigger_time,
            "reason": self.trigger_reason
        }


"""
Anomaly Detection for Institutional Risk Governance.

Detects abnormal system behavior.

Author: AFC3 Risk Governance
"""

from typing import Dict, Any, List
import statistics


class AnomalyDetector:
    """Detects abnormal behavior."""
    
    def __init__(self):
        self.pnl_history: List[float] = []
        self.order_history: List[int] = []
        self.thresholds = {
            "pnl_std_multiplier": 3.0,
            "order_rate_multiplier": 3.0
        }
    
    def record_pnl(self, pnl: float) -> None:
        """Record PnL for anomaly detection."""
        self.pnl_history.append(pnl)
        if len(self.pnl_history) > 100:
            self.pnl_history = self.pnl_history[-100:]
    
    def record_orders(self, count: int) -> None:
        """Record order count."""
        self.order_history.append(count)
        if len(self.order_history) > 100:
            self.order_history = self.order_history[-100:]
    
    def detect_pnl_anomaly(self) -> bool:
        """Detect abnormal PnL."""
        if len(self.pnl_history) < 10:
            return False
        
        mean = statistics.mean(self.pnl_history)
        std = statistics.stdev(self.pnl_history) if len(self.pnl_history) > 1 else 1
        
        recent = self.pnl_history[-1]
        
        if abs(recent - mean) > std * self.thresholds["pnl_std_multiplier"]:
            return True
        
        return False
    
    def detect_order_anomaly(self) -> bool:
        """Detect abnormal order rate."""
        if len(self.order_history) < 10:
            return False
        
        mean = statistics.mean(self.order_history[-10:])
        recent = self.order_history[-1]
        
        if recent > mean * self.thresholds["order_rate_multiplier"]:
            return True
        
        return False
    
    def check_anomalies(self) -> Dict[str, bool]:
        """Check for all anomalies."""
        return {
            "pnl_anomaly": self.detect_pnl_anomaly(),
            "order_anomaly": self.detect_order_anomaly()
        }


"""
Execution Guard for Institutional Risk Governance.

Validates orders before execution.

Author: AFC3 Risk Governance
"""

from typing import Dict, Any, Optional


class ExecutionGuard:
    """Validates orders before execution."""
    
    def __init__(self, limit_manager, kill_switch):
        self.limit_manager = limit_manager
        self.kill_switch = kill_switch
    
    def validate_order(self, order: Dict[str, Any], portfolio_state: Dict) -> Dict[str, Any]:
        """Validate an order."""
        # Check kill switch
        if self.kill_switch.is_active():
            return {"approved": False, "reason": "Kill switch active"}
        
        limits = self.limit_manager.limits
        
        # Check cash
        cash = portfolio_state.get("cash_available", 0)
        order_value = order.get("quantity", 0) * order.get("price", 0)
        
        if order_value > cash - limits.min_cash_reserve:
            return {"approved": False, "reason": "Insufficient cash"}
        
        # Check pending orders
        pending = portfolio_state.get("pending_orders", 0)
        if pending >= limits.max_pending_orders:
            return {"approved": False, "reason": "Max pending orders reached"}
        
        # Check leverage - only if leverage is already at or above max
        leverage = portfolio_state.get("leverage", 1.0)
        if leverage >= limits.max_portfolio_leverage:
            return {"approved": False, "reason": "Max leverage reached"}
        
        return {"approved": True}


"""
Risk Governance Agent for Institutional Risk Governance.

Safety authority agent.

Author: AFC3 Risk Governance
"""

from typing import Dict, Any
import asyncio


class RiskGovernanceAgent:
    """Safety authority agent."""
    
    def __init__(self, risk_manager, kill_switch, anomaly_detector, execution_guard):
        self.risk_manager = risk_manager
        self.kill_switch = kill_switch
        self.anomaly_detector = anomaly_detector
        self.execution_guard = execution_guard
    
    async def evaluate_risk(self, portfolio_state: Dict, positions: List[Dict]) -> Dict[str, Any]:
        """Evaluate current risk state."""
        # Calculate metrics
        metrics = self.risk_manager.calculate_metrics(portfolio_state, positions)
        
        # Check limits
        limit_check = self.risk_manager.check_limits(metrics)
        
        # Check anomalies
        anomalies = self.anomaly_detector.check_anomalies()
        
        # Trigger kill switch if needed
        if limit_check["kill_switch_triggered"]:
            reason = "; ".join(limit_check["violations"])
            self.kill_switch.trigger(reason)
        
        if anomalies.get("pnl_anomaly") or anomalies.get("order_anomaly"):
            limit_check["warnings"].append("Anomaly detected")
        
        return {
            "metrics": metrics.to_dict(),
            "limit_violations": limit_check["violations"],
            "warnings": limit_check["warnings"],
            "kill_switch_active": self.kill_switch.is_active(),
            "anomalies": anomalies
        }
    
    def validate_order(self, order: Dict, portfolio_state: Dict) -> Dict[str, Any]:
        """Validate an order."""
        return self.execution_guard.validate_order(order, portfolio_state)
    
    def get_risk_status(self) -> Dict[str, Any]:
        """Get overall risk status."""
        return {
            "kill_switch": self.kill_switch.get_status(),
            "limits": self.limit_manager.get_all_limits(),
            "anomalies": self.anomaly_detector.check_anomalies()
        }
