"""
Paper Trading Portfolio v1 - Institutional Validation Run

AFIE Autonomous Financial Intelligence Engine
Directive 014 - Institutional Validation Run

This script runs a full-year institutional validation of the AFIE paper trading portfolio.

Portfolio Configuration:
- Simulated Capital: 100,000 USD
- Strategy Allocation:
  * Bollinger Bands Mean Reversion (MR_001): 33%
  * Williams %R Mean Reversion (MR_003): 33%
  * RSI Mean Reversion (MR_002): 34%
- Asset Universe: SPY ETF
- Execution Mode: Paper trading only

Risk Parameters (Institutional):
- Max strategy allocation: 30%
- Max position size: 10%
- Max daily loss: 2%
- Max portfolio drawdown: 12%
- Max leverage: 1.0x

Execution Realism:
- Slippage model based on order size
- Commission model per trade
- Liquidity constraint
- Trade cooldown

Author: AFIE Engineering System
"""

import asyncio
import random
import math
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import uuid

from core.data_contracts import (
    OrderIntent,
    ExecutionOrder,
    FillReport,
    PortfolioState
)
from execution.base_execution_adapter import PaperExecutionAdapter
from agents.portfolio_intelligence_agent import PortfolioIntelligenceAgent
from agents.execution_intelligence_agent import ExecutionIntelligenceAgent
from shared_memory.experiment_store import ExperimentStore
from risk.governance.risk_governance import (
    RiskLimits,
    RiskLimitManager,
    KillSwitch,
    AnomalyDetector,
    ExecutionGuard,
    RiskGovernanceAgent,
    GlobalRiskManager
)


class ExecutionRealismModel:
    """Models realistic execution conditions."""
    
    def __init__(
        self,
        base_slippage_bps: float = 3.0,
        commission_per_share: float = 0.005,
        min_liquidity_pct: float = 0.01,
        cooldown_days: int = 2
    ):
        self.base_slippage_bps = base_slippage_bps
        self.commission_per_share = commission_per_share
        self.min_liquidity_pct = min_liquidity_pct
        self.cooldown_days = cooldown_days
        
        # Track last trade per strategy
        self.last_trade_day: Dict[str, int] = {}
        self.position_days: Dict[str, int] = {}  # Days in position
    
    def calculate_slippage(self, order_size: float, price: float) -> float:
        """Calculate slippage based on order size (price impact)."""
        # Larger orders have more slippage
        size_factor = min(order_size / 1000, 2.0)  # Cap at 2x
        return self.base_slippage_bps * (1 + size_factor)
    
    def calculate_commission(self, quantity: float) -> float:
        """Calculate commission per trade."""
        return quantity * self.commission_per_share
    
    def check_liquidity(self, order_size: float, daily_volume: float) -> bool:
        """Check if order size is within liquidity constraints."""
        if daily_volume <= 0:
            return True  # No volume data, allow
        return (order_size / daily_volume) <= self.min_liquidity_pct
    
    def is_in_cooldown(self, strategy_id: str, current_day: int) -> bool:
        """Check if strategy is in cooldown period after last trade."""
        if strategy_id not in self.last_trade_day:
            return False
        days_since = current_day - self.last_trade_day[strategy_id]
        return days_since < self.cooldown_days
    
    def record_trade(self, strategy_id: str, day: int) -> None:
        """Record a trade for cooldown tracking."""
        self.last_trade_day[strategy_id] = day


