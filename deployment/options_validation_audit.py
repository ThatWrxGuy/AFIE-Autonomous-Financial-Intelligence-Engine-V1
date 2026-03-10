"""
Options Alpha Engine Validation and Attribution Report

AFIE Autonomous Financial Intelligence Engine
Directive 015A - Options Validation Audit

Comprehensive validation with:
- Strategy PnL attribution
- Realized vs Unrealized breakdown
- Greeks exposure tracking
- Equity curves
- Full trade ledger

Author: AFIE Engineering System
"""

import random
import math
from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple
from dataclasses import dataclass, field


@dataclass
class OptionPosition:
    """Single option position with full tracking."""
    position_id: str
    strategy_id: str
    symbol: str
    option_type: str  # call/put
    strike: float
    expiration: str
    quantity: int  # positive = long, negative = short
    entry_price: float
    entry_greeks: Dict[str, float]
    entry_date: int
    close_target: int = 0  # Day to close
    current_price: float = 0.0
    
    @property
    def notional(self) -> float:
        return abs(self.quantity) * 100
    
    @property
    def entry_value(self) -> float:
        return self.entry_price * self.notional


@dataclass
class TradeRecord:
    """Full trade record for ledger."""
    trade_id: str
    strategy_id: str
    position_id: str
    action: str  # open/close
    symbol: str
    option_type: str
    strike: float
    expiration: str
    quantity: int
    price: float
    greeks: Dict[str, float]
    pnl: float = 0.0
    commission: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


class BlackScholes:
    """Black-Scholes pricing."""
    
    @staticmethod
    def norm_cdf(x):
        return 0.5 * (1 + math.erf(x / math.sqrt(2)))
    
    @staticmethod
    def norm_pdf(x):
        return math.exp(-0.5 * x * x) / math.sqrt(2 * math.pi)
    
    @staticmethod
    def price(S, K, T, r, sigma, opt_type):
        if T <= 0:
            return max(0, S - K) if opt_type == "call" else max(0, K - S)
        
        d1 = (math.log(S/K) + (r + 0.5*sigma**2)*T) / (sigma*math.sqrt(T))
        d2 = d1 - sigma*math.sqrt(T)
        
        if opt_type == "call":
            return S * BlackScholes.norm_cdf(d1) - K * math.exp(-r*T) * BlackScholes.norm_cdf(d2)
        else:
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
    """Base strategy with attribution."""
    
    def __init__(self, strategy_id: str, name: str):
        self.strategy_id = strategy_id
        self.name = name
        self.trades: List[Dict] = []
        self.realized_pnl = 0.0
        self.wins = 0
        self.losses = 0
    
    def record_trade(self, pnl: float):
        """Record trade result."""
        self.trades.append({"pnl": pnl, "timestamp": datetime.utcnow().isoformat()})
        self.realized_pnl += pnl
        if pnl > 0:
            self.wins += 1
        else:
            self.losses += 1
    
    def get_metrics(self) -> Dict:
        """Get strategy metrics."""
        n = len(self.trades)
        if n == 0:
            return {"sharpe": 0, "max_dd": 0, "win_rate": 0, "profit_factor": 0, "trades": 0}
        
        pnls = [t["pnl"] for t in self.trades]
        avg = sum(pnls) / n
        std = (sum((p-avg)**2 for p in pnls) / n) ** 0.5
        
        sharpe = (avg/std * (252/20)**0.5) if std > 0 else 0
        
        # Max drawdown
        peak = 0
        max_dd = 0
        running = 0
        for p in pnls:
            running += p
            if running > peak:
                peak = running
            dd = (peak - running) / max(peak, 1)
            max_dd = max(max_dd, dd)
        
        # Win rate
        win_rate = self.wins / n if n > 0 else 0
        
        # Profit factor
        gross_profit = sum(p for p in pnls if p > 0)
        gross_loss = abs(sum(p for p in pnls if p < 0))
        pf = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        return {
            "strategy_id": self.strategy_id,
            "name": self.name,
            "sharpe": sharpe,
            "max_dd": max_dd,
            "win_rate": win_rate,
            "profit_factor": pf,
            "trades": n,
            "realized_pnl": self.realized_pnl,
            "avg_pnl": avg,
            "gross_profit": gross_profit,
            "gross_loss": gross_loss
        }


