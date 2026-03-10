"""
Feature Engineering Pipeline for AFC3 Data Infrastructure.

Computes technical indicators and features for strategies.

Author: AFC3 Data Infrastructure
"""

from typing import Dict, Any, List, Optional
import statistics
import math

from data.schemas.market_data import OHLCVData, FeatureData


class FeatureEngine:
    """
    Feature engineering engine.
    
    Computes technical indicators and features.
    """
    
    def __init__(self):
        self.feature_functions = {
            "sma": self.compute_sma,
            "ema": self.compute_ema,
            "volatility": self.compute_volatility,
            "momentum": self.compute_momentum,
            "rsi": self.compute_rsi,
            "zscore": self.compute_zscore,
            "atr": self.compute_atr,
            "macd": self.compute_macd,
            "bollinger_bands": self.compute_bollinger_bands,
            "returns": self.compute_returns
        }
    
    def compute_sma(self, prices: List[float], period: int = 20) -> Optional[float]:
        """Compute Simple Moving Average."""
        if len(prices) < period:
            return None
        return sum(prices[-period:]) / period
    
    def compute_ema(self, prices: List[float], period: int = 20) -> Optional[float]:
        """Compute Exponential Moving Average."""
        if len(prices) < period:
            return None
        
        multiplier = 2 / (period + 1)
        ema = prices[0]
        
        for price in prices[1:]:
            ema = (price * multiplier) + (ema * (1 - multiplier))
        
        return ema
    
    def compute_volatility(self, returns: List[float], period: int = 20) -> Optional[float]:
        """Compute volatility (standard deviation of returns)."""
        if len(returns) < period:
            return None
        return statistics.stdev(returns[-period:]) if len(returns) > 1 else 0
    
    def compute_momentum(self, prices: List[float], period: int = 10) -> Optional[float]:
        """Compute momentum (rate of change)."""
        if len(prices) < period:
            return None
        return (prices[-1] - prices[-period]) / prices[-period]
    
    def compute_rsi(self, prices: List[float], period: int = 14) -> Optional[float]:
        """Compute Relative Strength Index."""
        if len(prices) < period + 1:
            return None
        
        gains = []
        losses = []
        
        for i in range(1, len(prices)):
            change = prices[i] - prices[i-1]
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))
        
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        
        if avg_loss == 0:
            return 100
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def compute_zscore(self, prices: List[float], period: int = 20) -> Optional[float]:
        """Compute z-score."""
        if len(prices) < period:
            return None
        
        recent = prices[-period:]
        mean = statistics.mean(recent)
        std = statistics.stdev(recent) if len(recent) > 1 else 1
        
        if std == 0:
            return 0
        
        return (prices[-1] - mean) / std
    
    def compute_atr(self, bars: List[OHLCVData], period: int = 14) -> Optional[float]:
        """Compute Average True Range."""
        if len(bars) < period + 1:
            return None
        
        true_ranges = []
        for i in range(1, len(bars)):
            high = bars[i].high
            low = bars[i].low
            prev_close = bars[i-1].close
            
            tr = max(
                high - low,
                abs(high - prev_close),
                abs(low - prev_close)
            )
            true_ranges.append(tr)
        
        if len(true_ranges) < period:
            return None
        
        return sum(true_ranges[-period:]) / period
    
    def compute_macd(
        self,
        prices: List[float],
        fast: int = 12,
        slow: int = 26,
        signal: int = 9
    ) -> Optional[Dict[str, float]]:
        """Compute MACD."""
        if len(prices) < slow:
            return None
        
        ema_fast = self.compute_ema(prices, fast)
        ema_slow = self.compute_ema(prices, slow)
        
        if ema_fast is None or ema_slow is None:
            return None
        
        macd_line = ema_fast - ema_slow
        
        # Signal line would need historical MACD values
        # Simplified version
        return {"macd": macd_line, "signal": macd_line * 0.9}
    
    def compute_bollinger_bands(
        self,
        prices: List[float],
        period: int = 20,
        std_dev: float = 2.0
    ) -> Optional[Dict[str, float]]:
        """Compute Bollinger Bands."""
        if len(prices) < period:
            return None
        
        recent = prices[-period:]
        sma = statistics.mean(recent)
        std = statistics.stdev(recent) if len(recent) > 1 else 1
        
        return {
            "upper": sma + (std * std_dev),
            "middle": sma,
            "lower": sma - (std * std_dev)
        }
    
    def compute_returns(self, prices: List[float]) -> List[float]:
        """Compute returns."""
        if len(prices) < 2:
            return []
        
        returns = []
        for i in range(1, len(prices)):
            ret = (prices[i] - prices[i-1]) / prices[i-1]
            returns.append(ret)
        
        return returns
    
    def compute_features_for_bars(
        self,
        bars: List[OHLCVData],
        feature_names: List[str]
    ) -> List[FeatureData]:
        """Compute multiple features for bars."""
        features = []
        
        # Extract price list
        closes = [bar.close for bar in bars]
        highs = [bar.high for bar in bars]
        lows = [bar.low for bar in bars]
        
        for feature_name in feature_names:
            if feature_name == "sma":
                val = self.compute_sma(closes)
                if val:
                    features.append(FeatureData(
                        asset_symbol=bars[-1].asset_symbol,
                        feature_name="sma_20",
                        value=val,
                        parameters={"period": 20}
                    ))
            
            elif feature_name == "volatility":
                rets = self.compute_returns(closes)
                val = self.compute_volatility(rets)
                if val:
                    features.append(FeatureData(
                        asset_symbol=bars[-1].asset_symbol,
                        feature_name="volatility_20",
                        value=val,
                        parameters={"period": 20}
                    ))
            
            elif feature_name == "momentum":
                val = self.compute_momentum(closes)
                if val:
                    features.append(FeatureData(
                        asset_symbol=bars[-1].asset_symbol,
                        feature_name="momentum_10",
                        value=val,
                        parameters={"period": 10}
                    ))
            
            elif feature_name == "zscore":
                val = self.compute_zscore(closes)
                if val is not None:
                    features.append(FeatureData(
                        asset_symbol=bars[-1].asset_symbol,
                        feature_name="zscore_20",
                        value=val,
                        parameters={"period": 20}
                    ))
            
            elif feature_name == "rsi":
                val = self.compute_rsi(closes)
                if val:
                    features.append(FeatureData(
                        asset_symbol=bars[-1].asset_symbol,
                        feature_name="rsi_14",
                        value=val,
                        parameters={"period": 14}
                    ))
        
        return features
    
    def get_available_features(self) -> List[str]:
        """Get list of available features."""
        return list(self.feature_functions.keys())


# Global feature engine
_feature_engine = None


def get_feature_engine() -> FeatureEngine:
    """Get global feature engine."""
    global _feature_engine
    if _feature_engine is None:
        _feature_engine = FeatureEngine()
    return _feature_engine
