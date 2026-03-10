"""
SPY Options Alpha Engine Simulation

AFIE Autonomous Financial Intelligence Engine
Directive 015 - SPY Options Alpha Engine

Simulates options trading on SPY using multiple strategies.

Author: AFIE Engineering System
"""

import random
import math
from datetime import datetime
from typing import Dict, Any, List


class BlackScholes:
    """Black-Scholes options pricing."""
    
    @staticmethod
    def norm_cdf(x):
        return 0.5 * (1 + math.erf(x / math.sqrt(2)))
    
    @staticmethod
    def norm_pdf(x):
        return math.exp(-0.5 * x * x) / math.sqrt(2 * math.pi)
    
    @staticmethod
    def call_price(S, K, T, r, sigma):
        if T <= 0:
            return max(0, S - K)
        d1 = (math.log(S/K) + (r + 0.5*sigma**2)*T) / (sigma*math.sqrt(T))
        d2 = d1 - sigma*math.sqrt(T)
        return S * BlackScholes.norm_cdf(d1) - K * math.exp(-r*T) * BlackScholes.norm_cdf(d2)
    
    @staticmethod
    def put_price(S, K, T, r, sigma):
        if T <= 0:
            return max(0, K - S)
        d1 = (math.log(S/K) + (r + 0.5*sigma**2)*T) / (sigma*math.sqrt(T))
        d2 = d1 - sigma*math.sqrt(T)
        return K * math.exp(-r*T) * BlackScholes.norm_cdf(-d2) - S * BlackScholes.norm_cdf(-d1)
    
    @staticmethod
    def greeks(S, K, T, r, sigma, opt_type):
        if T <= 0:
            return {"delta": 0, "gamma": 0, "theta": 0, "vega": 0}
        
        d1 = (math.log(S/K) + (r + 0.5*sigma**2)*T) / (sigma*math.sqrt(T))
        d2 = d1 - sigma*math.sqrt(T)
        sqrt_T = math.sqrt(T)
        
        nd1 = BlackScholes.norm_pdf(d1)
        
        if opt_type == "call":
            delta = BlackScholes.norm_cdf(d1)
            theta = (-S*nd1*sigma/(2*sqrt_T) - r*K*math.exp(-r*T)*BlackScholes.norm_cdf(d2)) / 365
        else:
            delta = BlackScholes.norm_cdf(d1) - 1
            theta = (-S*nd1*sigma/(2*sqrt_T) + r*K*math.exp(-r*T)*BlackScholes.norm_cdf(-d2)) / 365
        
        gamma = nd1 / (S * sigma * sqrt_T)
        vega = S * sqrt_T * nd1 / 100
        
        return {"delta": delta, "gamma": gamma, "theta": theta, "vega": vega}


class OptionsStrategy:
    """Base options strategy."""
    
    def __init__(self, strategy_id, name):
        self.strategy_id = strategy_id
        self.name = name
    
    def generate_signal(self, day, spot, vol, expiry_days):
        return None


class VerticalSpread(OptionsStrategy):
    """Bull/Bear vertical spreads."""
    
    def __init__(self):
        super().__init__("OPT_VS", "VerticalSpread")
    
    def generate_signal(self, day, spot, vol, expiry_days):
        if random.random() > 0.15:
            return None
        
        # Simple bull call spread
        direction = random.choice(["bull", "bear"])
        K1 = spot * random.uniform(0.97, 1.03)
        K2 = K1 * (1.05 if direction == "bull" else 0.95)
        
        return {
            "strategy_id": self.strategy_id,
            "type": "vertical_spread",
            "direction": direction,
            "legs": [
                {"action": "buy", "strike": K1, "opt_type": "call"},
                {"action": "sell", "strike": K2, "opt_type": "call" if direction == "bull" else "put"}
            ],
            "expiry_days": random.randint(14, 45)
        }


class IronCondor(OptionsStrategy):
    """Iron condor strategy."""
    
    def __init__(self):
        super().__init__("OPT_IC", "IronCondor")
    
    def generate_signal(self, day, spot, vol, expiry_days):
        if vol > 0.25 or random.random() > 0.08:
            return None
        
        return {
            "strategy_id": self.strategy_id,
            "type": "iron_condor",
            "legs": [
                {"action": "buy", "strike": spot * 1.05, "opt_type": "call"},
                {"action": "sell", "strike": spot * 1.02, "opt_type": "call"},
                {"action": "sell", "strike": spot * 0.98, "opt_type": "put"},
                {"action": "buy", "strike": spot * 0.95, "opt_type": "put"}
            ],
            "expiry_days": random.randint(21, 45)
        }


