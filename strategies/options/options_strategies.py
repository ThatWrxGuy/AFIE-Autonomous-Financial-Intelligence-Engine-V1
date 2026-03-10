"""
Options Strategies for AFIE.

Implements:
- Vertical Spread Strategy
- Calendar Spread Strategy
- Iron Condor Strategy
- Volatility Breakout Strategy

Author: AFIE Engineering System
"""

import random
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from strategies.options.options_data import (
    OptionsChain,
    OptionGreeks,
    OptionContract
)


class OptionsStrategy:
    """Base class for options strategies."""
    
    def __init__(
        self,
        strategy_id: str,
        name: str,
        max_allocation: float = 0.15
    ):
        self.strategy_id = strategy_id
        self.name = name
        self.max_allocation = max_allocation
        self.signals_generated: List[Dict[str, Any]] = []
    
    def generate_signals(
        self,
        day: int,
        options_chain: OptionsChain,
        portfolio_value: float
    ) -> List[Dict[str, Any]]:
        """Generate trading signals."""
        raise NotImplementedError
    
    def _create_signal(
        self,
        signal_type: str,
        option_type: str,
        strike: float,
        expiration: str,
        action: str,
        quantity: int,
        greeks: Dict[str, float]
    ) -> Dict[str, Any]:
        """Create a standardized signal."""
        return {
            "strategy_id": self.strategy_id,
            "strategy_name": self.name,
            "signal_type": signal_type,
            "option_type": option_type,
            "strike": strike,
            "expiration": expiration,
            "action": action,  # buy or sell
            "quantity": quantity,
            "greeks": greeks,
            "timestamp": datetime.utcnow().isoformat()
        }


class VerticalSpreadStrategy(OptionsStrategy):
    """
    Vertical Spread Strategy.
    
    Constructs bull call spreads and bear put spreads based on trend/momentum.
    Buys lower strike, sells higher strike for calls (bull) or vice versa for puts.
    """
    
    def __init__(self):
        super().__init__(
            strategy_id="OPT_VS_001",
            name="VerticalSpread",
            max_allocation=0.15
        )
    
    def generate_signals(
        self,
        day: int,
        options_chain: OptionsChain,
        portfolio_value: float
    ) -> List[Dict[str, Any]]:
        """Generate vertical spread signals."""
        signals = []
        
        # Only generate signals occasionally
        if random.random() > 0.15:
            return signals
        
        spot = options_chain.spot_price
        exp = options_chain.expirations[random.randint(0, min(3, len(options_chain.expirations)-1))]
        
        # Determine direction based on random signal (simulating trend)
        direction = random.choice(["bull", "bear"])
        
        if direction == "bull":
            # Bull Call Spread: Buy lower strike call, sell higher strike call
            strikes = sorted([s for s in options_chain.strikes if s >= spot])
            if len(strikes) < 2:
                return signals
            
            lower_strike = strikes[0]
            upper_strike = strikes[min(1, len(strikes)-1)]
            
            # Buy lower strike
            long_call_price = options_chain.get_option_price(lower_strike, exp, "call")
            long_greeks = options_chain.get_option_greeks(lower_strike, exp, "call")
            
            signals.append(self._create_signal(
                "bull_call_spread", "call", lower_strike, exp,
                "buy", 1, long_greeks.to_dict()
            ))
            
            # Sell higher strike
            short_call_price = options_chain.get_option_price(upper_strike, exp, "call")
            short_greeks = options_chain.get_option_greeks(upper_strike, exp, "call")
            
            signals.append(self._create_signal(
                "bull_call_spread", "call", upper_strike, exp,
                "sell", 1, short_greeks.to_dict()
            ))
        
        else:
            # Bear Put Spread: Buy higher strike put, sell lower strike put
            strikes = sorted([s for s in options_chain.strikes if s <= spot], reverse=True)
            if len(strikes) < 2:
                return signals
            
            higher_strike = strikes[0]
            lower_strike = strikes[min(1, len(strikes)-1)]
            
            # Buy higher strike put
            long_put_price = options_chain.get_option_price(higher_strike, exp, "put")
            long_greeks = options_chain.get_option_greeks(higher_strike, exp, "put")
            
            signals.append(self._create_signal(
                "bear_put_spread", "put", higher_strike, exp,
                "buy", 1, long_greeks.to_dict()
            ))
            
            # Sell lower strike put
            short_put_price = options_chain.get_option_price(lower_strike, exp, "put")
            short_greeks = options_chain.get_option_greeks(lower_strike, exp, "put")
            
            signals.append(self._create_signal(
                "bear_put_spread", "put", lower_strike, exp,
                "sell", 1, short_greeks.to_dict()
            ))
        
        self.signals_generated.extend(signals)
        return signals


