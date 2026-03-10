"""
Strategic Intelligence Agent for AFC3.

Meta-level system decision maker.

Author: AFC3 Strategic Intelligence
"""

from typing import Dict, Any, List, Optional
import asyncio

from agents.base_agent import BaseAgent, AgentResult
from strategic_intelligence.performance_analyzer import PerformanceAnalyzer
from strategic_intelligence.strategy_family_analyzer import StrategyFamilyAnalyzer
from strategic_intelligence.research_director import ResearchDirector, ComputeAllocator, PortfolioPolicyAdvisor


class StrategicIntelligenceAgent(BaseAgent):
    """
    Strategic Intelligence Agent.
    
    Acts as the executive decision maker for AFIE.
    """
    
    def __init__(self, name: str = "Strategic Intelligence"):
        super().__init__(name, "strategic_intelligence")
        
        # Analyzers
        self.performance_analyzer = PerformanceAnalyzer()
        self.family_analyzer = StrategyFamilyAnalyzer()
        self.research_director = ResearchDirector()
        self.compute_allocator = ComputeAllocator()
        self.portfolio_advisor = PortfolioPolicyAdvisor()
        
        # Memory references
        self.experiment_store = None
        self.long_term_memory = None
        
        # Event bus
        self.event_bus = None
    
    def set_experiment_store(self, store):
        self.experiment_store = store
    
    def set_long_term_memory(self, memory):
        self.long_term_memory = memory
    
    def set_event_bus(self, bus):
        self.event_bus = bus
    
    async def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Process strategic intelligence tasks."""
        action = task.get("action")
        data = task.get("data", {})
        
        try:
            if action == "analyze_system_performance":
                result = await self.analyze_system_performance(data)
            elif action == "rank_strategy_families":
                result = await self.rank_strategy_families(data)
            elif action == "update_research_priorities":
                result = await self.update_research_priorities(data)
            elif action == "optimize_compute_allocation":
                result = await self.optimize_compute_allocation(data)
            elif action == "advise_portfolio_policy":
                result = await self.advise_portfolio_policy(data)
            elif action == "run_strategic_analysis":
                result = await self.run_strategic_analysis(data)
            else:
                raise ValueError(f"Unknown action: {action}")
            
            return AgentResult.success(
                agent_id=self.id,
                agent_type=self.agent_type,
                action=action,
                task_id=task.get("id", "unknown"),
                result=result
            )
        except Exception as e:
            return AgentResult.error(
                agent_id=self.id,
                agent_type=self.agent_type,
                action=action,
                task_id=task.get("id", "unknown"),
                error=str(e)
            )
    
    async def analyze_system_performance(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze overall system performance."""
        # Get experiments
        experiments = []
        if self.experiment_store:
            experiments = self.experiment_store.list_experiments(limit=100)
        
        # Get compute stats
        from compute.compute_engine import get_compute_engine
        engine = get_compute_engine()
        compute_stats = engine.get_stats()["jobs"]
        
        # Analyze
        report = self.performance_analyzer.analyze(experiments, compute_stats, {})
        
        return {
            "performance_report": report.to_dict(),
            "trends": {
                "sharpe": self.performance_analyzer.get_trend("avg_sharpe"),
                "drawdown": self.performance_analyzer.get_trend("avg_drawdown"),
                "throughput": self.performance_analyzer.get_trend("compute_throughput")
            }
        }
    
    async def handle_message(self, message: Dict[str, Any]) -> None:
        """Handle incoming messages."""
        pass
    
    async def rank_strategy_families(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Rank strategy families."""
        experiments = []
        if self.experiment_store:
            experiments = self.experiment_store.list_experiments(limit=100)
        
        # Add family info to experiments
        for exp in experiments:
            if "family" not in exp:
                import random
                families = ["momentum", "mean_reversion", "breakout", "volatility"]
                exp["family"] = random.choice(families)
        
        ranked = self.family_analyzer.rank_families(experiments)
        
        return {"ranked_families": ranked, "top_family": ranked[0] if ranked else None}
    
    async def update_research_priorities(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update research priorities."""
        experiments = []
        if self.experiment_store:
            experiments = self.experiment_store.list_experiments(limit=100)
        
        # Get family performance
        family_perf = self.family_analyzer.analyze(experiments)
        
        # Update priorities
        priorities = self.research_director.update_priorities([fp.to_dict() for fp in family_perf])
        
        return {
            "priorities": [{"family": p.family, "allocation": p.allocation_percent, "reason": p.reason} 
                         for p in priorities]
        }
    
    async def optimize_compute_allocation(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize compute allocation."""
        from compute.compute_engine import get_compute_engine
        engine = get_compute_engine()
        
        stats = engine.get_stats()
        
        allocation = self.compute_allocator.optimize(
            stats.get("jobs", {}),
            stats.get("queue", {})
        )
        
        return {"compute_allocation": allocation}
    
    async def advise_portfolio_policy(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Advise on portfolio policy."""
        experiments = []
        if self.experiment_store:
            experiments = self.experiment_store.list_experiments(limit=100)
        
        suggestions = self.portfolio_advisor.analyze({}, experiments)
        
        return {
            "suggestions": [{"parameter": s.parameter, "current": s.current_value, 
                          "suggested": s.suggested_value, "reason": s.reason}
                         for s in suggestions]
        }
    
    async def run_strategic_analysis(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Run full strategic analysis."""
        perf = await self.analyze_system_performance({})
        families = await self.rank_strategy_families({})
        priorities = await self.update_research_priorities({})
        compute = await self.optimize_compute_allocation({})
        portfolio = await self.advise_portfolio_policy({})
        
        # Publish events
        if self.event_bus:
            from core.event_bus import Event
            await self.event_bus.publish(Event(
                event_type="strategy_family_ranked",
                source=self.agent_type,
                payload=families
            ))
        
        return {
            "performance": perf,
            "families": families,
            "priorities": priorities,
            "compute": compute,
            "portfolio": portfolio
        }
