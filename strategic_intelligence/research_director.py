"""
Research Director for Strategic Intelligence.

Decides research priorities based on performance.

Author: AFC3 Strategic Intelligence
"""

from typing import Dict, Any, List
from dataclasses import dataclass


@dataclass
class ResearchPriority:
    """Research priority recommendation."""
    family: str
    allocation_percent: float
    reason: str


class ResearchDirector:
    """Directs research priorities."""
    
    def __init__(self):
        self.current_priorities: Dict[str, float] = {
            "momentum": 0.25,
            "mean_reversion": 0.20,
            "breakout": 0.15,
            "volatility": 0.15,
            "stat_arb": 0.15,
            "macro": 0.10
        }
    
    def update_priorities(
        self,
        family_performance: List[Dict[str, Any]]
    ) -> List[ResearchPriority]:
        """Update research priorities based on performance."""
        if not family_performance:
            return self._get_default_priorities()
        
        # Calculate new allocations
        total_score = sum(p.get("success_rate", 0) * p.get("avg_sharpe", 0) 
                        for p in family_performance)
        
        new_priorities = []
        
        for perf in family_performance:
            family = perf.get("family", "unknown")
            score = (perf.get("success_rate", 0) * perf.get("avg_sharpe", 0))
            allocation = (score / total_score) if total_score > 0 else 0.2
            
            new_priorities.append(ResearchPriority(
                family=family,
                allocation_percent=allocation,
                reason=f"Success rate: {perf.get('success_rate', 0):.1%}, Sharpe: {perf.get('avg_sharpe', 0):.2f}"
            ))
        
        # Update current priorities
        for p in new_priorities:
            self.current_priorities[p.family] = p.allocation_percent
        
        return new_priorities
    
    def _get_default_priorities(self) -> List[ResearchPriority]:
        """Get default priorities."""
        return [ResearchPriority(f, v, "Default allocation") 
                for f, v in self.current_priorities.items()]
    
    def get_priorities(self) -> Dict[str, float]:
        """Get current priorities."""
        return self.current_priorities.copy()


"""
Compute Allocator for Strategic Intelligence.

Optimizes compute resource allocation.

Author: AFC3 Strategic Intelligence
"""

from typing import Dict, Any


class ComputeAllocator:
    """Allocates compute resources."""
    
    def __init__(self):
        self.allocation = {
            "backtest": 0.35,
            "simulation": 0.25,
            "learning": 0.20,
            "portfolio": 0.10,
            "feature": 0.10
        }
    
    def optimize(
        self,
        job_stats: Dict[str, Any],
        throughput: Dict[str, float]
    ) -> Dict[str, float]:
        """Optimize compute allocation."""
        # Simple optimization: favor areas with high throughput
        total = sum(throughput.values()) if throughput else 1
        
        if total > 0:
            for key in self.allocation:
                if key in throughput:
                    self.allocation[key] = min(0.5, max(0.1, throughput[key] / total))
        
        return self.allocation.copy()
    
    def get_allocation(self) -> Dict[str, float]:
        """Get current allocation."""
        return self.allocation.copy()


"""
Portfolio Policy Advisor for Strategic Intelligence.

Suggests portfolio policy adjustments.

Author: AFC3 Strategic Intelligence
"""

from typing import Dict, Any, List
from dataclasses import dataclass


@dataclass
class PolicySuggestion:
    """Portfolio policy suggestion."""
    parameter: str
    current_value: float
    suggested_value: float
    reason: str


class PortfolioPolicyAdvisor:
    """Advises on portfolio policies."""
    
    def __init__(self):
        self.current_policy = {
            "max_leverage": 2.0,
            "max_allocation_per_strategy": 0.25,
            "min_sharpe_ratio": 0.5,
            "max_drawdown_threshold": 0.20
        }
    
    def analyze(
        self,
        portfolio_stats: Dict[str, Any],
        experiments: List[Dict[str, Any]]
    ) -> List[PolicySuggestion]:
        """Analyze and suggest policy changes."""
        suggestions = []
        
        # Analyze drawdowns
        drawdowns = [e.get("max_drawdown", 0) for e in experiments]
        avg_dd = sum(drawdowns) / len(drawdowns) if drawdowns else 0.15
        
        if avg_dd > 0.20:
            suggestions.append(PolicySuggestion(
                parameter="max_drawdown_threshold",
                current_value=self.current_policy["max_drawdown_threshold"],
                suggested_value=avg_dd * 0.9,
                reason=f"Avg drawdown {avg_dd:.1%} exceeds threshold"
            ))
        
        # Analyze sharpe
        sharpes = [e.get("sharpe_ratio", 0) for e in experiments]
        avg_sharpe = sum(sharpes) / len(sharpes) if sharpes else 0.5
        
        if avg_sharpe > 1.0:
            suggestions.append(PolicySuggestion(
                parameter="min_sharpe_ratio",
                current_value=self.current_policy["min_sharpe_ratio"],
                suggested_value=min(1.5, avg_sharpe * 0.8),
                reason=f"Avg sharpe {avg_sharpe:.2f} is strong"
            ))
        
        return suggestions
    
    def get_policy(self) -> Dict[str, float]:
        """Get current policy."""
        return self.current_policy.copy()
