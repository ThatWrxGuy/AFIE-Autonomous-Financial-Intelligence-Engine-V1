"""Tests for Learning Engine"""
import pytest
import sys
sys.path.insert(0, '.')

from core.strategy_genome import StrategyGenome
from core.strategy_mutation_engine import StrategyMutationEngine
from core.performance_analysis_engine import PerformanceAnalysisEngine, StrategyPerformance
from agents.strategy_evolution_agent import StrategyEvolutionAgent

class TestStrategyGenome:
    def test_create_seed(self):
        g = StrategyGenome.create_seed("momentum")
        assert g.strategy_family == "momentum"
        assert len(g.parameters) > 0
    
    def test_to_dict(self):
        g = StrategyGenome.create_seed("mean_reversion")
        d = g.to_dict()
        assert "strategy_id" in d
        assert d["strategy_family"] == "mean_reversion"

class TestMutationEngine:
    def test_mutate_genome(self):
        engine = StrategyMutationEngine(mutation_rate=1.0)
        parent = StrategyGenome.create_seed("momentum")
        child = engine.mutate_genome(parent)
        assert child.generation == 1
        assert child.parent_id == parent.strategy_id
    
    def test_parameter_perturbation(self):
        engine = StrategyMutationEngine()
        g = StrategyGenome.create_seed("momentum")
        original = g.parameters.get("lookback_period", 0)
        g = engine.parameter_perturbation(g)
        # Value should be different (since mutation rate is high)

class TestPerformanceAnalysis:
    def test_compute_fitness(self):
        engine = PerformanceAnalysisEngine()
        perf = StrategyPerformance(
            strategy_id="test",
            sharpe_ratio=1.5,
            max_drawdown=0.1,
            win_rate=0.6,
            volatility=0.15,
            profit_factor=1.8
        )
        score = engine.compute_fitness_score(perf)
        assert score > 0
    
    def test_rank_strategies(self):
        engine = PerformanceAnalysisEngine()
        perfs = [
            StrategyPerformance("s1", sharpe_ratio=1.0),
            StrategyPerformance("s2", sharpe_ratio=2.0),
            StrategyPerformance("s3", sharpe_ratio=0.5)
        ]
        ranked = engine.rank_strategies_by_fitness(perfs)
        assert ranked[0][0].strategy_id == "s2"

class TestEvolutionAgent:
    @pytest.mark.asyncio
    async def test_agent_creation(self):
        agent = StrategyEvolutionAgent("Test")
        assert agent.name == "Test"
        assert agent.agent_type == "strategy_evolution"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