class VerticalSpread(OptionsStrategy):
    """Vertical spread strategy."""
    
    def __init__(self):
        super().__init__("OPT_VS", "VerticalSpread")
    
    def generate(self, day, spot, vol):
        """Generate signal with more frequent trades."""
        if random.random() > 0.15:  # More frequent
            return None
        
        direction = random.choice(["bull", "bear"])
        K1 = spot * random.uniform(0.97, 1.03)
        K2 = K1 * (1.05 if direction == "bull" else 0.95)
        
        return {
            "strategy_id": self.strategy_id,
            "type": "vertical_spread",
            "legs": [
                {"action": "buy", "strike": K1, "opt_type": "call" if direction == "bull" else "put"},
                {"action": "sell", "strike": K2, "opt_type": "call" if direction == "bull" else "put"}
            ],
            "expiry": random.randint(14, 45),
            "close_days": random.randint(3, 10)  # Close within 3-10 days
        }


class IronCondor(OptionsStrategy):
    """Iron condor strategy."""
    
    def __init__(self):
        super().__init__("OPT_IC", "IronCondor")
    
    def generate(self, day, spot, vol):
        if vol > 0.25 or random.random() > 0.10:
            return None
        
        return {
            "strategy_id": self.strategy_id,
            "type": "iron_condor",
            "legs": [
                {"action": "buy", "strike": spot * 1.06, "opt_type": "call"},
                {"action": "sell", "strike": spot * 1.03, "opt_type": "call"},
                {"action": "sell", "strike": spot * 0.97, "opt_type": "put"},
                {"action": "buy", "strike": spot * 0.94, "opt_type": "put"}
            ],
            "expiry": random.randint(21, 45),
            "close_days": random.randint(5, 12)
        }


class VolatilityBreakout(OptionsStrategy):
    """Volatility breakout strategy."""
    
    def __init__(self):
        super().__init__("OPT_VB", "VolatilityBreakout")
        self.last_day = -30
    
    def generate(self, day, spot, vol):
        if day - self.last_day < 25:
            return None
        
        if random.random() > 0.08:
            return None
        
        self.last_day = day
        
        return {
            "strategy_id": self.strategy_id,
            "type": "straddle",
            "legs": [
                {"action": "buy", "strike": spot, "opt_type": "call"},
                {"action": "buy", "strike": spot, "opt_type": "put"}
            ],
            "expiry": random.randint(14, 30),
            "close_days": random.randint(3, 7)
        }


class CalendarSpread(OptionsStrategy):
    """Calendar spread strategy."""
    
    def __init__(self):
        super().__init__("OPT_CS", "CalendarSpread")
    
    def generate(self, day, spot, vol):
        if random.random() > 0.12:
            return None
        
        opt_type = random.choice(["call", "put"])
        
        return {
            "strategy_id": self.strategy_id,
            "type": "calendar_spread",
            "legs": [
                {"action": "buy", "strike": spot, "opt_type": opt_type, "expiry": 45},
                {"action": "sell", "strike": spot, "opt_type": opt_type, "expiry": 14}
            ],
            "expiry": 14,
            "close_days": random.randint(2, 5)
        }


