"""
Combined Equity and Options Trading Simulation

AFIE Autonomous Financial Intelligence Engine
Directive 015 - SPY Options Alpha Engine

Combines equity mean-reversion strategies with options strategies.

Author: AFIE Engineering System
"""

import asyncio
import random
import math
from datetime import datetime
from typing import Dict, Any, List
import uuid

from strategies.options import (
    OptionsChain,
    OptionsPortfolio,
    OptionsStrategyManager,
    OptionGreeks
)
from deployment.institutional_validation_fixed import PaperPortfolioV1


class CombinedPortfolio:
    """
    Combined Equity + Options Portfolio.
    
    Manages both equity and options positions.
    """
    
    def __init__(
        self,
        initial_capital: float = 100000.0,
        max_drawdown: float = 0.12,
        max_daily_loss: float = 0.02,
        max_equity_allocation: float = 0.70,
        max_options_allocation: float = 0.30,
        simulation_days: int = 252
    ):
        # Configuration
        self.initial_capital = initial_capital
        self.simulation_days = simulation_days
        self.max_drawdown = max_drawdown
        self.max_daily_loss = max_daily_loss
        self.max_equity_allocation = max_equity_allocation
        self.max_options_allocation = max_options_allocation
        
        # Paper trading mode
        self.paper_trading = True
        self.live_trading = False
        
        # Equity portfolio (from previous implementation)
        self.equity_portfolio = PaperPortfolioV1(
            initial_capital=initial_capital * max_equity_allocation,
            max_drawdown=max_drawdown,
            max_daily_loss=max_daily_loss,
            max_position_size=0.10,
            max_strategy_allocation=0.30,
            simulation_days=simulation_days
        )
        
        # Options components
        self.options_chain = OptionsChain(
            underlying="SPY",
            spot_price=450.0,
            volatility=0.20
        )
        self.options_portfolio = OptionsPortfolio()
        self.options_manager = OptionsStrategyManager()
        
        # Combined cash
        self.cash = initial_capital * max_options_allocation  # Cash for options
        self.equity_cash = initial_capital * max_equity_allocation  # Cash for equity
        
        # Tracking
        self.current_day = 0
        self.current_spy_price = 450.0
        
        # PnL tracking
        self.realized_pnl = 0.0
        self.unrealized_pnl = 0.0
        self.commission_total = 0.0
        
        # Strategy PnL tracking
        self.strategy_pnl: Dict[str, float] = {}
        
        # Trade ledger
        self.trade_ledger: List[Dict[str, Any]] = []
        
        # Metrics
        self.daily_pnl: List[float] = []
        self.equity_curve: List[float] = []
        self.peak_value = initial_capital
        
        # Initialize strategy PnL
        for sid in ["MR_001", "MR_003", "MR_002"]:
            self.strategy_pnl[sid] = 0.0
        for sid in ["OPT_VS_001", "OPT_CS_001", "OPT_IC_001", "OPT_VB_001"]:
            self.strategy_pnl[sid] = 0.0
    
    def get_total_equity(self) -> float:
        """Get total portfolio equity."""
        # Equity: cash allocated + unrealized
        equity_positions_value = sum(
            pos["quantity"] * self.current_spy_price 
            for pos in self.equity_portfolio.strategy_positions.values()
        )
        equity_val = self.equity_cash + equity_positions_value
        
        # Options: cash + unrealized
        options_positions_value = self._calculate_options_mtm()
        options_val = self.cash + options_positions_value
        
        return equity_val + options_val
    
    def _calculate_options_mtm(self) -> float:
        """Calculate options mark-to-market value."""
        total = 0.0
        
        for symbol, pos in self.options_portfolio.get_positions().items():
            # Get current price
            price = self.options_chain.get_option_price(
                pos["strike"], pos["expiration"], pos["option_type"]
            )
            total += price * pos["quantity"] * 100
        
        return total
    
    def execute_equity_trade(
        self,
        strategy_id: str,
        side: str,
        quantity: int,
        price: float
    ) -> Dict[str, Any]:
        """Execute equity trade."""
        return self.equity_portfolio.execute_trade(strategy_id, side, quantity, price)
    
    def execute_options_trade(
        self,
        signal: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute options trade."""
        symbol = f"SPY_{signal['expiration']}_{signal['option_type'][0].upper()}{int(signal['strike'])}"
        
        # Get current option price
        option_price = self.options_chain.get_option_price(
            signal["strike"], signal["expiration"], signal["option_type"]
        )
        
        # Calculate cost
        cost = option_price * signal["quantity"] * 100  # x100 shares per contract
        commission = signal["quantity"] * 0.50  # $0.50 per contract
        
        if signal["action"] == "buy":
            if self.cash < cost + commission:
                return {"success": False, "reason": "Insufficient cash"}
            
            self.cash -= (cost + commission)
            self.commission_total += commission
            
            # Get greeks
            greeks = self.options_chain.get_option_greeks(
                signal["strike"], signal["expiration"], signal["option_type"]
            )
            
            # Add position
            self.options_portfolio.add_position(
                symbol, signal["option_type"], signal["strike"],
                signal["expiration"], signal["quantity"], option_price, greeks
            )
            
            # Record trade
            trade = {
                "trade_id": str(uuid.uuid4()),
                "type": "options",
                "strategy_id": signal["strategy_id"],
                "symbol": symbol,
                "side": "buy",
                "quantity": signal["quantity"],
                "strike": signal["strike"],
                "expiration": signal["expiration"],
                "entry_price": option_price,
                "pnl": 0,
                "commission": commission,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        else:  # sell
            # Close existing position
            exit_price = self.options_chain.get_option_price(
                signal["strike"], signal["expiration"], signal["option_type"]
            )
            
            pnl = self.options_portfolio.close_position(
                symbol, signal["quantity"], exit_price,
                OptionGreeks()
            )
            
            self.cash += (exit_price * signal["quantity"] * 100 - commission)
            self.commission_total += commission
            
            # Record PnL
            self.realized_pnl += pnl
            if signal["strategy_id"] not in self.strategy_pnl:
                self.strategy_pnl[signal["strategy_id"]] = 0.0
            self.strategy_pnl[signal["strategy_id"]] += pnl
            
            # Record trade
            trade = {
                "trade_id": str(uuid.uuid4()),
                "type": "options",
                "strategy_id": signal["strategy_id"],
                "symbol": symbol,
                "side": "sell",
                "quantity": signal["quantity"],
                "strike": signal["strike"],
                "expiration": signal["expiration"],
                "entry_price": 0,  # Would need to track entry
                "exit_price": exit_price,
                "pnl": pnl,
                "commission": commission,
                "timestamp": datetime.utcnow().isoformat()
            }
        
        self.trade_ledger.append(trade)
        
        return {"success": True, "trade": trade}
    
    def update_prices(self) -> None:
        """Update SPY and options prices."""
        # Random walk for SPY
        daily_return = random.gauss(0.0002, 0.005)
        self.current_spy_price *= (1 + daily_return)
        self.current_spy_price = max(100, min(1000, self.current_spy_price))
        
        # Update options chain
        self.options_chain.update_spot(self.current_spy_price)
        
        # Randomly adjust volatility
        vol_change = random.gauss(0, 0.01)
        new_vol = max(0.10, min(0.50, self.options_chain.volatility + vol_change))
        self.options_chain.update_volatility(new_vol)
    
    def check_expiration(self) -> List[Dict[str, Any]]:
        """Check for options expiring soon and close them."""
        from datetime import datetime
        
        expiring = []
        today = datetime.now()
        
        for symbol, pos in list(self.options_portfolio.get_positions().items()):
            exp_date = datetime.strptime(pos["expiration"], "%Y-%m-%d")
            days_until = (exp_date - today).days
            
            if days_until <= 2:
                # Close position
                exit_price = self.options_chain.get_option_price(
                    pos["strike"], pos["expiration"], pos["option_type"]
                )
                
                pnl = self.options_portfolio.close_position(
                    symbol, pos["quantity"], exit_price, OptionGreeks()
                )
                
                self.realized_pnl += pnl
                self.strategy_pnl[pos.get("strategy_id", "UNKNOWN")] += pnl
                
                expiring.append({
                    "symbol": symbol,
                    "days_until": days_until,
                    "pnl": pnl
                })
        
        return expiring
    
    def get_monitoring_data(self) -> Dict[str, Any]:
        """Get monitoring data."""
        equity_value = self.equity_portfolio.get_equity()
        options_exposure = self.options_portfolio.get_total_exposure()
        
        return {
            "total_equity": self.get_total_equity(),
            "equity_value": equity_value,
            "cash": self.cash,
            "realized_pnl": self.realized_pnl,
            "unrealized_pnl": self._calculate_options_mtm(),
            "options_positions": len(self.options_portfolio.get_positions()),
            "options_exposure": options_exposure,
            "daily_pnl": self.daily_pnl[-1] if self.daily_pnl else 0,
            "strategy_pnl": self.strategy_pnl
        }
    
    def run_simulation(self) -> Dict[str, Any]:
        """Run the combined simulation."""
        print(f"\n{'='*70}")
        print(f"COMBINED EQUITY + OPTIONS SIMULATION - {self.simulation_days} Days")
        print(f"Initial Capital: ${self.initial_capital:,.2f}")
        print(f"Equity Allocation: {self.max_equity_allocation:.0%}")
        print(f"Options Allocation: {self.max_options_allocation:.0%}")
        print(f"{'='*70}\n")
        
        # Initialize equity portfolio
        self.equity_portfolio.register_strategies()
        
        for day in range(1, self.simulation_days + 1):
            self.current_day = day
            
            # ===== EQUITY TRADING =====
            # Run equity strategies
            signals = asyncio.run(self.equity_portfolio.generate_signals())
            equity_trades = asyncio.run(self.equity_portfolio.process_signals(signals))
            
            # Track equity PnL
            for trade in equity_trades:
                if trade["side"] == "sell":
                    self.realized_pnl += trade.get("net_pnl", 0)
                    self.strategy_pnl[trade["strategy_id"]] = self.strategy_pnl.get(trade["strategy_id"], 0) + trade.get("net_pnl", 0)
            
            # ===== OPTIONS TRADING =====
            # Generate options signals
            options_signals = self.options_manager.generate_all_signals(
                day, self.options_chain, self.cash
            )
            
            # Execute options trades
            for signal in options_signals:
                if signal["action"] == "sell":
                    # Close existing position - need to track entry
                    result = self.execute_options_trade(signal)
            
            # Check for expiring options
            expiring = self.check_expiration()
            
            # Update prices
            self.update_prices()
            
            # Record daily PnL
            equity_pnl = self.equity_portfolio.realized_pnl
            daily_pnl = equity_pnl - sum(self.daily_pnl) if self.daily_pnl else equity_pnl
            self.daily_pnl.append(daily_pnl)
            
            # Equity curve
            total_equity = self.get_total_equity()
            self.equity_curve.append(total_equity)
            
            # Update peak
            if total_equity > self.peak_value:
                self.peak_value = total_equity
            
            # Check drawdown
            drawdown = (self.peak_value - total_equity) / self.peak_value if self.peak_value > 0 else 0
            
            if drawdown > self.max_drawdown:
                print(f"\n⚠️ KILL SWITCH: Drawdown {drawdown:.1%} exceeds limit")
                break
            
            if day % 50 == 0:
                print(f"Day {day}: Equity ${total_equity:,.2f}, Daily PnL: ${daily_pnl:,.2f}, Drawdown: {drawdown:.1%}")
        
        return self.generate_report()
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate combined performance report."""
        
        final_equity = self.get_total_equity()
        total_return = final_equity - self.initial_capital
        total_return_pct = total_return / self.initial_capital
        
        # Calculate metrics
        if self.daily_pnl:
            avg_daily = sum(self.daily_pnl) / len(self.daily_pnl)
            std_daily = (sum((p - avg_daily) ** 2 for p in self.daily_pnl) / len(self.daily_pnl)) ** 0.5
            sharpe = (avg_daily / std_daily * (252 ** 0.5)) if std_daily > 0 else 0
        else:
            sharpe = 0
        
        # Max drawdown
        max_dd = 0
        peak = self.initial_capital
        for equity in self.equity_curve:
            if equity > peak:
                peak = equity
            dd = (peak - equity) / peak if peak > 0 else 0
            max_dd = max(max_dd, dd)
        
        # Win rate
        closed_trades = [t for t in self.trade_ledger if t.get("side") == "sell"]
        winning = len([t for t in closed_trades if t.get("pnl", 0) > 0])
        win_rate = winning / len(closed_trades) if closed_trades else 0
        
        # Profit factor
        gross_profit = sum(t["pnl"] for t in closed_trades if t.get("pnl", 0) > 0)
        gross_loss = abs(sum(t["pnl"] for t in closed_trades if t.get("pnl", 0) < 0))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        # Options exposure
        options_exposure = self.options_portfolio.get_total_exposure()
        
        report = {
            "simulation_days": self.current_day,
            "initial_capital": self.initial_capital,
            "final_equity": final_equity,
            "total_return": total_return,
            "total_return_pct": total_return_pct,
            "sharpe_ratio": sharpe,
            "max_drawdown": max_dd,
            "trade_count": len(closed_trades),
            "win_rate": win_rate,
            "profit_factor": profit_factor,
            
            # Breakdown
            "equity_pnl": self.equity_portfolio.realized_pnl,
            "options_pnl": self.realized_pnl,
            "commission_total": self.commission_total,
            
            # Options metrics
            "options_exposure": options_exposure,
            
            # Strategy PnL
            "strategy_pnl": self.strategy_pnl
        }
        
        # Print report
        print(f"\n{'='*70}")
        print("COMBINED PORTFOLIO PERFORMANCE REPORT")
        print(f"{'='*70}")
        print(f"\n--- SUMMARY ---")
        print(f"Simulation Days: {report['simulation_days']}")
        print(f"Initial Capital: ${report['initial_capital']:,.2f}")
        print(f"Final Equity: ${report['final_equity']:,.2f}")
        print(f"Total Return: ${report['total_return']:,.2f} ({report['total_return_pct']:.2%})")
        print(f"Sharpe Ratio: {report['sharpe_ratio']:.2f}")
        print(f"Max Drawdown: {report['max_drawdown']:.2%}")
        print(f"Trade Count: {report['trade_count']}")
        print(f"Win Rate: {report['win_rate']:.2%}")
        
        print(f"\n--- PnL BREAKDOWN ---")
        print(f"Equity PnL: ${report['equity_pnl']:,.2f}")
        print(f"Options PnL: ${report['options_pnl']:,.2f}")
        print(f"Commissions: ${report['commission_total']:,.2f}")
        
        print(f"\n--- OPTIONS EXPOSURE ---")
        print(f"Delta: {options_exposure.get('Delta', 0):.2f}")
        print(f"Gamma: {options_exposure.get('gamma', 0):.4f}")
        print(f"Theta: {options_exposure.get('theta', 0):.2f}")
        print(f"Vega: {options_exposure.get('vega', 0):.2f}")
        
        print(f"\n--- STRATEGY PnL ---")
        for sid, pnl in self.strategy_pnl.items():
            print(f"  {sid}: ${pnl:,.2f}")
        
        print(f"\n{'='*70}\n")
        
        return report


if __name__ == "__main__":
    portfolio = CombinedPortfolio(
        initial_capital=100000.0,
        max_drawdown=0.12,
        max_daily_loss=0.02,
        max_equity_allocation=0.70,
        max_options_allocation=0.30,
        simulation_days=252
    )
    
    report = portfolio.run_simulation()
    
    print("\n✅ Combined Simulation Complete!")
    print(f"Final Equity: ${report['final_equity']:,.2f}")
    print(f"Return: {report['total_return_pct']:.2%}")
