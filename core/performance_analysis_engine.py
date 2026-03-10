"""
Performance Analysis Engine for AFC3 Learning Engine.

This component analyzes experiment results and execution summaries.

It computes:
- Sharpe ratio
- drawdown distribution
- win rate
- volatility
- profit factor
- regime performance

Author: AFC3 Learning Engine
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
import statistics


@dataclass
class StrategyPerformance:
    """Performance metrics for a strategy."""
    strategy_id: str
    sharpe_ratio: float = 0.0
    max_drawdown: float = 0.0
    win_rate: float = 0.0
    volatility: float = 0.0
    profit_factor: float = 0.0
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "strategy_id": self.strategy_id,
            "sharpe_ratio": self.sharpe_ratio,
            "max_drawdown": self.max_drawdown,
            "win_rate": self.win_rate,
            "volatility": self.volatility,
            "profit_factor": self.profit_factor,
            "total_trades": self.total_trades,
            "winning_trades": self.winning_trades,
            "losing_trades": self.losing_trades,
            "avg_win": self.avg_win,
            "avg_loss": self.avg_loss
        }


class PerformanceAnalysisEngine:
    """
    Engine for analyzing strategy performance.
    
    Analyzes experiment results and execution summaries to compute
    performance metrics.
    """
    
    def __init__(self, risk_free_rate: float = 0.02):
        self.risk_free_rate = risk_free_rate
    
    def analyze_from_experiments(
        self,
        experiments: List[Dict[str, Any]]
    ) -> List[StrategyPerformance]:
        """Analyze performance from experiment data."""
        performances = []
        
        # Handle case where experiments might be experiment objects
        exp_dicts = []
        for exp in experiments:
            if hasattr(exp, 'to_dict'):
                exp_dicts.append(exp.to_dict())
            else:
                exp_dicts.append(exp)
        
        # Group experiments by strategy
        strategy_experiments = {}
        for exp in exp_dicts:
            strategy_id = exp.get("pipeline_run_id", "unknown")
            if strategy_id not in strategy_experiments:
                strategy_experiments[strategy_id] = []
            strategy_experiments[strategy_id].append(exp)
        
        # Analyze each strategy
        for strategy_id, exps in strategy_experiments.items():
            perf = self.analyze_strategy_experiments(strategy_id, exps)
            performances.append(perf)
        
        return performances
    
    def analyze_strategy_experiments(
        self,
        strategy_id: str,
        experiments: List[Dict[str, Any]]
    ) -> StrategyPerformance:
        """Analyze experiments for a single strategy."""
        perf = StrategyPerformance(strategy_id=strategy_id)
        
        if not experiments:
            return perf
        
        # Extract returns from experiments
        returns = []
        trades = []
        
        for exp in experiments:
            # Get final result
            final_result = exp.get("final_result") or {}
            
            # Extract return
            ret = final_result.get("total_return")
            if ret is not None:
                returns.append(ret)
            
            # Extract trade info
            steps = exp.get("step_results", [])
            for step in steps:
                step_result = step.get("result", {})
                if "sharpe_ratio" in step_result:
                    perf.sharpe_ratio = step_result.get("sharpe_ratio", 0)
                if "max_drawdown" in step_result:
                    perf.max_drawdown = max(perf.max_drawdown, step_result.get("max_drawdown", 0))
        
        # Compute metrics
        if returns:
            perf.total_trades = len(returns)
            perf.volatility = statistics.stdev(returns) if len(returns) > 1 else 0.0
            perf.win_rate = sum(1 for r in returns if r > 0) / len(returns) if returns else 0.0
            
            # Calculate Sharpe ratio
            if perf.volatility > 0:
                mean_return = statistics.mean(returns)
                perf.sharpe_ratio = (mean_return - self.risk_free_rate) / perf.volatility
            
            # Calculate profit factor
            wins = [r for r in returns if r > 0]
            losses = [abs(r) for r in returns if r < 0]
            
            if wins:
                perf.winning_trades = len(wins)
                perf.avg_win = statistics.mean(wins)
            
            if losses:
                perf.losing_trades = len(losses)
                perf.avg_loss = statistics.mean(losses)
            
            if perf.avg_loss > 0:
                perf.profit_factor = perf.avg_win / perf.avg_loss if perf.avg_loss > 0 else 0
        
        return perf
    
    def identify_top_strategies(
        self,
        performances: List[StrategyPerformance],
        top_n: int = 10
    ) -> List[StrategyPerformance]:
        """Identify top-performing strategies by Sharpe ratio."""
        sorted_perf = sorted(
            performances,
            key=lambda p: p.sharpe_ratio,
            reverse=True
        )
        return sorted_perf[:top_n]
    
    def identify_failing_strategies(
        self,
        performances: List[StrategyPerformance],
        min_trades: int = 5
    ) -> List[StrategyPerformance]:
        """Identify strategies that are failing."""
        failing = []
        
        for perf in performances:
            if perf.total_trades < min_trades:
                continue
            if perf.sharpe_ratio < 0 or perf.win_rate < 0.4:
                failing.append(perf)
        
        return failing
    
    def identify_unstable_strategies(
        self,
        performances: List[StrategyPerformance],
        vol_threshold: float = 0.3
    ) -> List[StrategyPerformance]:
        """Identify strategies with high volatility."""
        unstable = []
        
        for perf in performances:
            if perf.volatility > vol_threshold:
                unstable.append(perf)
        
        return unstable
    
    def compute_fitness_score(
        self,
        perf: StrategyPerformance,
        weights: Optional[Dict[str, float]] = None
    ) -> float:
        """
        Compute a fitness score for a strategy.
        
        Args:
            perf: Strategy performance
            weights: Custom weights for each metric
            
        Returns:
            Fitness score (0-100)
        """
        if weights is None:
            weights = {
                "sharpe_ratio": 0.35,
                "win_rate": 0.20,
                "profit_factor": 0.20,
                "drawdown": 0.15,
                "stability": 0.10
            }
        
        # Normalize Sharpe (typically -2 to 4) to 0-100
        sharpe_score = min(max((perf.sharpe_ratio + 2) * 20, 0), 100)
        
        # Win rate is already 0-1
        win_score = perf.win_rate * 100
        
        # Profit factor (typically 0-3) to 0-100
        profit_score = min(perf.profit_factor * 33.3, 100)
        
        # Drawdown (0-1) - invert so lower is better
        drawdown_score = (1 - min(perf.max_drawdown, 1)) * 100
        
        # Stability - inverse of volatility
        stability_score = max(100 - perf.volatility * 100, 0)
        
        # Weighted sum
        fitness = (
            sharpe_score * weights.get("sharpe_ratio", 0.35) +
            win_score * weights.get("win_rate", 0.20) +
            profit_score * weights.get("profit_factor", 0.20) +
            drawdown_score * weights.get("drawdown", 0.15) +
            stability_score * weights.get("stability", 0.10)
        )
        
        return fitness
    
    def rank_strategies_by_fitness(
        self,
        performances: List[StrategyPerformance]
    ) -> List[Tuple[StrategyPerformance, float]]:
        """Rank strategies by fitness score."""
        ranked = []
        
        for perf in performances:
            fitness = self.compute_fitness_score(perf)
            ranked.append((perf, fitness))
        
        # Sort by fitness descending
        ranked.sort(key=lambda x: x[1], reverse=True)
        
        return ranked


def create_analysis_engine(risk_free_rate: float = 0.02) -> PerformanceAnalysisEngine:
    """Factory function to create analysis engine."""
    return PerformanceAnalysisEngine(risk_free_rate=risk_free_rate)
