from typing import Dict, Any
import asyncio
from agents.base_agent import BaseAgent

class QuantResearchAgent(BaseAgent):
    """
    Example implementation of a Quant Research Agent.
    """
    def __init__(self, name: str):
        super().__init__(name, "quant_research")

    async def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processes a quant research task.
        """
        print(f"Agent {self.name} (ID: {self.id}) processing quant research task: {task.get('action')}")
        # Simulate research work
        await asyncio.sleep(2)
        return {"result": f"Research completed for {task.get('action')}"}

    async def handle_message(self, message: Dict[str, Any]) -> None:
        """
        Handles incoming messages.
        """
        print(f"Agent {self.name} (ID: {self.id}) received message: {message.get('content')}")

class ExecutionAgent(BaseAgent):
    """
    Example implementation of an Execution Agent.
    """
    def __init__(self, name: str):
        super().__init__(name, "execution")

    async def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processes an execution task.
        """
        print(f"Agent {self.name} (ID: {self.id}) processing execution task: {task.get('action')}")
        # Simulate execution work
        await asyncio.sleep(1)
        return {"result": f"Execution completed for {task.get('action')}"}

    async def handle_message(self, message: Dict[str, Any]) -> None:
        """
        Handles incoming messages.
        """
        print(f"Agent {self.name} (ID: {self.id}) received message: {message.get('content')}")
