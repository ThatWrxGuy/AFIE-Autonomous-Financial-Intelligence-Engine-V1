"""
Integration Tests for AFC3 Capital Deployment Layer.

Tests:
1. Portfolio validation test - malformed or weak strategies are rejected
2. Position sizing test - valid strategies produce allocation decisions
3. Constraint enforcement test - leverage, drawdown, concentration limits
4. Order intent generation test - approved allocations produce valid order intents
5. Execution simulation test - order intents become orders and fill reports
6. End-to-end capital deployment pipeline test

Author: AFC3 Capital Deployment Layer
"""

import asyncio
import pytest
import sys
import os
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.portfolio_intelligence_agent import PortfolioIntelligenceAgent
from agents.execution_intelligence_agent import ExecutionIntelligenceAgent
from core.data_contracts import (
    ApprovedStrategy,
    AllocationDecision,
    OrderIntent,
    ExecutionOrder,
    PortfolioState
)
from core.portfolio_constraints import PortfolioConstraintEngine, PortfolioConstraintSet
from execution.base_execution_adapter import SimulatedExecutionAdapter


class TestPortfolioValidation:
    """Test portfolio validation."""
    
    def test_valid_strategy_passes(self):
        """Test that valid strategy passes validation."""
        engine = PortfolioConstraintEngine()
        
        strategy = ApprovedStrategy(
            strategy_id="test_strategy",
            pipeline_run_id="test_pipeline",
            approval_status="approved",
            signal_payload={"asset": "SPY"},
            sharpe_ratio=1.5,
            max_drawdown=0.1
        )
        
        is_valid, error = engine.validate_strategy_for_allocation(strategy)
        
        assert is_valid is True
        assert error is None
    
    def test_missing_sharpe_rejected(self):
        """Test that missing sharpe ratio causes rejection."""
        engine = PortfolioConstraintEngine()
        
        strategy = ApprovedStrategy(
            strategy_id="test_strategy",
            pipeline_run_id="test_pipeline",
            approval_status="approved",
            signal_payload={"asset": "SPY"},
            sharpe_ratio=None
        )
        
        is_valid, error = engine.validate_strategy_for_allocation(strategy)
        
        assert is_valid is False
        assert "sharpe_ratio" in error
    
    def test_low_sharpe_rejected(self):
        """Test that low sharpe ratio is rejected."""
        engine = PortfolioConstraintEngine(PortfolioConstraintSet(min_sharpe_ratio=1.0))
        
        strategy = ApprovedStrategy(
            strategy_id="test_strategy",
            pipeline_run_id="test_pipeline",
            approval_status="approved",
            signal_payload={"asset": "SPY"},
            sharpe_ratio=0.3,
            max_drawdown=0.1
        )
        
        allocation = AllocationDecision(
            strategy_id="test_strategy",
            target_weight=0.1
        )
        
        portfolio = PortfolioState()
        
        all_passed, results = engine.check_all_constraints(strategy, allocation, portfolio)
        
        sharpe_result = [r for r in results if r.constraint_name == "min_sharpe_ratio"][0]
        
        assert sharpe_result.passed is False
    
    def test_high_drawdown_rejected(self):
        """Test that high drawdown is rejected."""
        engine = PortfolioConstraintEngine(PortfolioConstraintSet(max_drawdown_threshold=0.15))
        
        strategy = ApprovedStrategy(
            strategy_id="test_strategy",
            pipeline_run_id="test_pipeline",
            approval_status="approved",
            signal_payload={"asset": "SPY"},
            sharpe_ratio=1.5,
            max_drawdown=0.25
        )
        
        allocation = AllocationDecision(
            strategy_id="test_strategy",
            target_weight=0.1
        )
        
        portfolio = PortfolioState()
        
        all_passed, results = engine.check_all_constraints(strategy, allocation, portfolio)
        
        drawdown_result = [r for r in results if r.constraint_name == "max_drawdown_threshold"][0]
        
        assert drawdown_result.passed is False


class TestPositionSizing:
    """Test position sizing."""
    
    @pytest.mark.asyncio
    async def test_valid_strategy_gets_position(self):
        """Test that valid strategy produces allocation decision."""
        agent = PortfolioIntelligenceAgent("Test Agent", initial_capital=100000)
        
        strategy_data = {
            "strategy_id": "test_strategy",
            "pipeline_run_id": "test_pipeline",
            "approval_status": "approved",
            "signal_payload": {"asset": "SPY"},
            "sharpe_ratio": 1.5,
            "max_drawdown": 0.1,
            "regime_score": 0.7
        }
        
        result = await agent.calculate_position_size({
            "strategy": strategy_data,
            "target_weight": 0.15
        })
        
        assert result["target_notional"] > 0
        assert result["target_notional"] == 15000.0


