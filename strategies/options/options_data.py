"""
Options Data Module for AFIE.

Provides options pricing and Greeks calculation using Black-Scholes model.

Author: AFIE Engineering System
"""

import math
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import random


@dataclass
class OptionContract:
    """Represents a single option contract."""
    symbol: str
    underlying: str
    strike: float
    expiration: str  # YYYY-MM-DD
    option_type: str  # "call" or "put"
    quantity: int = 1
    
    def __repr__(self):
        return f"{self.underlying}_{self.expiration}_{self.option_type[0].upper()}{int(self.strike)}"


@dataclass
class OptionGreeks:
    """Option Greeks values."""
    delta: float = 0.0
    gamma: float = 0.0
    theta: float = 0.0
    vega: float = 0.0
    rho: float = 0.0
    
    def to_dict(self) -> Dict[str, float]:
        return {
            "delta": self.delta,
            "gamma": self.gamma,
            "theta": self.theta,
            "vega": self.vega,
            "rho": self.rho
        }


class BlackScholes:
    """Black-Scholes options pricing model."""
    
    @staticmethod
    def _cumulative_normal(x: float) -> float:
        """Standard normal cumulative distribution function."""
        return 0.5 * (1 + math.erf(x / math.sqrt(2)))
    
    @staticmethod
    def _probability_density(x: float) -> float:
        """Standard normal probability density function."""
        return math.exp(-0.5 * x * x) / math.sqrt(2 * math.pi)
    
    @staticmethod
    def calculate_d1_d2(
        spot: float,
        strike: float,
        time_to_expiry: float,
        risk_free_rate: float,
        volatility: float
    ) -> Tuple[float, float]:
        """Calculate d1 and d2 parameters."""
        if time_to_expiry <= 0:
            return 0.0, 0.0
        
        d1 = (math.log(spot / strike) + (risk_free_rate + 0.5 * volatility ** 2) * time_to_expiry) / (volatility * math.sqrt(time_to_expiry))
        d2 = d1 - volatility * math.sqrt(time_to_expiry)
        
        return d1, d2
    
    @staticmethod
    def call_price(
        spot: float,
        strike: float,
        time_to_expiry: float,
        risk_free_rate: float,
        volatility: float
    ) -> float:
        """Calculate call option price."""
        if time_to_expiry <= 0:
            return max(0, spot - strike)
        
        d1, d2 = BlackScholes.calculate_d1_d2(spot, strike, time_to_expiry, risk_free_rate, volatility)
        
        call = spot * BlackScholes._cumulative_normal(d1) - strike * math.exp(-risk_free_rate * time_to_expiry) * BlackScholes._cumulative_normal(d2)
        
        return max(0, call)
    
    @staticmethod
    def put_price(
        spot: float,
        strike: float,
        time_to_expiry: float,
        risk_free_rate: float,
        volatility: float
    ) -> float:
        """Calculate put option price."""
        if time_to_expiry <= 0:
            return max(0, strike - spot)
        
        d1, d2 = BlackScholes.calculate_d1_d2(spot, strike, time_to_expiry, risk_free_rate, volatility)
        
        put = strike * math.exp(-risk_free_rate * time_to_expiry) * BlackScholes._cumulative_normal(-d2) - spot * BlackScholes._cumulative_normal(-d1)
        
        return max(0, put)
    
    @staticmethod
    def calculate_greeks(
        spot: float,
        strike: float,
        time_to_expiry: float,
        risk_free_rate: float,
        volatility: float,
        option_type: str
    ) -> OptionGreeks:
        """Calculate all Greeks for an option."""
        if time_to_expiry <= 0:
            return OptionGreeks()
        
        d1, d2 = BlackScholes.calculate_d1_d2(spot, strike, time_to_expiry, risk_free_rate, volatility)
        
        sqrt_t = math.sqrt(time_to_expiry)
        nd1 = BlackScholes._probability_density(d1)
        
        if option_type == "call":
            delta = BlackScholes._cumulative_normal(d1)
            rho = strike * time_to_expiry * math.exp(-risk_free_rate * time_to_expiry) * BlackScholes._cumulative_normal(d2) / 100
            theta = (-spot * nd1 * volatility / (2 * sqrt_t) - risk_free_rate * strike * math.exp(-risk_free_rate * time_to_expiry) * BlackScholes._cumulative_normal(d2)) / 365
        else:  # put
            delta = BlackScholes._cumulative_normal(d1) - 1
            rho = -strike * time_to_expiry * math.exp(-risk_free_rate * time_to_expiry) * BlackScholes._cumulative_normal(-d2) / 100
            theta = (-spot * nd1 * volatility / (2 * sqrt_t) + risk_free_rate * strike * math.exp(-risk_free_rate * time_to_expiry) * BlackScholes._cumulative_normal(-d2)) / 365
        
        gamma = nd1 / (spot * volatility * sqrt_t)
        vega = spot * sqrt_t * nd1 / 100
        
        return OptionGreeks(
            delta=delta,
            gamma=gamma,
            theta=theta,
            vega=vega,
            rho=rho
        )


