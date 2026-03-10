"""Risk Governance Workflows for AFC3."""
import asyncio
import sys
sys.path.insert(0, '.')

from risk.governance.risk_governance import (
    RiskLimitManager, GlobalRiskManager, KillSwitch,
    AnomalyDetector, ExecutionGuard, RiskGovernanceAgent
)

async def workflow_s():
    """Workflow S - Risk Limit Violation"""
    print("="*50)
    print("WORKFLOW S: Risk Limit Violation")
    print("="*50)
    
    # Setup
    limit_manager = RiskLimitManager()
    kill_switch = KillSwitch()
    anomaly_detector = AnomalyDetector()
    execution_guard = ExecutionGuard(limit_manager, kill_switch)
    
    risk_manager = GlobalRiskManager(limit_manager)
    agent = RiskGovernanceAgent(risk_manager, kill_switch, anomaly_detector, execution_guard)
    
    # Portfolio with high leverage
    portfolio = {"leverage": 2.5, "cash_available": 50000, "unrealized_pnl": -2000}
    positions = [{"strategy_weight": 0.35, "weight": 0.35}]
    
    print("\n[1/2] Evaluating risk...")
    result = await agent.evaluate_risk(portfolio, positions)
    
    print(f"  Kill switch active: {result['kill_switch_active']}")
    print(f"  Violations: {result['limit_violations']}")
    
    # Try to validate order
    print("\n[2/2] Validating order...")
    order = {"quantity": 100, "price": 50}
    validation = agent.validate_order(order, portfolio)
    print(f"  Order approved: {validation['approved']}")
    print(f"  Reason: {validation.get('reason', 'N/A')}")
    
    return {"status": "success", "violations": result['limit_violations']}

async def workflow_t():
    """Workflow T - Drawdown Breach"""
    print("="*50)
    print("WORKFLOW T: Drawdown Breach")
    print("="*50)
    
    limit_manager = RiskLimitManager()
    kill_switch = KillSwitch()
    anomaly_detector = AnomalyDetector()
    execution_guard = ExecutionGuard(limit_manager, kill_switch)
    risk_manager = GlobalRiskManager(limit_manager)
    agent = RiskGovernanceAgent(risk_manager, kill_switch, anomaly_detector, execution_guard)
    
    # Portfolio with large drawdown
    portfolio = {"leverage": 1.0, "cash_available": 100000, "unrealized_pnl": -25000}
    positions = []
    
    print("\n[1/1] Triggering kill switch...")
    result = await agent.evaluate_risk(portfolio, positions)
    
    print(f"  Kill switch: {result['kill_switch_active']}")
    print(f"  Reason: {result['limit_violations']}")
    
    return {"status": "success", "kill_switch": result['kill_switch_active']}

async def workflow_u():
    """Workflow U - Execution Guard"""
    print("="*50)
    print("WORKFLOW U: Execution Guard")
    print("="*50)
    
    limit_manager = RiskLimitManager()
    kill_switch = KillSwitch()
    anomaly_detector = AnomalyDetector()
    execution_guard = ExecutionGuard(limit_manager, kill_switch)
    risk_manager = GlobalRiskManager(limit_manager)
    agent = RiskGovernanceAgent(risk_manager, kill_switch, anomaly_detector, execution_guard)
    
    # Normal portfolio
    portfolio = {"leverage": 1.0, "cash_available": 50000, "pending_orders": 5}
    
    # Valid order
    print("\n[1/2] Validating valid order...")
    valid_order = {"quantity": 10, "price": 100}
    result = agent.validate_order(valid_order, portfolio)
    print(f"  Approved: {result['approved']}")
    
    # Invalid order (exceeds cash)
    print("\n[2/2] Validating invalid order...")
    invalid_order = {"quantity": 1000, "price": 100}
    result = agent.validate_order(invalid_order, portfolio)
    print(f"  Approved: {result['approved']}")
    print(f"  Reason: {result.get('reason', 'N/A')}")
    
    return {"status": "success"}

async def main():
    print("Risk Governance Workflows")
    print("="*50)
    
    result_s = await workflow_s()
    print(f"\nResult S: {result_s['status']}")
    
    result_t = await workflow_t()
    print(f"\nResult T: {result_t['status']}")
    
    result_u = await workflow_u()
    print(f"\nResult U: {result_u['status']}")
    
    print("\n" + "="*50)
    print("Risk workflows complete!")

if __name__ == "__main__":
    asyncio.run(main())
