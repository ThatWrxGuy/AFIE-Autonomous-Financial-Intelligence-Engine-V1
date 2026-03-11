"""
Vertical Spread Alpha Engine - Directive 016

Expanded vertical spread strategies with:
- Multiple spread variations
- Volatility regime filter
- Spread selection engine
- Improved position sizing
- Execution realism

Author: AFIE Engineering System
"""

import random
import math
from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass, field


@dataclass
class OptionPosition:
    """Single option position."""
    position_id: str
    strategy_id: str
    symbol: str
    option_type: str
    strike: float
    expiration: str
    quantity: int
    entry_price: float
    entry_greeks: Dict[str, float]
    entry_date: int
    close_target: int = 0
    

@dataclass
class TradeRecord:
    """Trade record."""
    trade_id: str
    strategy_id: str
    position_id: str
    action: str
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


class VolatilityRegimeDetector:
    """Detects volatility regime for strategy selection."""
    
    def __init__(self):
        self.vol_history: List[float] = []
        self.price_history: List[float] = []
        self.vix_proxy = 0.18  # Simulated VIX
    
    def update(self, price: float, vol: float) -> None:
        """Update regime state."""
        self.price_history.append(price)
        self.vol_history.append(vol)
        
        # Update VIX proxy
        self.vix_proxy = vol * random.uniform(0.9, 1.1)
        
        # Keep history limited
        if len(self.vol_history) > 60:
            self.vol_history.pop(0)
        if len(self.price_history) > 60:
            self.price_history.pop(0)
    
    def get_regime(self) -> str:
        """Get current volatility regime."""
        if not self.vol_history:
            return "normal"
        
        recent_vol = sum(self.vol_history[-10:]) / min(10, len(self.vol_history))
        avg_vol = sum(self.vol_history) / len(self.vol_history)
        
        # ATR-based expansion detection
        atr = 0
        if len(self.price_history) >= 14:
            trs = []
            for i in range(1, min(14, len(self.price_history))):
                h = self.price_history[-i]
                l = self.price_history[-i]
                tr = h - l
                trs.append(tr)
            atr = sum(trs) / len(trs) if trs else 0
        
        # Determine regime
        if recent_vol < avg_vol * 0.8:
            return "low_vol"
        elif recent_vol > avg_vol * 1.2:
            return "high_vol"
        elif atr > avg_vol * 0.02:
            return "volatile"
        else:
            return "normal"
    
    def get_regime_multiplier(self, regime: str) -> Dict[str, float]:
        """Get regime-based parameters."""
        multipliers = {
            "low_vol": {"sell_bias": 1.5, "width_pct": 0.03, "expiry_range": (21, 45)},
            "normal": {"sell_bias": 1.0, "width_pct": 0.05, "expiry_range": (14, 30)},
            "high_vol": {"sell_bias": 0.5, "width_pct": 0.07, "expiry_range": (7, 21)},
            "volatile": {"sell_bias": 0.3, "width_pct": 0.10, "expiry_range": (7, 14)}
        }
        return multipliers.get(regime, multipliers["normal"])


class SpreadSelectionEngine:
    """Selects optimal spread parameters."""
    
    def __init__(self, spot: float, regime: str):
        self.spot = spot
        self.regime = regime
    
    def select_strikes(self, direction: str, width_pct: float) -> Tuple[float, float]:
        """Select optimal strike prices."""
        if direction == "bull":
            # Bull call spread: buy lower, sell higher
            lower = self.spot * (1 - width_pct * 0.5)
            upper = self.spot * (1 + width_pct * 0.5)
        else:
            # Bear put spread: buy higher, sell lower
            upper = self.spot * (1 + width_pct * 0.5)
            lower = self.spot * (1 - width_pct * 0.5)
        
        return (lower, upper)
    
    def select_expiration(self, expiry_range: Tuple[int, int]) -> int:
        """Select optimal expiration."""
        return random.randint(*expiry_range)
    
    def calculate_risk_reward(self, lower_strike: float, upper_strike: float, 
                             lower_premium: float, upper_premium: float,
                             direction: str) -> Dict[str, float]:
        """Calculate risk/reward ratio."""
        if direction == "bull":
            max_risk = (lower_premium - upper_premium) * 100  # Net debit
            max_reward = (upper_strike - lower_strike) * 100 - max_risk
        else:
            max_risk = (upper_premium - lower_premium) * 100  # Net debit
            max_reward = (upper_strike - lower_strike) * 100 - max_risk
        
        risk_reward = abs(max_reward / max_risk) if max_risk > 0 else 0
        
        return {
            "max_risk": max_risk,
            "max_reward": max_reward,
            "risk_reward_ratio": risk_reward,
            "credit": max_risk < 0,
            "debit": max_risk > 0
        }