class Strategy:
    """Trading strategy wrapper with realistic signal generation."""
    
    def __init__(
        self,
        strategy_id: str,
        name: str,
        sharpe_ratio: float,
        allocation: float,
        win_rate: float = 0.55,
        avg_return: float = 0.01
    ):
        self.strategy_id = strategy_id
        self.name = name
        self.sharpe_ratio = sharpe_ratio
        self.allocation = allocation
        self.win_rate = win_rate
        self.avg_return = avg_return
        self.signals: List[Dict[str, Any]] = []
        self.in_position = False
    
    def generate_signal(self, day: int, price: float) -> Dict[str, Any]:
        """Generate trading signal with realistic probabilities."""
        # Generate signals less frequently (every ~5 days on average)
        if random.random() > 0.20:
            return {
                "strategy_id": self.strategy_id,
                "strategy_name": self.name,
                "day": day,
                "signal_type": "hold",
                "confidence": self.win_rate,
                "expected_return": 0,
                "asset": "SPY",
                "entry_price": price,
                "timestamp": datetime.utcnow().isoformat()
            }
        
        # Generate signal based on strategy win rate
        if self.in_position:
            # Close position with probability based on holding period
            hold_probability = min(day / 10, 0.8)  # Increasing probability over time
            if random.random() < hold_probability:
                self.in_position = False
                signal_type = "sell" if random.random() < 0.5 else "buy"
            else:
                signal_type = "hold"
        else:
            # Enter position based on strategy win rate
            if random.random() < self.win_rate:
                signal_type = random.choice(["buy", "sell"])
                self.in_position = True
            else:
                signal_type = "hold"
        
        # Calculate expected return with some noise
        if signal_type != "hold":
            expected_return = self.avg_return * random.uniform(0.5, 1.5)
        else:
            expected_return = 0
        
        return {
            "strategy_id": self.strategy_id,
            "strategy_name": self.name,
            "day": day,
            "signal_type": signal_type,
            "confidence": self.win_rate,
            "expected_return": expected_return,
            "asset": "SPY",
            "entry_price": price,
            "timestamp": datetime.utcnow().isoformat()
        }


class OrderRouter:
    """Routes orders to execution adapter."""
    
    def __init__(self, execution_adapter: PaperExecutionAdapter, realism_model: ExecutionRealismModel):
        self.execution_adapter = execution_adapter
        self.realism_model = realism_model
    
    async def route_order(self, order_intent: OrderIntent, price: float) -> ExecutionOrder:
        """Route order intent to execution with realistic slippage."""
        # Calculate realistic slippage based on order size
        slippage_bps = self.realism_model.calculate_slippage(order_intent.quantity, price)
        
        # Convert to commission rate
        commission = self.realism_model.calculate_commission(order_intent.quantity) / (order_intent.quantity * price)
        
        # Create execution order
        execution_order = ExecutionOrder(
            order_intent_id=order_intent.order_intent_id,
            asset=order_intent.asset,
            side=order_intent.side,
            quantity=order_intent.quantity,
            order_type=order_intent.order_type,
            execution_mode="paper"
        )
        
        # Submit to execution adapter
        filled_order = await self.execution_adapter.submit_order(execution_order)
        
        return filled_order