class OptionsChain:
    """Simulated options chain for SPY."""
    
    def __init__(
        self,
        underlying: str = "SPY",
        spot_price: float = 450.0,
        volatility: float = 0.20,
        risk_free_rate: float = 0.05
    ):
        self.underlying = underlying
        self.spot_price = spot_price
        self.volatility = volatility
        self.risk_free_rate = risk_free_rate
        self.black_scholes = BlackScholes()
        
        # Generate strikes around spot
        self.strikes = self._generate_strikes()
        
        # Generate expirations (every Friday for next 4 weeks)
        self.expirations = self._generate_expirations()
    
    def _generate_strikes(self) -> List[float]:
        """Generate strike prices around spot."""
        strikes = []
        for i in range(-10, 11):
            strike = self.spot_price + (i * 5)
            if strike > 0:
                strikes.append(strike)
        return strikes
    
    def _generate_expirations(self) -> List[str]:
        """Generate expiration dates."""
        expirations = []
        base_date = datetime.now()
        for weeks in range(1, 9):  # Next 8 weeks
            # Find next Friday
            days_until_friday = (4 - base_date.weekday()) % 7
            if days_until_friday == 0:
                days_until_friday = 7
            friday = base_date + timedelta(days=days_until_friday + (weeks - 1) * 7)
            expirations.append(friday.strftime("%Y-%m-%d"))
        return expirations
    
    def get_option_price(
        self,
        strike: float,
        expiration: str,
        option_type: str
    ) -> float:
        """Get option price."""
        # Calculate time to expiry
        exp_date = datetime.strptime(expiration, "%Y-%m-%d")
        days_to_expiry = (exp_date - datetime.now()).days
        time_to_expiry = days_to_expiry / 252
        
        if option_type == "call":
            return self.black_scholes.call_price(
                self.spot_price, strike, time_to_expiry,
                self.risk_free_rate, self.volatility
            )
        else:
            return self.black_scholes.put_price(
                self.spot_price, strike, time_to_expiry,
                self.risk_free_rate, self.volatility
            )
    
    def get_option_greeks(
        self,
        strike: float,
        expiration: str,
        option_type: str
    ) -> OptionGreeks:
        """Get option Greeks."""
        exp_date = datetime.strptime(expiration, "%Y-%m-%d")
        days_to_expiry = (exp_date - datetime.now()).days
        time_to_expiry = days_to_expiry / 252
        
        return self.black_scholes.calculate_greeks(
            self.spot_price, strike, time_to_expiry,
            self.risk_free_rate, self.volatility, option_type
        )
    
    def get_chain(self, expiration: str) -> List[Dict[str, Any]]:
        """Get full options chain for an expiration."""
        chain = []
        
        for strike in self.strikes:
            call_price = self.get_option_price(strike, expiration, "call")
            put_price = self.get_option_price(strike, expiration, "put")
            
            call_greeks = self.get_option_greeks(strike, expiration, "call")
            put_greeks = self.get_option_greeks(strike, expiration, "put")
            
            chain.append({
                "strike": strike,
                "call": {
                    "bid": call_price * 0.98,
                    "ask": call_price * 1.02,
                    "mid": call_price,
                    "greeks": call_greeks.to_dict()
                },
                "put": {
                    "bid": put_price * 0.98,
                    "ask": put_price * 1.02,
                    "mid": put_price,
                    "greeks": put_greeks.to_dict()
                }
            })
        
        return chain
    
    def update_spot(self, new_spot: float) -> None:
        """Update spot price."""
        self.spot_price = new_spot
    
    def update_volatility(self, new_vol: float) -> None:
        """Update volatility."""
        self.volatility = new_vol