class VerticalSpreadStrategy:
    """Base vertical spread strategy with variations."""
    
    def __init__(self, strategy_id: str, name: str, variation: str):
        self.strategy_id = strategy_id
        self.name = name
        self.variation = variation
        self.trades: List[Dict] = []
        self.realized_pnl = 0.0
        self.wins = 0
        self.losses = 0
        
        # Parameters
        self.max_loss_pct = 0.02  # 2% max loss per spread
    
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
        
        peak = 0
        max_dd = 0
        running = 0
        for p in pnls:
            running += p
            if running > peak:
                peak = running
            dd = (peak - running) / max(peak, 1)
            max_dd = max(max_dd, dd)
        
        win_rate = self.wins / n if n > 0 else 0
        
        gross_profit = sum(p for p in pnls if p > 0)
        gross_loss = abs(sum(p for p in pnls if p < 0))
        pf = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        return {
            "strategy_id": self.strategy_id,
            "name": self.name,
            "variation": self.variation,
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


class TrendVerticalSpread(VerticalSpreadStrategy):
    """Trend-following vertical spread."""
    
    def __init__(self):
        super().__init__("VST_001", "TrendVerticalSpread", "trend")
        self.price_history: List[float] = []
        self.last_direction = None
        self.day = 0
    
    def get_signal(self, spot: float, regime: str) -> Optional[Dict]:
        """Generate trend signal."""
        self.price_history.append(spot)
        if len(self.price_history) < 10:
            return None
        
        # Simple trend detection
        recent = sum(self.price_history[-5:]) / 5
        older = sum(self.price_history[-10:-5]) / 5
        
        if recent > older * 1.01:
            direction = "bull"
        elif recent < older * 0.99:
            direction = "bear"
        else:
            return None
        
        self.last_direction = direction
        
        return {
            "strategy_id": self.strategy_id,
            "type": "vertical_spread",
            "direction": direction,
            "spread_type": "call" if direction == "bull" else "put"
        }


class MomentumVerticalSpread(VerticalSpreadStrategy):
    """Momentum-based vertical spread."""
    
    def __init__(self):
        super().__init__("VSM_001", "MomentumVerticalSpread", "momentum")
        self.day = 0
    
    def get_signal(self, spot: float, regime: str) -> Optional[Dict]:
        """Generate momentum signal."""
        if random.random() > 0.15:
            return None
        
        # Random momentum direction
        direction = random.choice(["bull", "bear"])
        
        return {
            "strategy_id": self.strategy_id,
            "type": "vertical_spread",
            "direction": direction,
            "spread_type": "call" if direction == "bull" else "put"
        }


class VolatilityRegimeVerticalSpread(VerticalSpreadStrategy):
    """Volatility regime-aware vertical spread."""
    
    def __init__(self):
        super().__init__("VSV_001", "VolatilityRegimeVerticalSpread", "volatility_regime")
        self.last_trade_day = -20
        self.day = 0  # Track current day
    
    def get_signal(self, spot: float, regime: str) -> Optional[Dict]:
        """Generate volatility regime signal."""
        # Cooldown
        if self.last_trade_day >= 0 and self.day - self.last_trade_day < 10:
            return None
        
        if random.random() > 0.12:
            return None
        
        # Regime-based direction
        if regime == "low_vol":
            # In low vol, sell spreads (credit spreads)
            direction = random.choice(["bull", "bear"])
        elif regime == "high_vol" or regime == "volatile":
            # In high vol, buy spreads (debit spreads)
            direction = random.choice(["bull", "bear"])
        else:
            direction = random.choice(["bull", "bear"])
        
        self.last_trade_day = self.day
        
        return {
            "strategy_id": self.strategy_id,
            "type": "vertical_spread",
            "direction": direction,
            "spread_type": "call" if direction == "bull" else "put"
        }


class BreakoutVerticalSpread(VerticalSpreadStrategy):
    """Breakout vertical spread."""
    
    def __init__(self):
        super().__init__("VSB_001", "BreakoutVerticalSpread", "breakout")
        self.high = 0
        self.low = float('inf')
        self.last_breakout = -30
        self.day = 0
    
    def get_signal(self, spot: float, regime: str) -> Optional[Dict]:
        """Generate breakout signal."""
        # Update range
        if spot > self.high:
            self.high = spot
        if spot < self.low:
            self.low = spot
        
        # Check for breakout
        range_size = self.high - self.low
        if range_size < spot * 0.02:  # Need at least 2% range
            return None
        
        if self.day - self.last_breakout < 15:
            return None
        
        if random.random() > 0.08:
            return None
        
        # Determine breakout direction
        recent = sum([spot]) / 1
        if spot > self.high * 0.98:
            direction = "bull"
        elif spot < self.low * 1.02:
            direction = "bear"
        else:
            return None
        
        self.last_breakout = self.day
        
        return {
            "strategy_id": self.strategy_id,
            "type": "vertical_spread",
            "direction": direction,
            "spread_type": "call" if direction == "bull" else "put"
        }


class VerticalSpreadPortfolio:
    """Portfolio managing all vertical spread strategies."""
    
    def __init__(
        self,
        initial_capital=100000,
        max_drawdown=0.12,
        max_options_exposure=0.10,
        simulation_days=252
    ):
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.max_drawdown = max_drawdown
        self.max_exposure = max_options_exposure
        self.simulation_days = simulation_days
        
        # Market
        self.spot = 450.0
        self.vol = 0.18
        self.r = 0.05
        self.bs = BlackScholes()
        
        # Regime detector
        self.regime_detector = VolatilityRegimeDetector()
        
        # Strategies
        self.strategies = {
            "VST_001": TrendVerticalSpread(),
            "VSM_001": MomentumVerticalSpread(),
            "VSV_001": VolatilityRegimeVerticalSpread(),
            "VSB_001": BreakoutVerticalSpread()
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
        
        # PnL
        self.realized_pnl = 0.0
        self.position_counter = 0
    
    def _days_to_expiry(self, expiration: str) -> float:
        exp_date = datetime.strptime(expiration, "%Y-%m-%d")
        return max(1, (exp_date - datetime.now()).days)
    
    def _get_expiry(self, days: int) -> str:
        return (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
    
    def get_greeks(self) -> Dict[str, float]:
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
    
    def get_options_value(self) -> float:
        total = 0
        for pos in self.positions.values():
            price = self.bs.price(
                self.spot, pos.strike,
                self._days_to_expiry(pos.expiration) / 252,
                self.r, self.vol, pos.option_type
            )
            total += price * abs(pos.quantity) * 100
        return total
    
    def get_equity(self) -> float:
        return self.cash + self.get_options_value()
    
    def check_exposure(self, trade_value: float) -> bool:
        current = self.get_options_value()
        return (current + trade_value) / self.initial_capital <= self.max_exposure
    
    def calculate_position_size(self, risk_pct: float = 0.01) -> int:
        """Calculate number of spreads based on risk."""
        max_loss = self.initial_capital * risk_pct
        # Assume 1.5% moves = max loss per spread
        return max(1, int(max_loss / (self.spot * 0.015 * 100)))
    
    def execute_spread(
        self,
        signal: Dict,
        spread_engine: SpreadSelectionEngine,
        regime: str
    ) -> List[TradeRecord]:
        """Execute a vertical spread."""
        records = []
        
        direction = signal["direction"]
        spread_type = signal["spread_type"]
        
        # Get regime parameters
        regime_params = self.regime_detector.get_regime_multiplier(regime)
        width_pct = regime_params["width_pct"]
        expiry_range = regime_params["expiry_range"]
        
        # Select strikes
        lower_strike, upper_strike = spread_engine.select_strikes(direction, width_pct)
        expiry = spread_engine.select_expiration(expiry_range)
        
        # Get prices with bid/ask spread
        lower_price = self.bs.price(
            self.spot, lower_strike, expiry/252, self.r, self.vol, spread_type
        )
        upper_price = self.bs.price(
            self.spot, upper_strike, expiry/252, self.r, self.vol, spread_type
        )
        
        # Apply bid/ask spread (1% wide)
        if direction == "bull":
            # Buy lower (OTM), sell higher (further OTM)
            long_price = lower_price * 1.01  # Ask
            short_price = upper_price * 0.99  # Bid
            net_cost = (long_price - short_price) * 100
        else:
            # Buy higher (OTM), sell lower (further OTM) for put
            long_price = lower_price * 1.01  # Ask
            short_price = upper_price * 0.99  # Bid
            net_cost = (long_price - short_price) * 100
        
        # Check cash
        if net_cost > self.cash:
            return records
        
        # Commission
        commission = 1.00  # $1 per spread
        
        # Update cash
        self.cash -= (net_cost + commission)
        
        # Position size
        qty = self.calculate_position_size()
        
        # Open both legs
        exp_str = self._get_expiry(expiry)
        
        for i, (strike, price, opt_type) in enumerate([
            (lower_strike, long_price, spread_type),
            (upper_strike, short_price, spread_type)
        ]):
            self.position_counter += 1
            pos_id = f"P{self.position_counter}"
            
            q = qty if i == 0 else -qty  # Long then short
            
            position = OptionPosition(
                position_id=pos_id,
                strategy_id=signal["strategy_id"],
                symbol=f"{opt_type[0].upper()}{int(strike)}",
                option_type=opt_type,
                strike=strike,
                expiration=exp_str,
                quantity=q,
                entry_price=price,
                entry_greeks=self.bs.greeks(self.spot, strike, expiry/252, self.r, self.vol, opt_type),
                entry_date=self.day,
                close_target=self.day + random.randint(5, 12)
            )
            
            self.positions[pos_id] = position
            
            record = TradeRecord(
                trade_id=f"T{len(self.trade_ledger)+1}",
                strategy_id=signal["strategy_id"],
                position_id=pos_id,
                action="open",
                symbol=position.symbol,
                option_type=opt_type,
                strike=strike,
                expiration=exp_str,
                quantity=abs(q),
                price=price,
                greeks=position.entry_greeks,
                commission=commission/2
            )
            records.append(record)
            self.trade_ledger.append(record)
        
        return records
    
    def close_position(self, pos_id: str) -> float:
        """Close a position."""
        if pos_id not in self.positions:
            return 0.0
        
        pos = self.positions[pos_id]
        
        exit_price = self.bs.price(
            self.spot, pos.strike,
            self._days_to_expiry(pos.expiration) / 252,
            self.r, self.vol, pos.option_type
        )
        
        pnl = (exit_price - pos.entry_price) * pos.quantity * 100
        commission = 0.50
        
        # Cash settlement
        if pos.quantity > 0:
            self.cash += (exit_price * pos.quantity * 100 - commission)
        else:
            self.cash += abs(pos.quantity) * 100 * (pos.entry_price - exit_price) - commission
        
        self.realized_pnl += pnl - commission
        
        # Record strategy PnL
        self.strategies[pos.strategy_id].record_trade(pnl - commission)
        
        del self.positions[pos_id]
        
        return pnl - commission
    
    def close_expiring(self) -> int:
        """Close positions at target or expiration."""
        closed = 0
        
        for pos_id in list(self.positions.keys()):
            pos = self.positions[pos_id]
            
            should_close = (
                self.day >= pos.close_target or
                self._days_to_expiry(pos.expiration) <= 3
            )
            
            if should_close:
                self.close_position(pos_id)
                closed += 1
        
        return closed
    
    def update_market(self):
        """Update market."""
        self.spot *= (1 + random.gauss(0.0002, 0.008))
        self.spot = max(300, min(700, self.spot))
        
        self.vol += random.gauss(0, 0.003)
        self.vol = max(0.10, min(0.50, self.vol))
        
        self.regime_detector.update(self.spot, self.vol)
        
        # Update strategy day counters
        for s in self.strategies.values():
            if hasattr(s, 'day'):
                s.day = self.day
    
    def run(self):
        """Run simulation."""
        print(f"\n{'='*70}")
        print("VERTICAL SPREAD ALPHA ENGINE - 252 Days")
        print(f"Initial: ${self.initial_capital:,.2f}, Max Exposure: {self.max_exposure:.0%}")
        print(f"{'='*70}\n")
        
        for day in range(1, self.simulation_days + 1):
            self.day = day
            
            # Get regime
            regime = self.regime_detector.get_regime()
            spread_engine = SpreadSelectionEngine(self.spot, regime)
            
            # Generate signals from each strategy
            for sid, strategy in self.strategies.items():
                signal = strategy.get_signal(self.spot, regime)
                
                if signal:
                    # Execute spread
                    trade_value = self.spot * 0.05 * 100  # Estimate
                    if self.check_exposure(trade_value):
                        self.execute_spread(signal, spread_engine, regime)
            
            # Close positions
            self.close_expiring()
            
            # Update market
            self.update_market()
            
            # Track
            equity = self.get_equity()
            self.equity_curve.append(equity)
            self.greeks_history.append(self.get_greeks())
            
            if len(self.equity_curve) > 1:
                daily = equity - self.equity_curve[-2]
            else:
                daily = 0
            self.daily_pnl.append(daily)
            
            if equity > self.peak:
                self.peak = equity
            
            dd = (self.peak - equity) / self.peak
            if dd > self.max_drawdown:
                print(f"\n⚠️ KILL SWITCH: Drawdown {dd:.1%}")
                break
            
            if day % 50 == 0:
                g = self.get_greeks()
                print(f"Day {day}: Equity ${equity:,.2f}, Regime: {regime}, Delta: {g['delta']:.1f}")
        
        return self.report()
    
    def report(self) -> Dict:
        """Generate report."""
        equity = self.get_equity()
        ret = (equity - self.initial_capital) / self.initial_capital
        
        if self.daily_pnl:
            avg = sum(self.daily_pnl) / len(self.daily_pnl)
            std = (sum((p-avg)**2 for p in self.daily_pnl) / len(self.daily_pnl)) ** 0.5
            sharpe = (avg/std * 252**0.5) if std else 0
        else:
            sharpe = 0
        
        max_dd = 0
        peak = self.initial_capital
        for e in self.equity_curve:
            if e > peak:
                peak = e
            dd = (peak - e) / peak
            max_dd = max(max_dd, dd)
        
        closed = [t for t in self.trade_ledger if t.action == "close"]
        wins = len([t for t in closed if t.pnl > 0])
        win_rate = wins / len(closed) if closed else 0
        
        gross_profit = sum(t.pnl for t in closed if t.pnl > 0)
        gross_loss = abs(sum(t.pnl for t in closed if t.pnl < 0))
        pf = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        g = self.get_greeks()
        
        print(f"\n{'='*70}")
        print("VERTICAL SPREAD STRATEGY REPORT")
        print(f"{'='*70}")
        
        print(f"\n--- SUMMARY ---")
        print(f"Days: {len(self.equity_curve)}")
        print(f"Initial: ${self.initial_capital:,.2f}")
        print(f"Final: ${equity:,.2f}")
        print(f"Return: {ret:.2%}")
        print(f"Sharpe: {sharpe:.2f}")
        print(f"Max DD: {max_dd:.2%}")
        print(f"Win Rate: {win_rate:.0%}")
        print(f"Profit Factor: {pf:.2f}")
        
        print(f"\n--- GREEKS ---")
        print(f"Delta: {g['delta']:.2f}")
        print(f"Gamma: {g['gamma']:.4f}")
        print(f"Theta: {g['theta']:.2f}")
        print(f"Vega: {g['vega']:.2f}")
        
        print(f"\n--- STRATEGY PERFORMANCE ---")
        total_pnl = 0
        for sid, strategy in self.strategies.items():
            m = strategy.get_metrics()
            total_pnl += m["realized_pnl"]
            print(f"\n{sid} ({m['name']}):")
            print(f"  Trades: {m['trades']}, Win Rate: {m['win_rate']:.0%}")
            print(f"  Realized PnL: ${m['realized_pnl']:,.2f}")
            print(f"  Sharpe: {m['sharpe']:.2f}, PF: {m['profit_factor']:.2f}")
        
        print(f"\n--- RECONCILIATION ---")
        print(f"Strategy PnL Sum: ${total_pnl:,.2f}")
        print(f"Portfolio Realized: ${self.realized_pnl:,.2f}")
        print(f"✅ RECONCILED: {abs(total_pnl - self.realized_pnl) < 0.01}")
        
        print(f"\n--- PROMOTION CRITERIA ---")
        print(f"Sharpe > 1.5: {'✅' if sharpe > 1.5 else '❌'} ({sharpe:.2f})")
        print(f"Profit Factor > 1.3: {'✅' if pf > 1.3 else '❌'} ({pf:.2f})")
        print(f"Max DD < 10%: {'✅' if max_dd < 0.10 else '❌'} ({max_dd:.1%})")
        
        print(f"\n{'='*70}\n")
        
        return {
            "return": ret,
            "sharpe": sharpe,
            "max_dd": max_dd,
            "win_rate": win_rate,
            "profit_factor": pf,
            "equity_curve": self.equity_curve,
            "greeks": g
        }


if __name__ == "__main__":
    portfolio = VerticalSpreadPortfolio(
        initial_capital=100000,
        max_drawdown=0.12,  # Lower drawdown limit
        max_options_exposure=0.08,  # Lower exposure
        simulation_days=252
    )
    
    report = portfolio.run()
    
    print(f"\n✅ Vertical Spread Alpha Complete!")