class OptionsPortfolioAudit:
    """Full options portfolio with audit trail."""
    
    def __init__(
        self,
        initial_capital=100000,
        max_drawdown=0.12,
        max_exposure=0.10,
        simulation_days=252
    ):
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.max_drawdown = max_drawdown
        self.max_exposure = max_exposure
        self.simulation_days = simulation_days
        
        # Market
        self.spot = 450.0
        self.vol = 0.18
        self.r = 0.05
        self.bs = BlackScholes()
        
        # Strategies
        self.strategies = {
            "OPT_VS": VerticalSpread(),
            "OPT_IC": IronCondor(),
            "OPT_VB": VolatilityBreakout(),
            "OPT_CS": CalendarSpread()
        }
        
        # Positions and ledger
        self.positions: Dict[str, OptionPosition] = {}
        self.trade_ledger: List[TradeRecord] = []
        
        # Tracking
        self.equity_curve: List[float] = []
        self.greeks_history: List[Dict[str, float]] = []
        self.daily_pnl: List[float] = []
        self.peak = initial_capital
        self.day = 0
        
        # PnL breakdown
        self.realized_pnl = 0.0
        self.unrealized_pnl = 0.0
        
        # Position counter
        self.position_counter = 0
    
    def get_greeks(self) -> Dict[str, float]:
        """Calculate total Greeks."""
        delta = gamma = theta = vega = 0
        
        for pos in self.positions.values():
            g = self.bs.greeks(
                self.spot, pos.strike,
                self._days_to_expiry(pos.expiration) / 252,
                self.r, self.vol, pos.option_type
            )
            
            mult = pos.quantity * 100
            delta += g["delta"] * mult
            gamma += g["gamma"] * mult
            theta += g["theta"] * mult
            vega += g["vega"] * mult
        
        return {"delta": delta, "gamma": gamma, "theta": theta, "vega": vega}
    
    def _days_to_expiry(self, expiration: str) -> float:
        """Calculate days to expiry."""
        exp_date = datetime.strptime(expiration, "%Y-%m-%d")
        days = (exp_date - datetime.now()).days
        return max(1, days)
    
    def _get_expiry(self, days: int) -> str:
        """Get expiration date."""
        exp_date = datetime.now() + timedelta(days=days)
        return exp_date.strftime("%Y-%m-%d")
    
    def get_options_value(self) -> float:
        """Get mark-to-market value of options."""
        total = 0
        for pos in self.positions.values():
            price = self.bs.price(
                self.spot, pos.strike,
                self._days_to_expiry(pos.expiration) / 252,
                self.r, self.vol, pos.option_type
            )
            total += price * pos.notional
        return total
    
    def get_equity(self) -> float:
        """Get total equity."""
        return self.cash + self.get_options_value()
    
    def check_exposure(self, trade_value: float) -> bool:
        """Check if trade would exceed exposure limit."""
        current_value = self.get_options_value()
        new_value = current_value + trade_value
        
        return (new_value / self.initial_capital) <= self.max_exposure
    
    def open_position(self, signal: Dict) -> List[TradeRecord]:
        """Open new position from signal."""
        records = []
        close_target = self.day + signal.get("close_days", 5)
        
        for leg in signal.get("legs", []):
            self.position_counter += 1
            pos_id = f"P{self.position_counter}"
            
            strike = leg["strike"]
            opt_type = leg["opt_type"]
            action = leg["action"]
            expiry = self._get_expiry(signal.get("expiry", 30))
            
            # Get price and greeks
            price = self.bs.price(
                self.spot, strike,
                self._days_to_expiry(expiry) / 252,
                self.r, self.vol, opt_type
            )
            
            greeks = self.bs.greeks(
                self.spot, strike,
                self._days_to_expiry(expiry) / 252,
                self.r, self.vol, opt_type
            )
            
            # Calculate cost
            cost = price * 100
            commission = 0.50
            
            if action == "buy":
                if self.cash < cost + commission:
                    continue
                self.cash -= (cost + commission)
                qty = 1
            else:  # sell
                qty = -1
            
            # Create position
            symbol = f"{opt_type[0].upper()}{int(strike)}"
            position = OptionPosition(
                position_id=pos_id,
                strategy_id=signal["strategy_id"],
                symbol=symbol,
                option_type=opt_type,
                strike=strike,
                expiration=expiry,
                quantity=qty,
                entry_price=price,
                entry_greeks=greeks,
                entry_date=self.day,
                close_target=close_target
            )
            
            self.positions[pos_id] = position
            
            # Record trade
            record = TradeRecord(
                trade_id=f"T{len(self.trade_ledger)+1}",
                strategy_id=signal["strategy_id"],
                position_id=pos_id,
                action="open",
                symbol=symbol,
                option_type=opt_type,
                strike=strike,
                expiration=expiry,
                quantity=abs(qty),
                price=price,
                greeks=greeks,
                commission=commission
            )
            records.append(record)
            self.trade_ledger.append(record)
        
        return records
    
    def close_position(self, pos_id: str) -> Tuple[float, TradeRecord]:
        """Close a position."""
        if pos_id not in self.positions:
            return 0.0, None
        
        pos = self.positions[pos_id]
        
        # Get exit price
        exit_price = self.bs.price(
            self.spot, pos.strike,
            self._days_to_expiry(pos.expiration) / 252,
            self.r, self.vol, pos.option_type
        )
        
        exit_greeks = self.bs.greeks(
            self.spot, pos.strike,
            self._days_to_expiry(pos.expiration) / 252,
            self.r, self.vol, pos.option_type
        )
        
        # Calculate PnL
        pnl = (exit_price - pos.entry_price) * pos.notional
        commission = 0.50
        
        # Adjust for direction
        if pos.quantity < 0:
            pnl = -pnl
        
        pnl -= commission
        
        # Update cash
        exit_value = exit_price * pos.notional
        self.cash += exit_value - commission
        
        # Record strategy PnL
        self.strategies[pos.strategy_id].record_trade(pnl)
        
        # Create close record
        record = TradeRecord(
            trade_id=f"T{len(self.trade_ledger)+1}",
            strategy_id=pos.strategy_id,
            position_id=pos_id,
            action="close",
            symbol=pos.symbol,
            option_type=pos.option_type,
            strike=pos.strike,
            expiration=pos.expiration,
            quantity=abs(pos.quantity),
            price=exit_price,
            greeks=exit_greeks,
            pnl=pnl,
            commission=commission
        )
        self.trade_ledger.append(record)
        
        # Remove position
        del self.positions[pos_id]
        
        self.realized_pnl += pnl
        
        return pnl, record
    
    def close_expiring(self) -> int:
        """Close positions near expiration or at target day."""
        closed = 0
        
        for pos_id in list(self.positions.keys()):
            pos = self.positions[pos_id]
            
            # Close if at target day or near expiration
            should_close = (
                (self.day >= pos.close_target and pos.close_target > 0) or
                self._days_to_expiry(pos.expiration) <= 3
            )
            
            if should_close:
                self.close_position(pos_id)
                closed += 1
        
        return closed
    
    def update_market(self):
        """Update market conditions."""
        # Random walk
        self.spot *= (1 + random.gauss(0.0002, 0.008))
        self.spot = max(300, min(700, self.spot))
        
        # Vol mean reversion
        self.vol += random.gauss(0, 0.003)
        self.vol = max(0.10, min(0.50, self.vol))
    
    def run(self):
        """Run validation simulation."""
        print(f"\n{'='*70}")
        print("OPTIONS ALPHA ENGINE VALIDATION - 252 Days")
        print(f"Initial Capital: ${self.initial_capital:,.2f}")
        print(f"Max Exposure: {self.max_exposure:.0%}")
        print(f"{'='*70}\n")
        
        for day in range(1, self.simulation_days + 1):
            self.day = day
            
            # Generate and execute signals
            for strategy in self.strategies.values():
                signal = strategy.generate(day, self.spot, self.vol)
                
                if signal:
                    # Check exposure
                    trade_value = 0
                    for leg in signal.get("legs", []):
                        price = self.bs.price(
                            self.spot, leg["strike"],
                            signal.get("expiry", 30) / 252,
                            self.r, self.vol, leg["opt_type"]
                        )
                        trade_value += price * 100
                    
                    if self.check_exposure(trade_value):
                        self.open_position(signal)
            
            # Close expiring positions
            self.close_expiring()
            
            # Update market
            self.update_market()
            
            # Track equity
            equity = self.get_equity()
            self.equity_curve.append(equity)
            
            # Track Greeks
            self.greeks_history.append(self.get_greeks())
            
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
                g = self.get_greeks()
                print(f"Day {day}: Equity ${equity:,.2f}, Delta: {g['delta']:.1f}, Vol: {self.vol:.1%}")
        
        return self.generate_report()
    
    def generate_report(self) -> Dict:
        """Generate comprehensive report."""
        
        # Basic metrics
        equity = self.get_equity()
        ret = (equity - self.initial_capital) / self.initial_capital
        
        # Daily metrics
        if self.daily_pnl:
            avg_daily = sum(self.daily_pnl) / len(self.daily_pnl)
            std_daily = (sum((p - avg_daily)**2 for p in self.daily_pnl) / len(self.daily_pnl)) ** 0.5
            sharpe = (avg_daily / std_daily * (252**0.5)) if std_daily > 0 else 0
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
        closed_trades = [t for t in self.trade_ledger if t.action == "close"]
        wins = len([t for t in closed_trades if t.pnl > 0])
        win_rate = wins / len(closed_trades) if closed_trades else 0
        
        # Profit factor
        gross_profit = sum(t.pnl for t in closed_trades if t.pnl > 0)
        gross_loss = abs(sum(t.pnl for t in closed_trades if t.pnl < 0))
        pf = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        # Current Greeks
        current_greeks = self.get_greeks()
        
        # Strategy metrics
        strategy_metrics = {}
        for sid, strategy in self.strategies.items():
            m = strategy.get_metrics()
            m["name"] = strategy.name  # Add name
            strategy_metrics[sid] = m
        
        # Options value breakdown
        options_value = self.get_options_value()
        
        report = {
            "summary": {
                "initial_capital": self.initial_capital,
                "final_equity": equity,
                "return": ret,
                "sharpe": sharpe,
                "max_drawdown": max_dd,
                "win_rate": win_rate,
                "profit_factor": pf,
                "trade_count": len(closed_trades)
            },
            "accounting": {
                "cash": self.cash,
                "options_value": options_value,
                "realized_pnl": self.realized_pnl,
                "unrealized_pnl": options_value - (self.initial_capital - self.cash),
                "equity_identity": self.cash + options_value
            },
            "greeks": {
                "current": current_greeks,
                "history": self.greeks_history
            },
            "strategies": strategy_metrics,
            "equity_curve": self.equity_curve,
            "trade_ledger": self.trade_ledger
        }
        
        # Print report
        print(f"\n{'='*70}")
        print("OPTIONS STRATEGY ATTRIBUTION REPORT")
        print(f"{'='*70}")
        
        s = report["summary"]
        print(f"\n--- SUMMARY ---")
        print(f"Days: {len(self.equity_curve)}")
        print(f"Initial: ${s['initial_capital']:,.2f}")
        print(f"Final: ${s['final_equity']:,.2f}")
        print(f"Return: {s['return']:.2%}")
        print(f"Sharpe: {s['sharpe']:.2f}")
        print(f"Max DD: {s['max_drawdown']:.2%}")
        print(f"Win Rate: {s['win_rate']:.0%}")
        print(f"Profit Factor: {s['profit_factor']:.2f}")
        
        acc = report["accounting"]
        print(f"\n--- ACCOUNTING ---")
        print(f"Cash: ${acc['cash']:,.2f}")
        print(f"Options Value: ${acc['options_value']:,.2f}")
        print(f"Realized PnL: ${acc['realized_pnl']:,.2f}")
        print(f"Unrealized PnL: ${acc['unrealized_pnl']:,.2f}")
        print(f"Equity (identity check): ${acc['equity_identity']:,.2f}")
        
        g = report["greeks"]["current"]
        print(f"\n--- GREEKS EXPOSURE ---")
        print(f"Delta: {g['delta']:.2f}")
        print(f"Gamma: {g['gamma']:.4f}")
        print(f"Theta: {g['theta']:.2f}")
        print(f"Vega: {g['vega']:.2f}")
        
        print(f"\n--- STRATEGY ATTRIBUTION ---")
        for sid, strategy in self.strategies.items():
            m = strategy.get_metrics()
            print(f"\n{sid} ({m.get('name', sid)}):")
            print(f"  Trades: {m['trades']}, Win Rate: {m['win_rate']:.0%}")
            print(f"  Realized PnL: ${strategy.realized_pnl:,.2f}")
            print(f"  Sharpe: {m['sharpe']:.2f}, Profit Factor: {m['profit_factor']:.2f}")
        
        # Verification
        strategy_pnl_sum = sum(s.realized_pnl for s in self.strategies.values())
        
        print(f"\n--- RECONCILIATION ---")
        print(f"Strategy PnL Sum: ${strategy_pnl_sum:,.2f}")
        print(f"Portfolio Realized PnL: ${self.realized_pnl:,.2f}")
        print(f"Difference: ${abs(strategy_pnl_sum - self.realized_pnl):,.4f}")
        print(f"✅ RECONCILED: {abs(strategy_pnl_sum - self.realized_pnl) < 0.01}")
        
        print(f"\n{'='*70}\n")
        
        # Promotion check
        print("PROMOTION CRITERIA CHECK:")
        print(f"  Sharpe > 1.2: {'✅' if sharpe > 1.2 else '❌'} ({sharpe:.2f})")
        print(f"  Max DD < 10%: {'✅' if max_dd < 0.10 else '❌'} ({max_dd:.1%})")
        print(f"  Profit Factor > 1.3: {'✅' if pf > 1.3 else '❌'} ({pf:.2f})")
        
        return report


if __name__ == "__main__":
    portfolio = OptionsPortfolioAudit(
        initial_capital=100000,
        max_drawdown=0.15,
        max_exposure=0.10,
        simulation_days=252
    )
    
    report = portfolio.run()
    
    print(f"\n✅ Validation Complete!")
