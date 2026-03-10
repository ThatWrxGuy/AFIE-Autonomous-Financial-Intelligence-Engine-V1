"""
Core module for AFC3.

Provides:
- Event Bus: core/event_bus.py
- Logging: core/logging_utils.py
- Data Contracts: core/data_contracts.py
- Portfolio Constraints: core/portfolio_constraints.py
"""

from core.event_bus import EventBus, get_event_bus, publish_event
from core.logging_utils import get_logger, log_info, log_warning, log_error, log_debug
from core.data_contracts import (
    ApprovedStrategy,
    AllocationDecision,
    PortfolioConstraintSet,
    OrderIntent,
    ExecutionOrder,
    FillReport,
    ExecutionSummary,
    PortfolioState
)
from core.portfolio_constraints import PortfolioConstraintEngine, create_default_engine

__all__ = [
    "EventBus", 
    "get_event_bus", 
    "publish_event",
    "get_logger",
    "log_info",
    "log_warning",
    "log_error",
    "log_debug",
    "ApprovedStrategy",
    "AllocationDecision",
    "PortfolioConstraintSet",
    "OrderIntent",
    "ExecutionOrder",
    "FillReport",
    "ExecutionSummary",
    "PortfolioState",
    "PortfolioConstraintEngine",
    "create_default_engine"
]
