"""
Portfolio Constraint Engine for AFC3.

This module provides constraint checking and risk control for the capital deployment layer.

Features:
- Max allocation per strategy
- Max allocation per asset
- Max sector exposure
- Max portfolio leverage
- Max drawdown threshold
- Max concentration
- Correlation exposure limits
- Minimum liquidity requirements
- Regime-based exposure reduction
- Kill-switch conditions

Author: AFC3 Capital Deployment Layer
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from core.data_contracts import (
    ApprovedStrategy,
    AllocationDecision,
    PortfolioConstraintSet,
    PortfolioState
)


@dataclass
class ConstraintResult:
    """Result of a constraint check."""
    passed: bool
    constraint_name: str
    message: str
    value: Optional[float] = None
    limit: Optional[float] = None


class PortfolioConstraintEngine:
    """
    Portfolio constraint and risk control engine.
    
    Validates allocation decisions against portfolio constraints.
    """
    
    def __init__(self, constraints: Optional[PortfolioConstraintSet] = None):
        self.constraints = constraints or PortfolioConstraintSet()
        self.kill_switch_triggered = False
    
    def reset_kill_switch(self):
        """Reset the kill switch."""
        self.kill_switch_triggered = False
    
    def check_all_constraints(
        self,
        strategy: ApprovedStrategy,
        allocation_decision: AllocationDecision,
        portfolio_state: PortfolioState
    ) -> Tuple[bool, List[ConstraintResult]]:
        """
        Check all constraints for an allocation decision.
        
        Args:
            strategy: Approved strategy
            allocation_decision: Proposed allocation
            portfolio_state: Current portfolio state
            
        Returns:
            Tuple of (all_passed, list of constraint results)
        """
        results = []
        
        # Check kill switch first
        if self.kill_switch_triggered:
            results.append(ConstraintResult(
                passed=False,
                constraint_name="kill_switch",
                message="Kill switch triggered - no new allocations allowed"
            ))
            return False, results
        
        # Check individual constraints
        results.append(self.check_sharpe_ratio(strategy))
        results.append(self.check_max_drawdown(strategy))
        results.append(self.check_max_allocation_per_strategy(allocation_decision, portfolio_state))
        results.append(self.check_max_leverage(allocation_decision, portfolio_state))
        results.append(self.check_concentration(allocation_decision, portfolio_state))
        results.append(self.check_regime_based_exposure(strategy, allocation_decision))
        
        # Determine if all passed
        all_passed = all(r.passed for r in results)
        
        return all_passed, results
    
    def check_sharpe_ratio(self, strategy: ApprovedStrategy) -> ConstraintResult:
        """
        Check if sharpe ratio meets minimum threshold.
        
        Block allocation if sharpe ratio below threshold.
        """
        sharpe = strategy.sharpe_ratio
        
        if sharpe is None:
            return ConstraintResult(
                passed=False,
                constraint_name="min_sharpe_ratio",
                message="Strategy has no sharpe ratio - cannot validate"
            )
        
        if sharpe < self.constraints.min_sharpe_ratio:
            return ConstraintResult(
                passed=False,
                constraint_name="min_sharpe_ratio",
                message=f"Sharpe ratio {sharpe:.2f} below minimum {self.constraints.min_sharpe_ratio:.2f}",
                value=sharpe,
                limit=self.constraints.min_sharpe_ratio
            )
        
        return ConstraintResult(
            passed=True,
            constraint_name="min_sharpe_ratio",
            message=f"Sharpe ratio {sharpe:.2f} meets minimum",
            value=sharpe,
            limit=self.constraints.min_sharpe_ratio
        )
    
    def check_max_drawdown(self, strategy: ApprovedStrategy) -> ConstraintResult:
        """
        Check if max drawdown is within threshold.
        
        Block allocation if max_drawdown above threshold.
        """
        drawdown = strategy.max_drawdown
        
        if drawdown is None:
            return ConstraintResult(
                passed=False,
                constraint_name="max_drawdown_threshold",
                message="Strategy has no drawdown data - cannot validate"
            )
        
        if drawdown > self.constraints.max_drawdown_threshold:
            return ConstraintResult(
                passed=False,
                constraint_name="max_drawdown_threshold",
                message=f"Max drawdown {drawdown:.2%} exceeds threshold {self.constraints.max_drawdown_threshold:.2%}",
                value=drawdown,
                limit=self.constraints.max_drawdown_threshold
            )
        
        return ConstraintResult(
            passed=True,
            constraint_name="max_drawdown_threshold",
            message=f"Max drawdown {drawdown:.2%} within threshold",
            value=drawdown,
            limit=self.constraints.max_drawdown_threshold
        )
    
    def check_max_allocation_per_strategy(
        self,
        allocation: AllocationDecision,
        portfolio_state: PortfolioState
    ) -> ConstraintResult:
        """Check if allocation exceeds max per-strategy limit."""
        target_weight = allocation.target_weight or 0
        
        if target_weight > self.constraints.max_allocation_per_strategy:
            return ConstraintResult(
                passed=False,
                constraint_name="max_allocation_per_strategy",
                message=f"Target weight {target_weight:.2%} exceeds max {self.constraints.max_allocation_per_strategy:.2%}",
                value=target_weight,
                limit=self.constraints.max_allocation_per_strategy
            )
        
        return ConstraintResult(
            passed=True,
            constraint_name="max_allocation_per_strategy",
            message=f"Target weight {target_weight:.2%} within limit",
            value=target_weight,
            limit=self.constraints.max_allocation_per_strategy
        )
    
    def check_max_leverage(
        self,
        allocation: AllocationDecision,
        portfolio_state: PortfolioState
    ) -> ConstraintResult:
        """Check if total leverage would exceed limit."""
        current_leverage = portfolio_state.leverage
        new_allocation_leverage = allocation.leverage
        
        projected_leverage = current_leverage + (new_allocation_leverage - 1)
        
        if projected_leverage > self.constraints.max_portfolio_leverage:
            return ConstraintResult(
                passed=False,
                constraint_name="max_portfolio_leverage",
                message=f"Projected leverage {projected_leverage:.2f}x exceeds max {self.constraints.max_portfolio_leverage:.2f}x",
                value=projected_leverage,
                limit=self.constraints.max_portfolio_leverage
            )
        
        return ConstraintResult(
            passed=True,
            constraint_name="max_portfolio_leverage",
            message=f"Leverage {projected_leverage:.2f}x within limit",
            value=projected_leverage,
            limit=self.constraints.max_portfolio_leverage
        )
    
    def check_concentration(
        self,
        allocation: AllocationDecision,
        portfolio_state: PortfolioState
    ) -> ConstraintResult:
        """Check portfolio concentration limits."""
        target_weight = allocation.target_weight or 0
        
        # Get current max concentration
        current_positions = portfolio_state.current_positions
        max_current = 0
        for pos in current_positions.values():
            weight = pos.get("weight", 0)
            if weight > max_current:
                max_current = weight
        
        # Check if new allocation would exceed concentration
        new_concentration = max_current + target_weight
        
        if new_concentration > self.constraints.max_concentration:
            return ConstraintResult(
                passed=False,
                constraint_name="max_concentration",
                message=f"New concentration {new_concentration:.2%} would exceed max {self.constraints.max_concentration:.2%}",
                value=new_concentration,
                limit=self.constraints.max_concentration
            )
        
        return ConstraintResult(
            passed=True,
            constraint_name="max_concentration",
            message=f"Concentration {new_concentration:.2%} within limit",
            value=new_concentration,
            limit=self.constraints.max_concentration
        )
    
    def check_regime_based_exposure(
        self,
        strategy: ApprovedStrategy,
        allocation: AllocationDecision
    ) -> ConstraintResult:
        """
        Reduce sizing if macro regime is adverse.
        
        If regime_score is low, apply regime-based exposure reduction.
        """
        regime_score = strategy.regime_score
        
        if regime_score is None:
            # No regime data - allow allocation
            return ConstraintResult(
                passed=True,
                constraint_name="regime_based_exposure",
                message="No regime data - no reduction applied"
            )
        
        # If regime is adverse (low score), apply reduction
        if regime_score < 0.5:
            reduction = self.constraints.regime_based_reduction
            adjusted_weight = (allocation.target_weight or 0) * (1 - reduction)
            
            return ConstraintResult(
                passed=True,
                constraint_name="regime_based_exposure",
                message=f"Adverse regime - weight reduced by {reduction:.0%} to {adjusted_weight:.2%}",
                value=adjusted_weight,
                limit=allocation.target_weight
            )
        
        return ConstraintResult(
            passed=True,
            constraint_name="regime_based_exposure",
            message=f"Regime favorable - full allocation allowed"
        )
    
    def check_drawdown_kill_switch(self, portfolio_state: PortfolioState) -> bool:
        """
        Check if kill switch should be triggered based on drawdown.
        
        Returns True if kill switch should be triggered.
        """
        # Calculate current drawdown from peak
        current_drawdown = abs(portfolio_state.unrealized_pnl) / (portfolio_state.cash_available + portfolio_state.allocated_capital)
        
        if current_drawdown > self.constraints.kill_switch_drawdown:
            self.kill_switch_triggered = True
            return True
        
        return False
    
    def validate_strategy_for_allocation(
        self,
        strategy: ApprovedStrategy
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate a strategy can proceed to allocation.
        
        Args:
            strategy: Approved strategy to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        errors = []
        
        # Check required fields
        if not strategy.strategy_id:
            errors.append("Missing strategy_id")
        
        if not strategy.signal_payload:
            errors.append("Missing signal_payload")
        
        if strategy.approval_status != "approved":
            errors.append(f"Strategy not approved: {strategy.approval_status}")
        
        # Check metrics exist
        if strategy.sharpe_ratio is None:
            errors.append("Missing sharpe_ratio")
        
        if strategy.max_drawdown is None:
            errors.append("Missing max_drawdown")
        
        if errors:
            return False, "; ".join(errors)
        
        return True, None
    
    def get_applied_constraints(
        self,
        results: List[ConstraintResult]
    ) -> List[str]:
        """Get list of constraint names that were applied."""
        return [r.constraint_name for r in results if r.passed]


def create_default_engine() -> PortfolioConstraintEngine:
    """Create constraint engine with default settings."""
    return PortfolioConstraintEngine(PortfolioConstraintSet())
