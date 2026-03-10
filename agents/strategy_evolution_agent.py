"""
Strategy Evolution Agent for AFC3 Learning Engine.

This agent analyzes research results and generates improved strategy candidates.

Responsibilities:
- analyze historical experiments
- identify profitable patterns
- mutate parameters of successful strategies
- generate new candidate strategies
- retire underperforming strategies
- prioritize promising strategy families

Actions:
- analyze_strategy_history
- identify_high_performing_patterns
- mutate_strategy_parameters
- generate_strategy_variants
- retire_weak_strategies
- prioritize_strategy_candidates

Author: AFC3 Learning Engine
"""

from typing import Dict, Any, List, Optional
import asyncio
import time
from datetime import datetime
import uuid

from agents.base_agent import BaseAgent, AgentResult
from core.strategy_genome import StrategyGenome, STRATEGY_FAMILIES
from core.strategy_mutation_engine import StrategyMutationEngine, create_mutation_engine
from core.performance_analysis_engine import (
    PerformanceAnalysisEngine,
    StrategyPerformance,
    create_analysis_engine
)
from core.data_contracts import ApprovedStrategy


class StrategyEvolutionAgent(BaseAgent):
    """
    Strategy Evolution AI Agent for learning and improvement.
    
    Analyzes past results and generates improved strategies.
    """
    
    def __init__(self, name: str):
        super().__init__(name, "strategy_evolution")
        
        # Components
        self.mutation_engine = create_mutation_engine(mutation_rate=0.3)
        self.analysis_engine = create_analysis_engine(risk_free_rate=0.02)
        
        # Memory references
        self.experiment_store = None
        self.long_term_memory = None
        self.short_term_memory = None
        self.event_bus = None
        
        # State
        self.active_candidates: List[StrategyGenome] = []
        self.retired_strategies: List[str] = []
        self.evolution_history: List[Dict[str, Any]] = []
        
        # Safety limits
        self.max_candidates_per_cycle = 20
        self.max_generation_depth = 10
        self.min_fitness_threshold = 30.0
    
    def set_experiment_store(self, store):
        """Set experiment store reference."""
        self.experiment_store = store
    
    def set_long_term_memory(self, memory):
        """Set long-term memory reference."""
        self.long_term_memory = memory
    
    def set_short_term_memory(self, memory):
        """Set short-term memory reference."""
        self.short_term_memory = memory
    
    def set_event_bus(self, bus):
        """Set event bus reference."""
        self.event_bus = bus
    
    async def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Process strategy evolution tasks."""
        action = task.get("action")
        data = task.get("data", {})
        task_id = task.get("id", "unknown")
        
        start_time = time.time()
        
        print(f"Agent {self.name} (ID: {self.id}) processing {action} task.")
        
        try:
            if action == "analyze_strategy_history":
                result = await self.analyze_strategy_history(data)
            elif action == "identify_high_performing_patterns":
                result = await self.identify_high_performing_patterns(data)
            elif action == "mutate_strategy_parameters":
                result = await self.mutate_strategy_parameters(data)
            elif action == "generate_strategy_variants":
                result = await self.generate_strategy_variants(data)
            elif action == "retire_weak_strategies":
                result = await self.retire_weak_strategies(data)
            elif action == "prioritize_strategy_candidates":
                result = await self.prioritize_strategy_candidates(data)
            elif action == "run_evolution_cycle":
                result = await self.run_evolution_cycle(data)
            else:
                raise ValueError(f"Unknown action: {action}")
            
            duration = time.time() - start_time
            
            return AgentResult.success(
                agent_id=self.id,
                agent_type=self.agent_type,
                action=action,
                task_id=task_id,
                result=result,
                duration_seconds=duration
            )
            
        except Exception as e:
            return AgentResult.error(
                agent_id=self.id,
                agent_type=self.agent_type,
                action=action,
                task_id=task_id,
                error=str(e)
            )
    
    async def handle_message(self, message: Dict[str, Any]) -> None:
        """Handle incoming messages."""
        print(f"Agent {self.name} (ID: {self.id}) received message: {message.get('content')}")
    
    async def analyze_strategy_history(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze historical experiments and performance."""
        limit = data.get("limit", 100)
        
        # Get experiments from store
        experiments = []
        if self.experiment_store:
            experiments = self.experiment_store.list_experiments(limit=limit)
        
        # Analyze performance
        performances = self.analysis_engine.analyze_from_experiments(experiments)
        
        # Rank by fitness
        ranked = self.analysis_engine.rank_strategies_by_fitness(performances)
        
        # Get top and bottom strategies
        top = ranked[:5] if len(ranked) >= 5 else ranked
        bottom = ranked[-5:] if len(ranked) >= 5 else ranked
        
        result = {
            "total_experiments": len(experiments),
            "total_strategies_analyzed": len(performances),
            "top_strategies": [
                {"strategy_id": p[0].strategy_id, "fitness": p[1], "sharpe": p[0].sharpe_ratio}
                for p in top
            ],
            "bottom_strategies": [
                {"strategy_id": p[0].strategy_id, "fitness": p[1], "sharpe": p[0].sharpe_ratio}
                for p in bottom
            ]
        }
        
        return result
    
    async def identify_high_performing_patterns(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Identify patterns in high-performing strategies."""
        limit = data.get("limit", 100)
        
        # Get experiments
        experiments = []
        if self.experiment_store:
            experiments = self.experiment_store.list_experiments(limit=limit)
        
        # Analyze
        performances = self.analysis_engine.analyze_from_experiments(experiments)
        
        # Find top performers
        top_performers = self.analysis_engine.identify_top_strategies(performances, top_n=10)
        
        # Identify patterns
        patterns = {
            "high_sharpe_families": [],
            "low_drawdown_families": [],
            "high_winrate_families": []
        }
        
        for perf in top_performers:
            if perf.sharpe_ratio > 1.0:
                patterns["high_sharpe_families"].append(perf.strategy_id)
            if perf.max_drawdown < 0.15:
                patterns["low_drawdown_families"].append(perf.strategy_id)
            if perf.win_rate > 0.55:
                patterns["high_winrate_families"].append(perf.strategy_id)
        
        result = {
            "patterns": patterns,
            "top_performers": [p.to_dict() for p in top_performers]
        }
        
        return result
    
    async def mutate_strategy_parameters(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Mutate parameters of a successful strategy."""
        genome_data = data.get("genome")
        
        if not genome_data:
            return {"error": "No genome provided"}
        
        # Create genome from data
        genome = StrategyGenome.from_dict(genome_data)
        
        # Generate variants
        num_variants = data.get("num_variants", 5)
        variants = self.mutation_engine.generate_variants(genome, num_variants)
        
        # Store as candidates
        self.active_candidates.extend(variants)
        
        # Emit events
        if self.event_bus:
            for variant in variants:
                from core.event_bus import Event
                event = Event(
                    event_type="strategy.mutation_generated",
                    source=self.agent_type,
                    payload=variant.to_dict()
                )
                await self.event_bus.publish(event)
        
        result = {
            "parent_id": genome.strategy_id,
            "variants_generated": len(variants),
            "variants": [v.to_dict() for v in variants]
        }
        
        return result
    
    async def generate_strategy_variants(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate new strategy variants from top performers."""
        limit = data.get("limit", 50)
        
        # Get experiments
        experiments = []
        if self.experiment_store:
            experiments = self.experiment_store.list_experiments(limit=limit)
        
        # Analyze
        performances = self.analysis_engine.analyze_from_experiments(experiments)
        
        # Get top strategies
        top_performers = self.analysis_engine.identify_top_strategies(performances, top_n=5)
        
        # Generate variants from each
        all_variants = []
        
        for perf in top_performers:
            # Create a seed genome for the strategy family
            genome = StrategyGenome.create_seed(strategy_family="momentum")
            genome.strategy_id = perf.strategy_id
            
            # Generate variants
            variants = self.mutation_engine.generate_variants(genome, num_variants=3)
            all_variants.extend(variants)
        
        # Limit total variants
        if len(all_variants) > self.max_candidates_per_cycle:
            all_variants = all_variants[:self.max_candidates_per_cycle]
        
        # Store
        self.active_candidates.extend(all_variants)
        
        # Store in memory
        if self.long_term_memory:
            for variant in all_variants:
                self.long_term_memory.store_model_output(
                    f"strategy_{variant.strategy_id}",
                    variant.to_dict()
                )
        
        result = {
            "total_variants": len(all_variants),
            "variants": [v.to_dict() for v in all_variants]
        }
        
        return result
    
    async def retire_weak_strategies(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Retire underperforming strategies."""
        limit = data.get("limit", 50)
        
        # Get experiments
        experiments = []
        if self.experiment_store:
            experiments = self.experiment_store.list_experiments(limit=limit)
        
        # Analyze
        performances = self.analysis_engine.analyze_from_experiments(experiments)
        
        # Find failing strategies
        failing = self.analysis_engine.identify_failing_strategies(performances, min_trades=5)
        
        # Retire them
        retired = []
        for perf in failing:
            if perf.strategy_id not in self.retired_strategies:
                self.retired_strategies.append(perf.strategy_id)
                retired.append(perf.strategy_id)
        
        # Emit events
        if self.event_bus and retired:
            from core.event_bus import Event
            for strategy_id in retired:
                event = Event(
                    event_type="strategy.retired",
                    source=self.agent_type,
                    payload={"strategy_id": strategy_id}
                )
                await self.event_bus.publish(event)
        
        result = {
            "retired_count": len(retired),
            "retired_strategies": retired
        }
        
        return result
    
    async def prioritize_strategy_candidates(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Prioritize strategy candidates by fitness."""
        # Get candidates from memory if available
        candidates = self.active_candidates.copy()
        
        if not candidates and self.long_term_memory:
            # Try to load from long-term memory
            models = self.long_term_memory.list_models(limit=100)
            for model in models:
                if "strategy_id" in model:
                    genome = StrategyGenome.from_dict(model)
                    candidates.append(genome)
        
        # Compute fitness for each (simplified - would need performance data)
        scored = []
        for candidate in candidates:
            # Simplified fitness based on generation
            fitness = 100 - (candidate.generation * 5)
            scored.append((candidate, fitness))
        
        # Sort by fitness
        scored.sort(key=lambda x: x[1], reverse=True)
        
        result = {
            "total_candidates": len(candidates),
            "top_candidates": [
                {"strategy_id": c[0].strategy_id, "fitness": c[1], "generation": c[0].generation}
                for c in scored[:10]
            ]
        }
        
        return result
    
    async def run_evolution_cycle(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Run a full evolution cycle."""
        print(f"Agent {self.name}: Starting evolution cycle")
        
        # Step 1: Analyze history
        analysis = await self.analyze_strategy_history({"limit": 50})
        print(f"Agent {self.name}: Analyzed {analysis['total_strategies_analyzed']} strategies")
        
        # Step 2: Generate variants
        variants = await self.generate_strategy_variants({})
        print(f"Agent {self.name}: Generated {variants['total_variants']} variants")
        
        # Step 3: Retire weak strategies
        retired = await self.retire_weak_strategies({})
        print(f"Agent {self.name}: Retired {retired['retired_count']} strategies")
        
        # Step 4: Get prioritized candidates
        prioritized = await self.prioritize_strategy_candidates({})
        print(f"Agent {self.name}: {prioritized['total_candidates']} candidates ready")
        
        # Emit evolution completed event
        if self.event_bus:
            from core.event_bus import Event
            event = Event(
                event_type="strategy.evolution_completed",
                source=self.agent_type,
                payload={
                    "variants_generated": variants["total_variants"],
                    "strategies_retired": retired["retired_count"],
                    "total_candidates": prioritized["total_candidates"]
                }
            )
            await self.event_bus.publish(event)
        
        return {
            "analysis": analysis,
            "variants": variants,
            "retired": retired,
            "prioritized": prioritized
        }
    
    def get_active_candidates(self) -> List[Dict[str, Any]]:
        """Get active strategy candidates."""
        return [c.to_dict() for c in self.active_candidates]
    
    def get_retired_strategies(self) -> List[str]:
        """Get list of retired strategy IDs."""
        return self.retired_strategies.copy()