class VolatilityBreakout(OptionsStrategy):
    """Long straddle/strangle."""
    
    def __init__(self):
        super().__init__("OPT_VB", "VolatilityBreakout")
        self.last_signal_day = -30
    
    def generate_signal(self, day, spot, vol, expiry_days):
        if day - self.last_signal_day < 20:
            return None
        
        if random.random() > 0.05:
            return None
        
        self.last_signal_day = day
        
        return {
            "strategy_id": self.strategy_id,
            "type": "straddle",
            "legs": [
                {"action": "buy", "strike": spot, "opt_type": "call"},
                {"action": "buy", "strike": spot, "opt_type": "put"}
            ],
            "expiry_days": random.randint(14, 30)
        }


class OptionsPortfolio:
    """Options trading portfolio."""
    
    def __init__(
        self,
        initial_capital=100000,
        max_drawdown=0.12,
        max_options_exposure=0.30,
        simulation_days=252
    ):
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.max_drawdown = max_drawdown
        self.max_options_exposure = max_options_exposure
        self.simulation_days = simulation_days
        
        # Market
        self.spot = 450.0
        self.vol = 0.20
        self.r = 0.05
        self.bs = BlackScholes()
        
        # Strategies
        self.strategies = [VerticalSpread(), IronCondor(), VolatilityBreakout()]
        
        # Positions: {symbol: {strike, opt_type, quantity, entry_price, side}}
        self.positions = {}
        
        # Tracking
        self.daily_pnl = []
        self.equity_curve = []
        self.peak = initial_capital
        self.realized_pnl = 0
        self.commission = 0
        
        # Strategy PnL
        self.strategy_pnl = {s.strategy_id: 0 for s in self.strategies}
        
        # Trade log
        self.trades = []
    
    def execute_leg(self, leg, action, expiry_days):
        """Execute a single option leg."""
        K = leg["strike"]
        opt_type = leg["opt_type"]
        
        T = expiry_days / 252
        if opt_type == "call":
            price = self.bs.call_price(self.spot, K, T, self.r, self.vol)
        else:
            price = self.bs.put_price(self.spot, K, T, self.r, self.vol)
        
        cost = price * 100  # per contract
        qty = leg.get("quantity", 1) * (1 if action == "buy" else -1)
        comm = 0.50
        
        # Check cash
        total_cost = abs(qty) * cost + comm
        if action == "buy" and total_cost > self.cash:
            return None
        
        if action == "buy":
            self.cash -= total_cost
        else:
            self.cash += cost * abs(qty) - comm
        
        self.commission += comm
        
        # Create position
        symbol = f"{opt_type[0].upper()}{int(K)}"
        
        if action == "buy":
            self.positions[symbol] = {
                "strike": K,
                "opt_type": opt_type,
                "quantity": qty,
                "entry_price": price,
                "expiry_days": expiry_days
            }
        else:
            # Close position
            if symbol in self.positions:
                pnl = (price - self.positions[symbol]["entry_price"]) * abs(qty) * 100
                self.realized_pnl += pnl
                del self.positions[symbol]
                return pnl
        
        return 0
    
    def mark_to_market(self):
        """Calculate unrealized PnL."""
        total = 0
        for symbol, pos in self.positions.items():
            K = pos["strike"]
            opt_type = pos["opt_type"]
            T = max(pos["expiry_days"], 1) / 252
            
            if opt_type == "call":
                price = self.bs.call_price(self.spot, K, T, self.r, self.vol)
            else:
                price = self.bs.put_price(self.spot, K, T, self.r, self.vol)
            
            total += (price - pos["entry_price"]) * pos["quantity"] * 100
        
        return total
    
    def get_equity(self):
        """Get total equity."""
        return self.cash + self.mark_to_market() + self.realized_pnl
    
    def update_market(self):
        """Update market conditions."""
        # Random walk
        self.spot *= (1 + random.gauss(0.0002, 0.008))
        self.spot = max(200, min(800, self.spot))
        
        # Vol mean reversion
        self.vol += random.gauss(0, 0.005)
        self.vol = max(0.10, min(0.60, self.vol))
    
    def close_expiring(self):
        """Close positions near expiration."""
        closed = []
        for symbol, pos in list(self.positions.items()):
            if pos["expiry_days"] <= 2:
                K = pos["strike"]
                opt_type = pos["opt_type"]
                T = 1 / 252
                
                if opt_type == "call":
                    price = self.bs.call_price(self.spot, K, T, self.r, self.vol)
                else:
                    price = self.bs.put_price(self.spot, K, T, self.r, self.vol)
                
                pnl = (price - pos["entry_price"]) * pos["quantity"] * 100
                self.realized_pnl += pnl
                self.cash += price * abs(pos["quantity"]) * 100
                closed.append(symbol)
                
                for s in self.strategies:
                    if s.strategy_id in symbol:
                        self.strategy_pnl[s.strategy_id] += pnl
        
        for s in closed:
            del self.positions[s]
        
        return closed
    
    def run(self):
        """Run simulation."""
        print(f"\n{'='*60}")
        print(f"OPTIONS ALPHA SIMULATION - {self.simulation_days} Days")
        print(f"Initial Capital: ${self.initial_capital:,.2f}")
        print(f"{'='*60}\n")
        
        for day in range(1, self.simulation_days + 1):
            # Generate signals
            for strategy in self.strategies:
                signal = strategy.generate_signal(day, self.spot, self.vol, 30)
                
                if signal:
                    # Execute legs
                    pnl = 0
                    for leg in signal.get("legs", []):
                        result = self.execute_leg(
                            leg, leg["action"], signal.get("expiry_days", 30)
                        )
                        if result:
                            pnl += result
                    
                    if pnl != 0:
                        self.strategy_pnl[signal["strategy_id"]] += pnl
            
            # Update positions
            for pos in self.positions.values():
                pos["expiry_days"] -= 1
            
            # Close expiring
            self.close_expiring()
            
            # Update market
            self.update_market()
            
            # Track equity
            equity = self.get_equity()
            self.equity_curve.append(equity)
            
            # Daily PnL
            if len(self.equity_curve) > 1:
                daily = equity - self.equity_curve[-2]
            else:
                daily = 0
            self.daily_pnl.append(daily)
            
            # Peak
            if equity > self.peak:
                self.peak = equity
            
            # Drawdown check
            dd = (self.peak - equity) / self.peak
            if dd > self.max_drawdown:
                print(f"\n⚠️ KILL SWITCH: Drawdown {dd:.1%}")
                break
            
            if day % 50 == 0:
                print(f"Day {day}: Equity ${equity:,.2f}, Vol: {self.vol:.1%}, Positions: {len(self.positions)}")
        
        return self.report()
    
    def report(self):
        """Generate report."""
        equity = self.get_equity()
        ret = (equity - self.initial_capital) / self.initial_capital
        
        # Metrics
        if self.daily_pnl:
            avg = sum(self.daily_pnl) / len(self.daily_pnl)
            std = (sum((p-avg)**2 for p in self.daily_pnl) / len(self.daily_pnl)) ** 0.5
            sharpe = (avg/std * 252**0.5) if std else 0
        else:
            sharpe = 0
        
        # Drawdown
        max_dd = 0
        peak = self.initial_capital
        for e in self.equity_curve:
            if e > peak:
                peak = e
            dd = (peak - e) / peak
            max_dd = max(max_dd, dd)
        
        # Win rate
        pnl_trades = [p for p in self.daily_pnl if p != 0]
        wins = len([p for p in pnl_trades if p > 0])
        win_rate = wins / len(pnl_trades) if pnl_trades else 0
        
        # Greeks
        total_delta = sum(
            self.bs.greeks(self.spot, p["strike"], max(p["expiry_days"],1)/252, self.r, self.vol, p["opt_type"])["delta"] * p["quantity"]
            for p in self.positions.values()
        )
        
        print(f"\n{'='*60}")
        print("OPTIONS STRATEGY PERFORMANCE REPORT")
        print(f"{'='*60}")
        print(f"Days: {len(self.equity_curve)}")
        print(f"Initial: ${self.initial_capital:,.2f}")
        print(f"Final: ${equity:,.2f}")
        print(f"Return: {ret:.2%}")
        print(f"Sharpe: {sharpe:.2f}")
        print(f"Max DD: {max_dd:.2%}")
        print(f"Win Rate: {win_rate:.0%}")
        print(f"\nStrategy PnL:")
        for sid, pnl in self.strategy_pnl.items():
            print(f"  {sid}: ${pnl:,.2f}")
        print(f"\nOptions Greek Exposure:")
        print(f"  Delta: {total_delta:.2f}")
        print(f"  Vol: {self.vol:.1%}")
        print(f"  Positions: {len(self.positions)}")
        print(f"{'='*60}\n")
        
        return {
            "days": len(self.equity_curve),
            "initial": self.initial_capital,
            "final": equity,
            "return": ret,
            "sharpe": sharpe,
            "max_dd": max_dd,
            "win_rate": win_rate,
            "strategy_pnl": self.strategy_pnl,
            "positions": len(self.positions)
        }


if __name__ == "__main__":
    portfolio = OptionsPortfolio(
        initial_capital=100000,
        max_drawdown=0.25,  # Higher for options
        simulation_days=252
    )
    
    report = portfolio.run()
    
    print(f"\n✅ Options Alpha Engine Complete!")
    print(f"Final: ${report['final']:,.2f}, Return: {report['return']:.2%}")