class CalendarSpreadStrategy(OptionsStrategy):
    """
    Calendar Spread Strategy.
    
    Exploits term structure differences between near-term and longer-term options.
    Sells near-term, buys longer-term with same strike.
    """
    
    def __init__(self):
        super().__init__(
            strategy_id="OPT_CS_001",
            name="CalendarSpread",
            max_allocation=0.15
        )
    
    def generate_signals(
        self,
        day: int,
        options_chain: OptionsChain,
        portfolio_value: float
    ) -> List[Dict[str, Any]]:
        """Generate calendar spread signals."""
        signals = []
        
        if random.random() > 0.10:
            return signals
        
        spot = options_chain.spot_price
        
        # Need at least 2 expirations
        if len(options_chain.expirations) < 2:
            return signals
        
        near_exp = options_chain.expirations[0]
        far_exp = options_chain.expirations[min(3, len(options_chain.expirations)-1)]
        
        # Find ATM strike
        strikes = sorted(options_chain.strikes, key=lambda x: abs(x - spot))
        atm_strike = strikes[0]
        
        # Sell near-term, buy far-term (neutral calendar)
        option_type = random.choice(["call", "put"])
        
        # Buy far-term
        far_price = options_chain.get_option_price(atm_strike, far_exp, option_type)
        far_greeks = options_chain.get_option_greeks(atm_strike, far_exp, option_type)
        
        signals.append(self._create_signal(
            "calendar_spread", option_type, atm_strike, far_exp,
            "buy", 1, far_greeks.to_dict()
        ))
        
        # Sell near-term
        near_price = options_chain.get_option_price(atm_strike, near_exp, option_type)
        near_greeks = options_chain.get_option_greeks(atm_strike, near_exp, option_type)
        
        signals.append(self._create_signal(
            "calendar_spread", option_type, atm_strike, near_exp,
            "sell", 1, near_greeks.to_dict()
        ))
        
        self.signals_generated.extend(signals)
        return signals


class IronCondorStrategy(OptionsStrategy):
    """
    Iron Condor Strategy.
    
    Sells volatility in low-volatility environments using out-of-the-money spreads.
    Sell OTM call spread + sell OTM put spread.
    """
    
    def __init__(self):
        super().__init__(
            strategy_id="OPT_IC_001",
            name="IronCondor",
            max_allocation=0.15
        )
    
    def generate_signals(
        self,
        day: int,
        options_chain: OptionsChain,
        portfolio_value: float
    ) -> List[Dict[str, Any]]:
        """Generate iron condor signals."""
        signals = []
        
        # Only in low volatility environments
        if options_chain.volatility > 0.25:
            return signals
        
        if random.random() > 0.08:
            return signals
        
        spot = options_chain.spot_price
        exp = options_chain.expirations[random.randint(0, min(2, len(options_chain.expirations)-1))]
        
        # Find OTM strikes
        call_strikes = [s for s in options_chain.strikes if s > spot * 1.02]
        put_strikes = [s for s in options_chain.strikes if s < spot * 0.98]
        
        if len(call_strikes) < 2 or len(put_strikes) < 2:
            return signals
        
        # Sell OTM call spread (higher strikes)
        short_call_strike = call_strikes[min(1, len(call_strikes)-1)]
        long_call_strike = call_strikes[min(2, len(call_strikes)-1)]
        
        # Buy further OTM call
        long_call_price = options_chain.get_option_price(long_call_strike, exp, "call")
        long_call_greeks = options_chain.get_option_greeks(long_call_strike, exp, "call")
        
        signals.append(self._create_signal(
            "iron_condor", "call", long_call_strike, exp,
            "buy", 1, long_call_greeks.to_dict()
        ))
        
        # Sell closer OTM call
        short_call_price = options_chain.get_option_price(short_call_strike, exp, "call")
        short_call_greeks = options_chain.get_option_greeks(short_call_strike, exp, "call")
        
        signals.append(self._create_signal(
            "iron_condor", "call", short_call_strike, exp,
            "sell", 1, short_call_greeks.to_dict()
        ))
        
        # Sell OTM put spread (lower strikes)
        short_put_strike = put_strikes[0]
        long_put_strike = put_strikes[1]
        
        # Buy further OTM put
        long_put_price = options_chain.get_option_price(long_put_strike, exp, "put")
        long_put_greeks = options_chain.get_option_greeks(long_put_strike, exp, "put")
        
        signals.append(self._create_signal(
            "iron_condor", "put", long_put_strike, exp,
            "buy", 1, long_put_greeks.to_dict()
        ))
        
        # Sell closer OTM put
        short_put_price = options_chain.get_option_price(short_put_strike, exp, "put")
        short_put_greeks = options_chain.get_option_greeks(short_put_strike, exp, "put")
        
        signals.append(self._create_signal(
            "iron_condor", "put", short_put_strike, exp,
            "sell", 1, short_put_greeks.to_dict()
        ))
        
        self.signals_generated.extend(signals)
        return signals


