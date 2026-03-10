"""
Strategy Mutation Engine for AFC3 Learning Engine.

This module provides mutation operations for strategy genomes.

Capabilities:
- parameter mutation
- feature combination mutation
- asset universe mutation
- regime-specific mutation
- crossover between strategies

Author: AFC3 Learning Engine
"""

from typing import Dict, Any, List, Optional, Tuple
import random
import uuid

from core.strategy_genome import StrategyGenome, AVAILABLE_FEATURES


class StrategyMutationEngine:
    """
    Engine for mutating strategy genomes.
    
    Provides various mutation operations:
    - parameter_perturbation
    - parameter_scaling
    - feature_swap
    - feature_add
    - asset_universe_mutation
    - strategy_crossover
    """
    
    def __init__(self, mutation_rate: float = 0.1):
        self.mutation_rate = mutation_rate
    
    def should_mutate(self) -> bool:
        """Determine if mutation should occur."""
        return random.random() < self.mutation_rate
    
    def mutate_genome(self, genome: StrategyGenome) -> StrategyGenome:
        """
        Apply random mutations to a genome.
        
        Args:
            genome: Original genome
            
        Returns:
            Mutated genome
        """
        # Create a copy
        mutated = StrategyGenome(
            strategy_id=str(uuid.uuid4()),
            strategy_family=genome.strategy_family,
            parameters=genome.parameters.copy(),
            feature_set=genome.feature_set.copy(),
            risk_profile=genome.risk_profile,
            target_assets=genome.target_assets.copy(),
            expected_return=genome.expected_return,
            expected_volatility=genome.expected_volatility,
            generation=genome.generation + 1,
            parent_id=genome.strategy_id
        )
        
        # Apply mutations
        if self.should_mutate():
            mutated = self.parameter_perturbation(mutated)
        
        if self.should_mutate():
            mutated = self.parameter_scaling(mutated)
        
        if self.should_mutate():
            mutated = self.feature_swap(mutated)
        
        if self.should_mutate():
            mutated = self.asset_universe_mutation(mutated)
        
        return mutated
    
    def parameter_perturbation(self, genome: StrategyGenome) -> StrategyGenome:
        """
        Perturb numeric parameters by a random amount.
        
        Example: lookback_period = 20 → 22
        """
        if not genome.parameters:
            return genome
        
        param_name = random.choice(list(genome.parameters.keys()))
        value = genome.parameters[param_name]
        
        if isinstance(value, (int, float)):
            # Perturb by ±10%
            change = value * random.uniform(-0.1, 0.1)
            new_value = value + change
            
            # Keep within reasonable bounds
            if isinstance(value, int):
                new_value = max(1, int(new_value))
            else:
                new_value = max(0.001, new_value)
            
            genome.parameters[param_name] = new_value
        
        return genome
    
    def parameter_scaling(self, genome: StrategyGenome) -> StrategyGenome:
        """
        Scale a parameter by a factor.
        
        Example: entry_threshold = 2.0 → 2.3
        """
        if not genome.parameters:
            return genome
        
        # Select a threshold-like parameter
        threshold_params = ["entry_threshold", "exit_threshold", "stop_loss", "take_profit"]
        available = [p for p in threshold_params if p in genome.parameters]
        
        if available:
            param_name = random.choice(available)
            value = genome.parameters[param_name]
            
            if isinstance(value, (int, float)):
                # Scale by ±15%
                scale = random.uniform(0.85, 1.15)
                genome.parameters[param_name] = value * scale
        
        return genome
    
    def feature_swap(self, genome: StrategyGenome) -> StrategyGenome:
        """
        Replace one feature with another.
        
        Example: feature_set = ["returns", "volume"] → ["returns", "rsi"]
        """
        if not genome.feature_set or len(genome.feature_set) == 0:
            return genome
        
        # Replace one feature
        idx = random.randint(0, len(genome.feature_set) - 1)
        new_feature = random.choice(AVAILABLE_FEATURES)
        
        if new_feature not in genome.feature_set:
            genome.feature_set[idx] = new_feature
        
        return genome
    
    def feature_add(self, genome: StrategyGenome) -> StrategyGenome:
        """Add a new feature to the feature set."""
        if len(genome.feature_set) >= 5:  # Max 5 features
            return genome
        
        available = [f for f in AVAILABLE_FEATURES if f not in genome.feature_set]
        if available:
            new_feature = random.choice(available)
            genome.feature_set.append(new_feature)
        
        return genome
    
    def asset_universe_mutation(self, genome: StrategyGenome) -> StrategyGenome:
        """
        Mutate the target asset universe.
        
        Replace or add one asset.
        """
        all_assets = ["SPY", "QQQ", "IWM", "EFA", "EEM", "TLT", "GLD", "TNA", "TECL", "SOXL"]
        
        if len(genome.target_assets) >= 5:  # Max 5 assets
            return genome
        
        # Either add or replace
        if random.random() < 0.5 and genome.target_assets:
            # Replace
            idx = random.randint(0, len(genome.target_assets) - 1)
            new_asset = random.choice(all_assets)
            if new_asset not in genome.target_assets:
                genome.target_assets[idx] = new_asset
        else:
            # Add
            available = [a for a in all_assets if a not in genome.target_assets]
            if available:
                genome.target_assets.append(random.choice(available))
        
        return genome
    
    def strategy_crossover(self, genome1: StrategyGenome, genome2: StrategyGenome) -> StrategyGenome:
        """
        Perform crossover between two strategies.
        
        Combines parameters from both parents.
        """
        # Create child
        child = StrategyGenome(
            strategy_id=str(uuid.uuid4()),
            strategy_family=genome1.strategy_family,
            parameters={},
            feature_set=genome1.feature_set.copy(),
            risk_profile=genome1.risk_profile,
            target_assets=genome1.target_assets.copy(),
            generation=max(genome1.generation, genome2.generation) + 1,
            parent_id=genome1.strategy_id
        )
        
        # Mix parameters (50/50)
        all_params = set(genome1.parameters.keys()) | set(genome2.parameters.keys())
        for param in all_params:
            if param in genome1.parameters and param in genome2.parameters:
                child.parameters[param] = random.choice([
                    genome1.parameters[param],
                    genome2.parameters[param]
                ])
            elif param in genome1.parameters:
                child.parameters[param] = genome1.parameters[param]
            else:
                child.parameters[param] = genome2.parameters[param]
        
        # Mix features
        child.feature_set = list(set(genome1.feature_set) | set(genome2.feature_set))[:5]
        
        return child
    
    def generate_variants(
        self,
        parent: StrategyGenome,
        num_variants: int = 5
    ) -> List[StrategyGenome]:
        """
        Generate multiple variants from a parent genome.
        
        Args:
            parent: Parent genome
            num_variants: Number of variants to generate
            
        Returns:
            List of mutated genomes
        """
        variants = []
        
        for _ in range(num_variants):
            variant = self.mutate_genome(parent)
            variants.append(variant)
        
        return variants


def create_mutation_engine(mutation_rate: float = 0.1) -> StrategyMutationEngine:
    """Factory function to create mutation engine."""
    return StrategyMutationEngine(mutation_rate=mutation_rate)