class TestOrderIntents:
    """Test order intent generation."""
    
    @pytest.mark.asyncio
    async def test_allocation_generates_order_intents(self):
        """Test that approved allocation generates order intents."""
        agent = PortfolioIntelligenceAgent("Test Agent", initial_capital=100000)
        
        allocation_decisions = [{
            "strategy_id": "test_strategy",
            "approved": True,
            "target_weight": 0.1,
            "target_notional": 10000
        }]
        
        result = await agent.generate_order_intents({
            "allocation_decisions": allocation_decisions,
            "default_asset": "SPY",
            "order_type": "market"
        })
        
        assert result["total_intents"] == 1
        assert len(result["order_intents"]) == 1


class TestExecutionSimulation:
    """Test execution simulation."""
    
    @pytest.mark.asyncio
    async def test_order_executes(self):
        """Test that order executes in simulation."""
        agent = ExecutionIntelligenceAgent("Test Agent", execution_mode="simulation")
        
        order_intents = [{
            "order_intent_id": f"intent_{uuid.uuid4().hex[:8]}",
            "asset": "SPY",
            "side": "buy",
            "quantity": 100,
            "order_type": "market",
            "strategy_id": "test_strategy"
        }]
        
        orders_result = await agent.generate_orders({
            "order_intents": order_intents
        })
        
        assert orders_result["total_orders"] == 1
        
        execution_result = await agent.simulate_execution({
            "orders": orders_result["orders"]
        })
        
        assert execution_result["orders_executed"] == 1
        assert len(execution_result["fill_reports"]) == 1
        assert execution_result["fill_reports"][0]["status"] == "filled"


class TestConstraintEnforcement:
    """Test constraint enforcement."""
    
    def test_max_leverage_enforced(self):
        """Test that max leverage is enforced."""
        engine = PortfolioConstraintEngine(PortfolioConstraintSet(max_portfolio_leverage=2.0))
        
        strategy = ApprovedStrategy(
            strategy_id="test_strategy",
            pipeline_run_id="test_pipeline",
            approval_status="approved",
            signal_payload={"asset": "SPY"},
            sharpe_ratio=1.5,
            max_drawdown=0.1
        )
        
        portfolio = PortfolioState(
            allocated_capital=75000,
            cash_available=50000,
            leverage=2.5
        )
        
        allocation = AllocationDecision(
            strategy_id="test_strategy",
            target_weight=0.5,
            leverage=2.5
        )
        
        all_passed, results = engine.check_all_constraints(strategy, allocation, portfolio)
        
        leverage_result = [r for r in results if r.constraint_name == "max_portfolio_leverage"][0]
        
        assert leverage_result.passed is False


class TestEndToEnd:
    """End-to-end capital deployment tests."""
    
    @pytest.mark.asyncio
    async def test_full_pipeline(self):
        """Test full capital deployment pipeline."""
        portfolio_agent = PortfolioIntelligenceAgent("Portfolio Agent", initial_capital=100000)
        execution_agent = ExecutionIntelligenceAgent("Execution Agent", execution_mode="simulation")
        
        strategy_data = {
            "strategy_id": "e2e_strategy",
            "pipeline_run_id": "e2e_pipeline",
            "approval_status": "approved",
            "signal_payload": {"asset": "SPY", "signal": "buy"},
            "sharpe_ratio": 1.5,
            "max_drawdown": 0.1,
            "expected_return": 0.15,
            "regime_score": 0.7,
            "confidence": 0.85
        }
        
        # Validate
        validation = await portfolio_agent.validate_strategy_for_allocation({
            "strategy": strategy_data
        })
        assert validation["is_valid"] is True
        
        # Position size
        position = await portfolio_agent.calculate_position_size({
            "strategy": strategy_data,
            "target_weight": 0.1
        })
        assert position["target_notional"] > 0
        
        # Generate intents
        intents = await portfolio_agent.generate_order_intents({
            "allocation_decisions": [{
                "strategy_id": strategy_data["strategy_id"],
                "approved": True,
                "target_weight": position["target_weight"],
                "target_notional": position["target_notional"]
            }],
            "default_asset": "SPY"
        })
        assert intents["total_intents"] > 0
        
        # Generate orders
        orders = await execution_agent.generate_orders({
            "order_intents": intents["order_intents"]
        })
        assert orders["total_orders"] > 0
        
        # Execute
        execution = await execution_agent.simulate_execution({
            "orders": orders["orders"]
        })
        assert execution["orders_executed"] > 0
        assert len(execution["fill_reports"]) > 0


class TestExecutionAdapter:
    """Test execution adapters."""
    
    @pytest.mark.asyncio
    async def test_simulated_adapter_fills(self):
        """Test simulated execution adapter."""
        adapter = SimulatedExecutionAdapter(slippage_bps=5.0, commission=0.001)
        
        order = ExecutionOrder(
            order_intent_id="test_intent",
            asset="SPY",
            side="buy",
            quantity=100,
            order_type="market"
        )
        
        result = await adapter.submit_order(order)
        
        assert result.status == "filled"
        
        fills = adapter.get_fills(order.order_id)
        assert len(fills) > 0
        assert fills[0].filled_quantity == 100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