class VolatilityBreakoutStrategy(OptionsStrategy):
    """
    Volatility Breakout Strategy.
    
    Enters long straddle or strangle positions during volatility expansion signals.
    """
    
    def __init__(self):
        super().__init__(
            strategy_id="OPT_VB_001",
            name="VolatilityBreakout",
            max_allocation=0.15
        )
        self.last_vol_event_day = -100
    
    def generate_signals(
        self,
        day: int,
        options_chain: OptionsChain,
        portfolio_value: float
    ) -> List[Dict[str, Any]]:
        """Generate volatility breakout signals."""
        signals = []
        
        # Check cooldown
        if day - self.last_vol_event_day < 20:
            return signals
        
        # Simulate volatility expansion event
        if random.random() > 0.05:
            return signals
        
        # Volatility breakout detected!
        self.last_vol_event_day = day
        
        spot = options_chain.spot_price
        exp = options_chain.expirations[random.randint(1, min(3, len(options_chain.expirations)-1))]
        
        # ATM strike for straddle
        strikes = sorted(options_chain.strikes, key=lambda x: abs(x - spot))
        atm_strike = strikes[0]
        
        # Buy call
        call_price = options_chain.get_option_price(atm_strike, exp, "call")
        call_greeks = options_chain.get_option_greeks(atm_strike, exp, "call")
        
        signals.append(self._create_signal(
            "volatility_breakout", "call", atm_strike, exp,
            "buy", 1, call_greeks.to_dict()
        ))
        
        # Buy put
        put_price = options_chain.get_option_price(atm_strike, exp, "put")
        put_greeks = options_chain.get_option_greeks(atm_strike, exp, "put")
        
        signals.append(self._create_signal(
            "volatility_breakout", "put", atm_strike, exp,
            "buy", 1, put_greeks.to_dict()
        ))
        
        self.signals_generated.extend(signals)
        return signals


class OptionsStrategyManager:
    """Manages all options strategies."""
    
    def __init__(self):
        self.strategies: Dict[str, OptionsStrategy] = {}
        self._register_strategies()
    
    def _register_strategies(self):
        """Register all options strategies."""
        self.strategies["OPT_VS_001"] = VerticalSpreadStrategy()
        self.strategies["OPT_CS_001"] = CalendarSpreadStrategy()
        self.strategies["OPT_IC_001"] = IronCondorStrategy()
        self.strategies["OPT_VB_001"] = VolatilityBreakoutStrategy()
    
    def generate_all_signals(
        self,
        day: int,
        options_chain: OptionsChain,
        portfolio_value: float
    ) -> List[Dict[str, Any]]:
        """Generate signals from all strategies."""
        all_signals = []
        
        for strategy in self.strategies.values():
            signals = strategy.generate_signals(day, options_chain, portfolio_value)
            all_signals.extend(signals)
        
        return all_signals
    
    def get_strategy(self, strategy_id: str) -> Optional[OptionsStrategy]:
        """Get a specific strategy."""
        return self.strategies.get(strategy_id)
    
    def get_all_strategies(self) -> List[OptionsStrategy]:
        """Get all strategies."""
        return list(self.strategies.values())
