from typing import Dict, Any, List
import asyncio
import random
import time
from datetime import datetime
from agents.base_agent import BaseAgent, AgentResult

class MacroIntelligenceAgent(BaseAgent):
    """
    Macro Intelligence AI Agent for monitoring macroeconomic indicators and detecting regime changes.
    
    Uses standardized result envelopes.
    """
    def __init__(self, name: str):
        super().__init__(name, "macro_intelligence")

    async def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processes macro intelligence tasks.
        Returns standardized result envelope.
        """
        action = task.get("action")
        data = task.get("data", {})
        task_id = task.get("id", "unknown")
        
        start_time = time.time()
        
        print(f"Agent {self.name} (ID: {self.id}) processing {action} task.")
        
        try:
            if action == "monitor_indicators":
                result = await self.monitor_indicators(data.get("indicators", []))
            elif action == "detect_regime_changes":
                result = await self.detect_regime_changes(data.get("indicator_data", {}))
            elif action == "generate_regime_probability_scores":
                result = await self.generate_regime_probability_scores(data.get("current_state", {}))
            elif action == "send_alerts_to_risk_system":
                result = await self.send_alerts_to_risk_system(data.get("alert_data", {}))
            else:
                raise ValueError(f"Unknown action: {action}")
            
            duration = time.time() - start_time
            
            # Return standardized success envelope
            return AgentResult.success(
                agent_id=self.id,
                agent_type=self.agent_type,
                action=action,
                task_id=task_id,
                result=result,
                duration_seconds=duration
            )
            
        except Exception as e:
            # Return standardized error envelope
            return AgentResult.error(
                agent_id=self.id,
                agent_type=self.agent_type,
                action=action,
                task_id=task_id,
                error=str(e)
            )

    async def handle_message(self, message: Dict[str, Any]) -> None:
        """
        Handles incoming messages.
        """
        print(f"Agent {self.name} (ID: {self.id}) received message: {message.get('content')}")

    async def monitor_indicators(self, indicators: List[str]) -> Dict[str, Any]:
        """
        Monitors macroeconomic indicators.
        """
        # Simulate indicator monitoring
        await asyncio.sleep(2)
        indicator_values = {indicator: random.uniform(0, 100) for indicator in indicators}
        return {"status": "success", "indicator_values": indicator_values}

    async def detect_regime_changes(self, indicator_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Detects regime changes based on indicator analysis.
        """
        # Simulate regime change detection
        await asyncio.sleep(2.5)
        regimes = ["low_volatility", "high_volatility", "trending", "mean_reverting"]
        detected_regime = random.choice(regimes)
        return {"status": "success", "detected_regime": detected_regime, "confidence": random.uniform(0.7, 0.95)}

    async def generate_regime_probability_scores(self, current_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generates probability scores for different market regimes.
        """
        # Simulate regime probability score generation
        await asyncio.sleep(2)
        regimes = ["low_volatility", "high_volatility", "trending", "mean_reverting"]
        scores = {regime: random.uniform(0, 1) for regime in regimes}
        # Normalize scores to sum to 1
        total = sum(scores.values())
        normalized_scores = {k: v / total for k, v in scores.items()}
        return {"status": "success", "regime_probability_scores": normalized_scores}

    async def send_alerts_to_risk_system(self, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sends alerts to the portfolio risk system.
        """
        # Simulate sending alerts
        await asyncio.sleep(1)
        print(f"ALERT: {alert_data.get('message')}")
        return {"status": "success", "alert_sent": True}
