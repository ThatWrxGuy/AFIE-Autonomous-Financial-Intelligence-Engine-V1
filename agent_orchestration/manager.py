from typing import Dict, List, Any
import asyncio
from agents.base_agent import BaseAgent, AgentStatus

class AgentOrchestrationManager:
    """
    Manages the lifecycle and interactions of multiple autonomous AI agents.
    """
    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}
        self.agent_types: Dict[str, List[str]] = {}

    def register_agent(self, agent: BaseAgent) -> str:
        """
        Registers a new agent with the Control Core.
        """
        self.agents[agent.id] = agent
        if agent.agent_type not in self.agent_types:
            self.agent_types[agent.agent_type] = []
        self.agent_types[agent.agent_type].append(agent.id)
        print(f"Agent registered: {agent.name} (ID: {agent.id}, Type: {agent.agent_type})")
        return agent.id

    def discover_agents(self, agent_type: str = None) -> List[Dict[str, Any]]:
        """
        Discovers agents of a specific type or all agents.
        """
        if agent_type:
            agent_ids = self.agent_types.get(agent_type, [])
            return [self.agents[aid].get_info() for aid in agent_ids]
        return [agent.get_info() for agent in self.agents.values()]

    async def route_task(self, agent_id: str, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Routes a task to a specific agent.
        """
        if agent_id not in self.agents:
            raise ValueError(f"Agent with ID {agent_id} not found.")
        
        agent = self.agents[agent_id]
        agent.set_status("busy")
        
        # Create proper task structure if not present
        if "id" not in task:
            task["id"] = task.get("id", "unknown")
        
        try:
            result = await agent.process_task(task)
            return result
        finally:
            agent.set_status("idle")

    async def broadcast_message(self, message: Dict[str, Any]) -> None:
        """
        Broadcasts a message to all registered agents.
        """
        tasks = [agent.handle_message(message) for agent in self.agents.values()]
        await asyncio.gather(*tasks)