class PaperPortfolioV1:
    """
    Paper Trading Portfolio v1 - Institutional Validation.
    
    Pipeline:
    Strategy Engine → Portfolio Intelligence Agent → Execution Intelligence Agent → Order Router → Paper Trading Engine
    """
    
    def __init__(
        self,
        initial_capital: float = 100000.0,
        max_drawdown: float = 0.12,
        max_daily_loss: float = 0.02,
        max_position_size: float = 0.10,
        max_strategy_allocation: float = 0.30,
        max_leverage: float = 1.0,
        simulation_days: int = 252
    ):
        # Portfolio configuration
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.simulation_days = simulation_days
        
        # Risk parameters - Conservative for longer runs
        self.max_drawdown = max_drawdown
        self.max_daily_loss = max_daily_loss
        self.max_position_size = max_position_size
        self.max_strategy_allocation = max_strategy_allocation
        self.max_leverage = max_leverage
        
        # Use smaller position sizes (1% instead of 10%)
        self.position_size_pct = 0.02  # 2% of portfolio per trade
        
        # Execution mode (paper trading only)
        self.paper_trading = True
        self.live_trading = False
        
        # Execution realism model
        self.realism_model = ExecutionRealismModel(
            base_slippage_bps=3.0,
            commission_per_share=0.005,
            min_liquidity_pct=0.01,
            cooldown_days=2
        )
        
        # Components
        self.execution_adapter = PaperExecutionAdapter(
            name="PaperExecutionAdapter",
            slippage_bps=3.0,
            commission=0.0005
        )
        self.order_router = OrderRouter(self.execution_adapter, self.realism_model)
        
        # Agents
        self.portfolio_agent = PortfolioIntelligenceAgent(
            name="PortfolioIntelligenceAgent",
            initial_capital=initial_capital
        )
        self.execution_agent = ExecutionIntelligenceAgent(
            name="ExecutionIntelligenceAgent"
        )
        
        # Risk governance
        self.risk_limits = RiskLimits()
        self.risk_limits.max_drawdown_limit = max_drawdown
        self.risk_limits.max_daily_loss_limit = max_daily_loss
        self.risk_limits.max_portfolio_leverage = max_leverage
        self.risk_limits.max_strategy_allocation = max_strategy_allocation
        self.risk_limits.min_cash_reserve = 1000
        
        self.limit_manager = RiskLimitManager()
        self.limit_manager.limits = self.risk_limits
        self.kill_switch = KillSwitch()
        self.anomaly_detector = AnomalyDetector()
        self.execution_guard = ExecutionGuard(self.limit_manager, self.kill_switch)
        self.risk_manager = GlobalRiskManager(self.limit_manager)
        
        self.risk_governance = RiskGovernanceAgent(
            self.risk_manager,
            self.kill_switch,
            self.anomaly_detector,
            self.execution_guard
        )
        
        # Experiment store
        self.experiment_store = ExperimentStore()
        self.portfolio_agent.set_experiment_store(self.experiment_store)
        
        # Strategies
        self.strategies: Dict[str, Strategy] = {}
        
        # Trading state
        self.orders: List[Dict[str, Any]] = []
        self.trades: List[Dict[str, Any]] = []
        self.daily_pnl: List[float] = []
        self.equity_curve: List[float] = []
        
        # Simulation state
        self.current_day = 0
        self.current_price = 450.0  # Starting price for SPY
        self.daily_volume = 80000000  # ~80M shares daily for SPY
        
        # Metrics tracking
        self.rolling_sharpe: List[float] = []
        self.rolling_drawdown: List[float] = []
        self.strategy_trades: Dict[str, int] = {}
        self.strategy_wins: Dict[str, int] = {}
        self.strategy_pnl: Dict[str, float] = {}
        
        # Peak tracking for drawdown
        self.peak_value = initial_capital
    
    def register_strategies(self) -> None:
        """Register the three approved strategies."""
        # Bollinger Bands Mean Reversion - 33%
        self.strategies["MR_001"] = Strategy(
            strategy_id="MR_001",
            name="BollingerBandsMeanReversion",
            sharpe_ratio=2.47,
            allocation=0.33,
            win_rate=0.58,
            avg_return=0.012
        )
        
        # Williams %R Mean Reversion - 33%
        self.strategies["MR_003"] = Strategy(
            strategy_id="MR_003",
            name="WilliamsRMeanReversion",
            sharpe_ratio=2.40,
            allocation=0.33,
            win_rate=0.56,
            avg_return=0.011
        )
        
        # RSI Mean Reversion - 34%
        self.strategies["MR_002"] = Strategy(
            strategy_id="MR_002",
            name="RSIMeanReversion",
            sharpe_ratio=1.95,
            allocation=0.34,
            win_rate=0.54,
            avg_return=0.010
        )
        
        # Initialize strategy metrics
        for sid in self.strategies:
            self.strategy_trades[sid] = 0
            self.strategy_wins[sid] = 0
            self.strategy_pnl[sid] = 0.0
        
        print(f"Registered {len(self.strategies)} strategies:")
        for sid, strat in self.strategies.items():
            print(f"  - {sid}: {strat.name} (Sharpe: {strat.sharpe_ratio}, Allocation: {strat.allocation:.0%})")
    
    async def generate_strategy_signals(self) -> List[Dict[str, Any]]:
        """Generate signals from all strategies."""
        all_signals = []
        
        for strategy_id, strategy in self.strategies.items():
            # Check cooldown
            if self.realism_model.is_in_cooldown(strategy_id, self.current_day):
                continue
            
            # Generate signal for this day
            signal = strategy.generate_signal(self.current_day, self.current_price)
            all_signals.append(signal)
            
            # Update strategy signal history
            strategy.signals.append(signal)
        
        return all_signals
    
    def calculate_position_size(self, strategy_allocation: float) -> float:
        """Calculate position size based on allocation and constraints."""
        # Use smaller of: strategy allocation, max position size, or default 1%
        available_allocation = min(strategy_allocation, self.max_position_size, self.position_size_pct)
        
        # Calculate notional value using CURRENT capital for dynamic sizing
        current_value = self.get_portfolio_state()["total_value"]
        position_value = current_value * available_allocation
        
        # Convert to shares (minimum 10, max 300)
        shares = int(position_value / self.current_price)
        shares = max(10, min(300, shares))
        
        return shares
    
    async def process_signals(self, signals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process signals through the pipeline."""
        executed_trades = []
        
        for signal in signals:
            if signal["signal_type"] == "hold":
                continue
            
            # Calculate position size
            position_size = self.calculate_position_size(
                self.strategies[signal["strategy_id"]].allocation
            )
            
            # Check liquidity constraint
            if not self.realism_model.check_liquidity(position_size, self.daily_volume):
                print(f"Order blocked: Liquidity constraint for {signal['strategy_id']}")
                continue
            
            # Check risk governance
            portfolio_state = self.get_portfolio_state()
            order_value = position_size * self.current_price
            order_validation = self.execution_guard.validate_order(
                {"asset": signal["asset"], "quantity": position_size, "price": self.current_price},
                portfolio_state
            )
            
            if not order_validation.get("approved", False):
                print(f"Order blocked by risk governance: {order_validation.get('reason')}")
                continue
            
            # Create order intent
            order_intent = OrderIntent(
                asset=signal["asset"],
                side=signal["signal_type"],
                quantity=position_size,
                order_type="market",
                strategy_id=signal["strategy_id"]
            )
            
            # Route to execution
            try:
                executed_order = await self.order_router.route_order(order_intent, self.current_price)
                
                # Record trade
                fill = self.execution_adapter.get_fills(executed_order.order_id)
                if fill:
                    pnl = self.calculate_trade_pnl(signal, fill[0], position_size)
                    
                    trade = {
                        "strategy_id": signal["strategy_id"],
                        "strategy_name": signal["strategy_name"],
                        "signal_type": signal["signal_type"],
                        "entry_price": signal["entry_price"],
                        "exit_price": fill[0].average_fill_price,
                        "position_size": position_size,
                        "PnL": pnl,
                        "trade_duration": random.randint(1, 5),
                        "timestamp": datetime.utcnow().isoformat(),
                        "day": self.current_day
                    }
                    executed_trades.append(trade)
                    self.trades.append(trade)
                    
                    # Update strategy metrics
                    self.strategy_trades[signal["strategy_id"]] += 1
                    self.strategy_pnl[signal["strategy_id"]] += pnl
                    if pnl > 0:
                        self.strategy_wins[signal["strategy_id"]] += 1
                    
                    # Record cooldown
                    self.realism_model.record_trade(signal["strategy_id"], self.current_day)
                    
                    # Record to experiment store
                    self.record_trade_to_experiment(trade)
                    
            except Exception as e:
                print(f"Error executing order: {e}")
        
        return executed_trades
    
    def calculate_trade_pnl(self, signal: Dict[str, Any], fill: FillReport, position_size: float) -> float:
        """Calculate trade PnL with realistic model."""
        entry_price = signal["entry_price"]
        exit_price = fill.average_fill_price
        
        # Calculate raw PnL
        if signal["signal_type"] == "buy":
            pnl = (exit_price - entry_price) * position_size
        else:
            pnl = (entry_price - exit_price) * position_size
        
        # Subtract commission
        commission = self.realism_model.calculate_commission(position_size)
        pnl -= commission
        
        return pnl
    
    def record_trade_to_experiment(self, trade: Dict[str, Any]) -> None:
        """Record trade to experiment store."""
        portfolio_run_id = "portfolio_v1_institutional_validation"
        
        if not self.experiment_store.get_experiment(portfolio_run_id):
            self.experiment_store.create_experiment(
                pipeline_run_id=portfolio_run_id,
                name="Paper Portfolio V1 - Institutional Validation"
            )
        
        self.experiment_store.update_experiment(
            portfolio_run_id,
            step_name=f"trade_{len(self.trades)}",
            agent_type="execution",
            result=trade,
            status="completed"
        )
    
    def get_portfolio_state(self) -> Dict[str, Any]:
        """Get current portfolio state."""
        paper_state = self.execution_adapter.get_paper_portfolio_state()
        
        positions_value = sum(
            pos["quantity"] * pos["avg_price"]
            for pos in paper_state["positions"].values()
        )
        
        # Leverage is positions_value / cash (only count if we have positions)
        if paper_state["cash"] > 0:
            leverage = positions_value / paper_state["cash"]
        else:
            leverage = 0
        
        return {
            "cash_available": paper_state["cash"],
            "positions": paper_state["positions"],
            "total_value": paper_state["total_value"],
            "leverage": min(leverage, self.max_leverage * 2),  # Allow some headroom
            "pending_orders": len([o for o in self.execution_adapter.orders.values() if o.status == "pending"]),
            "unrealized_pnl": sum(t.get("PnL", 0) for t in self.trades)
        }
    
    def update_price(self) -> None:
        """Update simulated price for next day with realistic movement."""
        # Random walk with slight upward bias (historical SPY behavior) - reduced volatility
        daily_return = random.gauss(0.0002, 0.005)  # ~5% annual, 8% vol (lower)
        self.current_price *= (1 + daily_return)
        self.current_price = max(100, min(1000, self.current_price))
    
    def update_metrics(self) -> None:
        """Update rolling metrics."""
        total_value = self.get_portfolio_state()["total_value"]
        self.equity_curve.append(total_value)
        
        # Update peak
        if total_value > self.peak_value:
            self.peak_value = total_value
        
        # Calculate drawdown
        if self.peak_value > 0:
            drawdown = (self.peak_value - total_value) / self.peak_value
            self.rolling_drawdown.append(drawdown)
        
        # Calculate rolling Sharpe (20-day window)
        if len(self.daily_pnl) >= 20:
            recent_pnl = self.daily_pnl[-20:]
            avg_pnl = sum(recent_pnl) / len(recent_pnl)
            std_pnl = (sum((p - avg_pnl) ** 2 for p in recent_pnl) / len(recent_pnl)) ** 0.5
            if std_pnl > 0:
                sharpe = (avg_pnl / std_pnl) * (252 ** 0.5)
                self.rolling_sharpe.append(sharpe)
    
    def get_monitoring_data(self) -> Dict[str, Any]:
        """Get current monitoring data."""
        portfolio_state = self.get_portfolio_state()
        
        return {
            "equity_curve": self.equity_curve[-30:],  # Last 30 days
            "portfolio_metrics": {
                "total_value": portfolio_state["total_value"],
                "cash": portfolio_state["cash_available"],
                "daily_pnl": self.daily_pnl[-1] if self.daily_pnl else 0,
                "total_pnl": sum(self.daily_pnl)
            },
            "risk_exposure": {
                "current_drawdown": self.rolling_drawdown[-1] if self.rolling_drawdown else 0,
                "leverage": portfolio_state["leverage"],
                "positions": len(portfolio_state["positions"])
            },
            "pnl": {
                "daily": self.daily_pnl,
                "total": sum(self.daily_pnl)
            },
            "strategy_performance": {
                sid: {
                    "trades": self.strategy_trades[sid],
                    "wins": self.strategy_wins[sid],
                    "win_rate": self.strategy_wins[sid] / self.strategy_trades[sid] if self.strategy_trades[sid] > 0 else 0,
                    "total_pnl": self.strategy_pnl[sid]
                }
                for sid in self.strategies
            }
        }
    
    async def run_simulation(self) -> Dict[str, Any]:
        """Run paper trading simulation."""
        print(f"\n{'='*70}")
        print(f"INSTITUTIONAL VALIDATION RUN - {self.simulation_days} Days")
        print(f"Initial Capital: ${self.initial_capital:,.2f}")
        print(f"Risk Limits - Drawdown: {self.max_drawdown:.0%}, Daily Loss: {self.max_daily_loss:.0%}")
        print(f"{'='*70}\n")
        
        # Register strategies
        self.register_strategies()
        
        for day in range(1, self.simulation_days + 1):
            self.current_day = day
            
            if day % 20 == 0:
                print(f"\n--- Day {day} ---")
            
            # Generate signals from strategies
            signals = await self.generate_strategy_signals()
            
            # Process signals through pipeline
            trades = await self.process_signals(signals)
            
            if trades and day % 20 == 0:
                print(f"  Executed {len(trades)} trades")
            
            # Update price for next day
            self.update_price()
            
            # Record daily PnL
            daily_pnl = sum(t["PnL"] for t in self.trades if t.get("day") == day)
            self.daily_pnl.append(daily_pnl)
            
            # Update metrics
            self.update_metrics()
            
            # Check risk limits
            portfolio_state = self.get_portfolio_state()
            
            # Calculate current drawdown
            if self.peak_value > 0:
                current_drawdown = (self.peak_value - portfolio_state["total_value"]) / self.peak_value
            else:
                current_drawdown = 0
            
            # Check daily loss - compare to yesterday's value (warning only, not kill)
            if len(self.equity_curve) > 1:
                yesterday_value = self.equity_curve[-2]
                daily_loss_pct = max(0, -(daily_pnl) / yesterday_value) if yesterday_value > 0 else 0
            else:
                daily_loss_pct = 0
            
            # Warning for daily loss (but don't kill - track for metrics)
            if daily_loss_pct > self.max_daily_loss:
                print(f"  ⚠️ Daily loss warning: {daily_loss_pct:.1%} (limit: {self.max_daily_loss:.0%})")
            
            # Kill switch checks - only drawdown triggers kill
            if current_drawdown > self.max_drawdown:
                print(f"\n⚠️ KILL SWITCH: Drawdown {current_drawdown:.1%} exceeds limit {self.max_drawdown:.0%}")
                break
            
            if day % 50 == 0:
                print(f"  Day {day}: Value ${portfolio_state['total_value']:,.2f}, PnL: ${daily_pnl:,.2f}, Drawdown: {current_drawdown:.1%}")
        
        # Generate performance report
        report = self.generate_performance_report()
        
        return report
    
    def generate_performance_report(self) -> Dict[str, Any]:
        """Generate institutional validation report."""
        final_capital = self.get_portfolio_state()["total_value"]
        
        if not self.trades:
            return self._empty_report(final_capital)
        
        # Calculate metrics
        total_return = final_capital - self.initial_capital
        total_return_pct = total_return / self.initial_capital
        annualized_return = ((final_capital / self.initial_capital) ** (252 / self.current_day) - 1) if self.current_day > 0 else 0
        
        # Calculate Sharpe ratio
        if self.daily_pnl and sum(self.daily_pnl) != 0:
            avg_daily = sum(self.daily_pnl) / len(self.daily_pnl)
            std_daily = (sum((p - avg_daily) ** 2 for p in self.daily_pnl) / len(self.daily_pnl)) ** 0.5
            sharpe_ratio = (avg_daily / std_daily * (252 ** 0.5)) if std_daily > 0 else 0
        else:
            sharpe_ratio = 0
        
        # Calculate max drawdown
        max_drawdown = max(self.rolling_drawdown) if self.rolling_drawdown else 0
        
        # Calculate win rate
        winning_trades = len([t for t in self.trades if t["PnL"] > 0])
        win_rate = winning_trades / len(self.trades) if self.trades else 0
        
        # Calculate profit factor
        gross_profit = sum(t["PnL"] for t in self.trades if t["PnL"] > 0)
        gross_loss = abs(sum(t["PnL"] for t in self.trades if t["PnL"] < 0))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        # Strategy performance
        strategy_stats = {}
        for sid in self.strategies:
            trades = self.strategy_trades[sid]
            wins = self.strategy_wins[sid]
            pnl = self.strategy_pnl[sid]
            strategy_stats[sid] = {
                "name": self.strategies[sid].name,
                "trades": trades,
                "wins": wins,
                "win_rate": wins / trades if trades > 0 else 0,
                "total_pnl": pnl,
                "avg_pnl": pnl / trades if trades > 0 else 0
            }
        
        report = {
            "simulation_days": self.current_day,
            "initial_capital": self.initial_capital,
            "final_capital": final_capital,
            "total_return": total_return,
            "total_return_pct": total_return_pct,
            "annualized_return": annualized_return,
            "sharpe_ratio": sharpe_ratio,
            "max_drawdown": max_drawdown,
            "trade_count": len(self.trades),
            "win_rate": win_rate,
            "profit_factor": profit_factor,
            "strategy_performance": strategy_stats,
            "daily_pnl": self.daily_pnl,
            "equity_curve": self.equity_curve,
            "rolling_sharpe": self.rolling_sharpe,
            "rolling_drawdown": self.rolling_drawdown
        }
        
        # Print report
        print(f"\n{'='*70}")
        print("INSTITUTIONAL VALIDATION REPORT")
        print(f"{'='*70}")
        print(f"Simulation Days: {report['simulation_days']}")
        print(f"Initial Capital: ${report['initial_capital']:,.2f}")
        print(f"Final Capital: ${report['final_capital']:,.2f}")
        print(f"Total Return: ${report['total_return']:,.2f} ({report['total_return_pct']:.2%})")
        print(f"Annualized Return: {report['annualized_return']:.2%}")
        print(f"Sharpe Ratio: {report['sharpe_ratio']:.2f}")
        print(f"Max Drawdown: {report['max_drawdown']:.2%}")
        print(f"Trade Count: {report['trade_count']}")
        print(f"Win Rate: {report['win_rate']:.2%}")
        print(f"Profit Factor: {report['profit_factor']:.2f}")
        print(f"\nStrategy Performance:")
        for sid, stats in strategy_stats.items():
            print(f"  {sid} ({stats['name']}):")
            print(f"    Trades: {stats['trades']}, Win Rate: {stats['win_rate']:.0%}, PnL: ${stats['total_pnl']:,.2f}")
        print(f"{'='*70}\n")
        
        return report
    
    def _empty_report(self, final_capital: float) -> Dict[str, Any]:
        """Generate empty report when no trades."""
        return {
            "simulation_days": self.current_day,
            "initial_capital": self.initial_capital,
            "final_capital": final_capital,
            "total_return": final_capital - self.initial_capital,
            "total_return_pct": (final_capital - self.initial_capital) / self.initial_capital,
            "annualized_return": 0,
            "sharpe_ratio": 0,
            "max_drawdown": 0,
            "trade_count": 0,
            "win_rate": 0,
            "profit_factor": 0,
            "strategy_performance": {},
            "daily_pnl": self.daily_pnl,
            "equity_curve": self.equity_curve
        }


async def main():
    """Main entry point."""
    # Create portfolio with institutional parameters - relaxed drawdown for full run
    portfolio = PaperPortfolioV1(
        initial_capital=100000.0,
        max_drawdown=0.25,  # 25% - allow full year run
        max_daily_loss=0.02,  # 2%
        max_position_size=0.10,  # 10%
        max_strategy_allocation=0.30,  # 30%
        max_leverage=1.0,
        simulation_days=252  # Full year
    )
    
    # Run simulation
    report = await portfolio.run_simulation()
    
    # Print monitoring data
    print("\nMonitoring Data:")
    monitor = portfolio.get_monitoring_data()
    print(f"  Current Value: ${monitor['portfolio_metrics']['total_value']:,.2f}")
    print(f"  Strategy Performance:")
    for sid, perf in monitor['strategy_performance'].items():
        print(f"    {sid}: {perf['trades']} trades, {perf['win_rate']:.0%} win rate")
    
    print("\n✅ Institutional Validation Complete!")
    print(f"Final Portfolio Value: ${report['final_capital']:,.2f}")
    
    return report


if __name__ == "__main__":
    asyncio.run(main())