class OptionsPortfolio:
    """Track options positions."""
    
    def __init__(self):
        self.positions: Dict[str, Dict[str, Any]] = {}  # {symbol: position}
    
    def add_position(
        self,
        symbol: str,
        option_type: str,
        strike: float,
        expiration: str,
        quantity: int,
        entry_price: float,
        greeks: OptionGreeks
    ) -> None:
        """Add an options position."""
        if symbol in self.positions:
            pos = self.positions[symbol]
            # Average in
            old_qty = pos["quantity"]
            old_price = pos["entry_price"]
            new_qty = old_qty + quantity
            pos["entry_price"] = (old_price * old_qty + entry_price * quantity) / new_qty
            pos["quantity"] = new_qty
        else:
            self.positions[symbol] = {
                "option_type": option_type,
                "strike": strike,
                "expiration": expiration,
                "quantity": quantity,
                "entry_price": entry_price,
                "entry_greeks": greeks.to_dict()
            }
    
    def close_position(self, symbol: str, quantity: int, exit_price: float, greeks: OptionGreeks) -> float:
        """Close an options position and return PnL."""
        if symbol not in self.positions:
            return 0.0
        
        pos = self.positions[symbol]
        
        if quantity >= pos["quantity"]:
            # Close entire position
            pnl = (exit_price - pos["entry_price"]) * pos["quantity"] * 100  # Options are x100 shares
            del self.positions[symbol]
            return pnl
        else:
            # Partial close
            pnl = (exit_price - pos["entry_price"]) * quantity * 100
            pos["quantity"] -= quantity
            return pnl
    
    def get_positions(self) -> Dict[str, Dict[str, Any]]:
        """Get all positions."""
        return self.positions
    
    def get_total_exposure(self) -> Dict[str, float]:
        """Calculate total options exposure."""
        delta = 0.0
        gamma = 0.0
        theta = 0.0
        vega = 0.0
        
        for pos in self.positions.values():
            mult = pos["quantity"] * 100
            greeks = pos["entry_greeks"]
            
            delta += greeks["delta"] * mult
            gamma += greeks["gamma"] * mult
            theta += greeks["theta"] * mult
            vega += greeks["vega"] * mult
        
        return {
            "delta": delta,
            "gamma": gamma,
            "theta": theta,
            "vega": vega,
            "position_count": len(self.positions)
        }


if __name__ == "__main__":
    # Test options chain
    chain = OptionsChain(spot_price=450, volatility=0.20)
    
    print("SPY Options Chain Test")
    print(f"Spot: ${chain.spot_price}, Vol: {chain.volatility:.1%}")
    print()
    
    # Get ATM options
    exp = chain.expirations[0]
    chain_data = chain.get_chain(exp)
    
    atm = [c for c in chain_data if c["strike"] == 450][0]
    print(f"Expiration: {exp}")
    print(f"Strike: $450")
    print(f"Call: ${atm['call']['mid']:.2f} (Delta: {atm['call']['greeks']['delta']:.3f})")
    print(f"Put: ${atm['put']['mid']:.2f} (Delta: {atm['put']['greeks']['delta']:.3f})")
    
    # Test portfolio
    portfolio = OptionsPortfolio()
    portfolio.add_position(
        "SPY_2024-03-15_C450",
        "call", 450, "2024-03-15", 1, atm['call']['mid'],
        OptionGreeks(delta=0.5, gamma=0.02, theta=-0.05, vega=0.10)
    )
    
    exposure = portfolio.get_total_exposure()
    print(f"\nPortfolio Delta: {exposure['delta']:.2f}")
    print(f"Positions: {exposure['position_count']}")
