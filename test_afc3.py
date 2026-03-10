import asyncio
from agent_orchestration.manager import AgentOrchestrationManager
from task_scheduler.scheduler import TaskScheduler
from agents.example_agents import QuantResearchAgent, ExecutionAgent

async def test_afc3():
    """
    Test script for the AFIE Control Core (AFC3).
    """
    print("Testing AFIE Control Core (AFC3)...")
    
    # Initialize core components
    orchestration_manager = AgentOrchestrationManager()
    task_scheduler = TaskScheduler(orchestration_manager)
    
    # Register agents
    research_agent = QuantResearchAgent("Research-1")
    execution_agent = ExecutionAgent("Execution-1")
    
    orchestration_manager.register_agent(research_agent)
    orchestration_manager.register_agent(execution_agent)
    
    # Start the task scheduler in the background
    scheduler_task = asyncio.create_task(task_scheduler.run_scheduler())
    
    # Schedule tasks
    task1_id = await task_scheduler.schedule_task({
        "agent_type": "quant_research",
        "action": "analyze_volatility",
        "data": {"symbol": "AAPL"}
    }, priority=1)
    
    task2_id = await task_scheduler.schedule_task({
        "agent_type": "execution",
        "action": "place_order",
        "data": {"symbol": "AAPL", "quantity": 100}
    }, priority=2)
    
    # Wait for tasks to complete
    await asyncio.sleep(5)
    
    # Broadcast a message
    await orchestration_manager.broadcast_message({"content": "System update in progress."})
    
    # Clean up
    scheduler_task.cancel()
    print("AFC3 test completed.")

if __name__ == "__main__":
    asyncio.run(test_afc3())
