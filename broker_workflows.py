"""Broker Integration Workflows for AFC3."""
import asyncio
import sys
sys.path.insert(0, '.')

from brokers.broker_interface import (
    create_broker_adapter, PaperTradingEngine, OrderRouter
)
from risk.governance.risk_governance import RiskLimitManager, KillSwitch, ExecutionGuard

async def workflow_v():
    """Workflow V - Paper Trading"""
    print("="*50)
    print("WORKFLOW V: Paper Trading")
    print("="*50)
    
    # Setup broker
    broker = create_broker_adapter("ib", mode="paper")
    
    print("\n[1/4] Connecting to broker...")
    await broker.connect()
    print(f"  Connected: {broker.is_connected()}")
    
    print("\n[2/4] Getting market data...")
    data = await broker.get_market_data("AAPL")
    print(f"  AAPL: ${data['bid']:.2f} / ${data['ask']:.2f}")
    
    print("\n[3/4] Submitting paper order...")
    from brokers.broker_interface import BrokerOrder, OrderSide
    order = BrokerOrder(order_id="1", symbol="AAPL", side=OrderSide.BUY.value,
                      quantity=100, order_type="market")
    result = await broker.submit_order(order)
    print(f"  Order: {result.status}, Filled: ${result.average_fill_price:.2f}")
    
    print("\n[4/4] Getting account state...")
    account = await broker.get_account_state()
    print(f"  Equity: ${account.equity:.2f}")
    
    await broker.disconnect()
    return {"status": "success"}

async def workflow_w():
    """Workflow W - Broker Connectivity"""
    print("="*50)
    print("WORKFLOW W: Broker Connectivity")
    print("="*50)
    
    # Test IB
    print("\n[1/2] Testing Interactive Brokers...")
    ib = create_broker_adapter("ib")
    await ib.connect()
    print(f"  Connected: {ib.is_connected()}")
    
    positions = await ib.get_positions()
    print(f"  Positions: {len(positions)}")
    
    await ib.disconnect()
    print("  Disconnected")
    
    # Test Schwab
    print("\n[2/2] Testing Schwab...")
    schwab = create_broker_adapter("schwab")
    await schwab.connect()
    print(f"  Connected: {schwab.is_connected()}")
    
    await schwab.disconnect()
    print("  Disconnected")
    
    return {"status": "success"}

async def workflow_x():
    """Workflow X - Risk Governance with Broker"""
    print("="*50)
    print("WORKFLOW X: Risk Governance")
    print("="*50)
    
    # Setup risk
    limit_manager = RiskLimitManager()
    kill_switch = KillSwitch()
    execution_guard = ExecutionGuard(limit_manager, kill_switch)
    
    # Setup broker
    broker = create_broker_adapter("ib", mode="paper")
    await broker.connect()
    
    print("\n[1/3] Testing valid order...")
    portfolio = {"cash_available": 50000, "leverage": 1.0, "pending_orders": 5}
    order = {"quantity": 10, "price": 150}
    result = execution_guard.validate_order(order, portfolio)
    print(f"  Valid order: {result['approved']}")
    
    print("\n[2/3] Triggering kill switch...")
    kill_switch.trigger("Test kill switch")
    result = execution_guard.validate_order(order, portfolio)
    print(f"  Order blocked: {not result['approved']}")
    print(f"  Reason: {result.get('reason')}")
    
    print("\n[3/3] Testing order with insufficient cash...")
    kill_switch.reset()
    portfolio_low = {"cash_available": 100, "leverage": 1.0}
    order_large = {"quantity": 10000, "price": 100}
    result = execution_guard.validate_order(order_large, portfolio_low)
    print(f"  Blocked: {not result['approved']}")
    print(f"  Reason: {result.get('reason')}")
    
    await broker.disconnect()
    return {"status": "success"}

async def main():
    print("Broker Integration Workflows")
    print("="*50)
    
    result_v = await workflow_v()
    print(f"\nResult V: {result_v['status']}")
    
    result_w = await workflow_w()
    print(f"\nResult W: {result_w['status']}")
    
    result_x = await workflow_x()
    print(f"\nResult X: {result_x['status']}")
    
    print("\n" + "="*50)
    print("Broker workflows complete!")

if __name__ == "__main__":
    asyncio.run(main())
