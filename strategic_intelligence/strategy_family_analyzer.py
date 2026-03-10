"""
Strategy Family Analyzer for Strategic Intelligence.

Analyzes and ranks strategy families.

Author: AFC3 Strategic Intelligence
"""

from typing import Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class FamilyPerformance:
    """Performance metrics for a strategy family."""
    family: str
    experiment_count: int
    avg_sharpe: float
    avg_drawdown: float
    success_rate: float
    fitness_trend: str = "stable"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "family": self.family,
            "experiment_count": self.experiment_count,
            "avg_sharpe": self.avg_sharpe,
            "avg_drawdown": self.avg_drawdown,
            "success_rate": self.success_rate,
            "fitness_trend": self.fitness_trend
        }


class StrategyFamilyAnalyzer:
    """Analyzes strategy family performance."""
    
    FAMILIES = ["momentum", "mean_reversion", "breakout", "volatility", "stat_arb", "macro"]
    
    def __init__(self):
        self.family_history: Dict[str, List[FamilyPerformance]] = {f: [] for f in self.FAMILIES}
    
    def analyze(self, experiments: List[Dict[str, Any]]) -> List[FamilyPerformance]:
        """Analyze strategy family performance."""
        # Group by family
        family_data: Dict[str, List[Dict]] = {f: [] for f in self.FAMILIES}
        
        for exp in experiments:
            family = exp.get("family", "unknown")
            if family not in family_data:
                family_data[family] = []
            family_data[family].append(exp)
        
        # Calculate metrics for each family
        results = []
        
        for family, exps in family_data.items():
            if not exps:
                continue
            
            sharpes = [e.get("sharpe_ratio", 0) for e in exps]
            drawdowns = [e.get("max_drawdown", 0) for e in exps]
            approved = sum(1 for e in exps if e.get("status") == "approved")
            
            perf = FamilyPerformance(
                family=family,
                experiment_count=len(exps),
                avg_sharpe=sum(sharpes) / len(sharpes) if sharpes else 0,
                avg_drawdown=sum(drawdowns) / len(drawdowns) if drawdowns else 0,
                success_rate=approved / len(exps) if exps else 0
            )
            
            # Get trend
            if family in self.family_history and self.family_history[family]:
                recent = self.family_history[family][-3:]
                if recent:
                    old_sharpe = sum(p.avg_sharpe for p in recent) / len(recent)
                    if perf.avg_sharpe > old_sharpe * 1.1:
                        perf.fitness_trend = "improving"
                    elif perf.avg_sharpe < old_sharpe * 0.9:
                        perf.fitness_trend = "declining"
            
            results.append(perf)
            self.family_history[family].append(perf)
        
        # Sort by success rate and sharpe
        results.sort(key=lambda x: (x.success_rate, x.avg_sharpe), reverse=True)
        
        return results
    
    def rank_families(self, experiments: List[Dict[str, Any]]) -> List[str]:
        """Rank families by performance."""
        perfs = self.analyze(experiments)
        return [p.family for p in perfs]
    
    def get_top_family(self, experiments: List[Dict[str, Any]]) -> str:
        """Get top performing family."""
        ranked = self.rank_families(experiments)
        return ranked[0] if ranked else "momentum"
