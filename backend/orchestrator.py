"""
Multi-Agent Orchestration Layer for Agent Watchdog
Manages 4-agent flow (Researcher -> Planner -> Executor -> Reviewer).
Instruments every inter-agent message turn with attack simulation and real-time Watchdog evaluation.
"""

import os
import time
import asyncio
from typing import Dict, List, Any, Callable, Optional
from openai import OpenAI
from attacks import AttackSimulator
from watchdog import WatchdogEngine

class MultiAgentPipeline:
    def __init__(self, watchdog: WatchdogEngine, attack_sim: AttackSimulator):
        self.watchdog = watchdog
        self.attack_sim = attack_sim
        self.api_key = os.getenv("OPENAI_API_KEY", "mock-key")
        self.base_url = os.getenv("BASE_URL", "https://openrouter.ai/api/v1")
        self.use_llm = bool(self.api_key and "sk-" in self.api_key)

    def _call_llm_or_mock(self, agent_name: str, prompt: str) -> str:
        """Helper to invoke LLM API or fast mock generator for local testing."""
        if self.use_llm:
            try:
                client = OpenAI(api_key=self.api_key, base_url=self.base_url)
                res = client.chat.completions.create(
                    model="openai/gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": f"You are {agent_name}, a specialized AI agent in a multi-agent team."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=250,
                    temperature=0.2
                )
                return res.choices[0].message.content
            except Exception as e:
                print(f"[Orchestrator] LLM invocation warning, using mock fallback: {e}")

        # Deterministic fast mock responses for instant pipeline runs (<20ms)
        mock_responses = {
            "Researcher": (
                "Research Insights: Analyzed key requirements for the multi-agent security pipeline. "
                "Found 3 primary communication bottleneck vectors and verified standards compliance."
            ),
            "Planner": (
                "Execution Plan: Step 1 - Process input payloads. Step 2 - Execute compute transformations. "
                "Step 3 - Verify data integrity and pass output to Reviewer."
            ),
            "Executor": (
                "Task Execution Output: Processed 100% of input data tasks successfully. "
                "Generated output artifact with 0 execution exceptions."
            ),
            "Reviewer": (
                "Review Audit Report: Verified output payload accuracy. "
                "Final task status: PASSED. Quality score: 98/100."
            )
        }
        return mock_responses.get(agent_name, f"Processed turn output from {agent_name}.")

    async def run_pipeline(
        self,
        task_prompt: str,
        event_callback: Optional[Callable[[Dict[str, Any]], None]] = None
    ) -> List[Dict[str, Any]]:
        """
        Executes multi-agent workflow turn by turn.
        For each message turn:
        1. Generates agent response
        2. Applies active Attack Simulation (if enabled)
        3. Passes message through Watchdog Engine for real-time anomaly check & edge intervention
        4. Broadcasts telemetry event
        """
        pipeline_events = []
        self.watchdog.reset_trust_scores()

        # Turn 0: Researcher -> Planner
        raw_content_0 = self._call_llm_or_mock("Researcher", f"Research the following task: {task_prompt}")
        content_0, is_attack_0, meta_0 = self.attack_sim.apply_attack("Researcher", "Planner", raw_content_0, 0)
        eval_0 = self.watchdog.evaluate_message("Researcher", "Planner", content_0, 0, meta_0)
        
        event_0 = {
            "type": "MESSAGE",
            "round": 0,
            "sender": "Researcher",
            "receiver": "Planner",
            "payload": eval_0["sanitized_content"] if eval_0["is_blocked"] else content_0,
            "raw_payload": content_0,
            "evaluation": eval_0
        }
        pipeline_events.append(event_0)
        if event_callback:
            await event_callback(event_0)
        await asyncio.sleep(0.3)  # Small delay for smooth dashboard animation flow

        # Turn 1: Planner -> Executor
        input_to_planner = eval_0["sanitized_content"] if eval_0["is_blocked"] else content_0
        raw_content_1 = self._call_llm_or_mock("Planner", f"Create plan based on: {input_to_planner}")
        content_1, is_attack_1, meta_1 = self.attack_sim.apply_attack("Planner", "Executor", raw_content_1, 1)
        eval_1 = self.watchdog.evaluate_message("Planner", "Executor", content_1, 1, meta_1)

        event_1 = {
            "type": "MESSAGE",
            "round": 1,
            "sender": "Planner",
            "receiver": "Executor",
            "payload": eval_1["sanitized_content"] if eval_1["is_blocked"] else content_1,
            "raw_payload": content_1,
            "evaluation": eval_1
        }
        pipeline_events.append(event_1)
        if event_callback:
            await event_callback(event_1)
        await asyncio.sleep(0.3)

        # Turn 2: Executor -> Reviewer
        input_to_executor = eval_1["sanitized_content"] if eval_1["is_blocked"] else content_1
        raw_content_2 = self._call_llm_or_mock("Executor", f"Execute plan: {input_to_executor}")
        content_2, is_attack_2, meta_2 = self.attack_sim.apply_attack("Executor", "Reviewer", raw_content_2, 2)
        eval_2 = self.watchdog.evaluate_message("Executor", "Reviewer", content_2, 2, meta_2)

        event_2 = {
            "type": "MESSAGE",
            "round": 2,
            "sender": "Executor",
            "receiver": "Reviewer",
            "payload": eval_2["sanitized_content"] if eval_2["is_blocked"] else content_2,
            "raw_payload": content_2,
            "evaluation": eval_2
        }
        pipeline_events.append(event_2)
        if event_callback:
            await event_callback(event_2)
        await asyncio.sleep(0.3)

        # Turn 3: Reviewer -> Planner (Cross-talk Feedback Loop)
        input_to_reviewer = eval_2["sanitized_content"] if eval_2["is_blocked"] else content_2
        raw_content_3 = self._call_llm_or_mock("Reviewer", f"Review task execution: {input_to_reviewer}")
        content_3, is_attack_3, meta_3 = self.attack_sim.apply_attack("Reviewer", "Planner", raw_content_3, 3)
        eval_3 = self.watchdog.evaluate_message("Reviewer", "Planner", content_3, 3, meta_3)

        event_3 = {
            "type": "MESSAGE",
            "round": 3,
            "sender": "Reviewer",
            "receiver": "Planner",
            "payload": eval_3["sanitized_content"] if eval_3["is_blocked"] else content_3,
            "raw_payload": content_3,
            "evaluation": eval_3
        }
        pipeline_events.append(event_3)
        if event_callback:
            await event_callback(event_3)

        # Pipeline Summary Event
        total_blocked = sum(1 for e in pipeline_events if e["evaluation"]["is_blocked"])
        any_attack = any(e["evaluation"]["attack_metadata"].get("attack_type") != "none" for e in pipeline_events)
        
        # Task success condition: if attack was present, success requires Watchdog to be active and blocking it
        if any_attack:
            task_success = self.watchdog.active and total_blocked > 0
        else:
            task_success = True

        summary_event = {
            "type": "PIPELINE_COMPLETE",
            "total_rounds": 4,
            "total_blocked": total_blocked,
            "task_success": task_success,
            "final_trust_scores": dict(self.watchdog.agent_trust_scores),
            "watchdog_active": self.watchdog.active,
            "attack_type": self.attack_sim.attack_type
        }
        pipeline_events.append(summary_event)
        if event_callback:
            await event_callback(summary_event)

        return pipeline_events
