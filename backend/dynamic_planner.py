"""
Dynamic Meta-Planner Engine for Sunniva Safeguard
Runs FIRST before any agent pipeline execution.
Uses a real OpenRouter LLM call to analyze any raw user task prompt and dynamically generate:
1. Custom agent roles (3-5 specialized agents tailored for THIS specific task)
2. Role descriptions and specialized system prompts
3. Tool assignments
4. Communication sequence topology
"""

import os
import json
import re
from typing import Dict, List, Any
from openai import OpenAI

class DynamicMetaPlanner:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY", "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")
        self.base_url = os.getenv("BASE_URL", "https://openrouter.ai/api/v1")
        self.model_name = "openai/gpt-4o-mini"

    def plan_swarm(self, user_prompt: str) -> Dict[str, Any]:
        """
        Invokes real OpenRouter LLM to generate a dynamic multi-agent team for the user prompt.
        """
        client = OpenAI(api_key=self.api_key, base_url=self.base_url)

        meta_system_prompt = (
            "You are an expert AI Multi-Agent Architect. Your job is to analyze the user's task request "
            "and design a custom 3 to 5 agent team specialized for THIS specific task.\n\n"
            "Respond ONLY with a valid JSON object matching this schema:\n"
            "{\n"
            '  "task_summary": "Short summary of task goal",\n'
            '  "agents": [\n'
            '    {\n'
            '      "id": "ShortIdentifier",\n'
            '      "label": "Role Title",\n'
            '      "role_description": "Detailed explanation of responsibilities",\n'
            '      "system_prompt": "Specialized prompt instruction for this agent",\n'
            '      "primary_tool": "search_files_or_web" or "execute_python_code" or "shared_memory_store" or "verify_schema_audit"\n'
            '    }\n'
            '  ],\n'
            '  "sequence": [\n'
            '    {"sender": "Agent1_ID", "receiver": "Agent2_ID", "turn_goal": "What Sender passes to Receiver"}\n'
            '  ]\n'
            "}"
        )

        user_input = f"Design a custom AI agent team and task sequence for this request: '{user_prompt}'"

        try:
            res = client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": meta_system_prompt},
                    {"role": "user", "content": user_input}
                ],
                max_tokens=600,
                temperature=0.3
            )
            raw_text = res.choices[0].message.content.strip()

            # Clean JSON formatting code blocks if present
            json_str = raw_text
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0].strip()
            elif "```" in json_str:
                json_str = json_str.split("```")[1].split("```")[0].strip()

            parsed_plan = json.loads(json_str)
            return parsed_plan
        except Exception as e:
            print(f"[MetaPlanner Warning]: Failed to parse LLM JSON plan, using smart prompt-adaptive fallback: {e}")
            return self._fallback_plan_generator(user_prompt)

    def _fallback_plan_generator(self, prompt: str) -> Dict[str, Any]:
        """Smart fallback planner when JSON parsing requires fallback."""
        prompt_lower = prompt.lower()

        if "marketing" in prompt_lower or "campaign" in prompt_lower or "app" in prompt_lower:
            return {
                "task_summary": f"Digital Marketing Campaign: {prompt}",
                "agents": [
                    {
                        "id": "BrandStrategist",
                        "label": "Brand Strategist",
                        "role_description": "Analyzes target audience and brand positioning",
                        "system_prompt": "You are a Brand Strategist. Define target demographics, value proposition, and messaging hooks.",
                        "primary_tool": "search_files_or_web"
                    },
                    {
                        "id": "CampaignPlanner",
                        "label": "Campaign Planner",
                        "role_description": "Structures multi-channel campaign tactics and schedule",
                        "system_prompt": "You are a Campaign Planner. Create step-by-step channel distribution plans.",
                        "primary_tool": "shared_memory_store"
                    },
                    {
                        "id": "Copywriter",
                        "label": "Ad Copywriter",
                        "role_description": "Drafts compelling ad copy and creative slogans",
                        "system_prompt": "You are an Ad Copywriter. Write engaging headlines, social media copy, and call-to-actions.",
                        "primary_tool": "execute_python_code"
                    },
                    {
                        "id": "ComplianceAuditor",
                        "label": "Compliance Auditor",
                        "role_description": "Audits copy for brand guidelines and regulatory safety",
                        "system_prompt": "You are a Compliance Auditor. Review all marketing materials for accuracy and safety compliance.",
                        "primary_tool": "verify_schema_audit"
                    }
                ],
                "sequence": [
                    {"sender": "BrandStrategist", "receiver": "CampaignPlanner", "turn_goal": "Brand positioning strategy"},
                    {"sender": "CampaignPlanner", "receiver": "Copywriter", "turn_goal": "Channel schedule & copy briefs"},
                    {"sender": "Copywriter", "receiver": "ComplianceAuditor", "turn_goal": "Drafted ad copy & copy assets"},
                    {"sender": "ComplianceAuditor", "receiver": "CampaignPlanner", "turn_goal": "Audited campaign report"}
                ]
            }
        elif "debug" in prompt_lower or "code" in prompt_lower or "software" in prompt_lower:
            return {
                "task_summary": f"Codebase Inspection & Debugging: {prompt}",
                "agents": [
                    {
                        "id": "CodeInspector",
                        "label": "Code Inspector",
                        "role_description": "Scans codebase files and identifies error trace patterns",
                        "system_prompt": "You are a Code Inspector. Scan source files and identify bug symptoms.",
                        "primary_tool": "search_files_or_web"
                    },
                    {
                        "id": "BugDiagnostician",
                        "label": "Bug Diagnostician",
                        "role_description": "Diagnoses root causes and formulates patch strategies",
                        "system_prompt": "You are a Bug Diagnostician. Determine root causes of code defects.",
                        "primary_tool": "shared_memory_store"
                    },
                    {
                        "id": "PatchExecutor",
                        "label": "Patch Executor",
                        "role_description": "Writes refactored python code to fix defects",
                        "system_prompt": "You are a Patch Executor. Write clean Python code patches.",
                        "primary_tool": "execute_python_code"
                    },
                    {
                        "id": "CodeReviewer",
                        "label": "Code Reviewer",
                        "role_description": "Audits code patches for security and performance",
                        "system_prompt": "You are a Code Reviewer. Verify patch correctness and test output.",
                        "primary_tool": "verify_schema_audit"
                    }
                ],
                "sequence": [
                    {"sender": "CodeInspector", "receiver": "BugDiagnostician", "turn_goal": "Code inspection report"},
                    {"sender": "BugDiagnostician", "receiver": "PatchExecutor", "turn_goal": "Root cause diagnosis & patch brief"},
                    {"sender": "PatchExecutor", "receiver": "CodeReviewer", "turn_goal": "Refactored code patch"},
                    {"sender": "CodeReviewer", "receiver": "BugDiagnostician", "turn_goal": "Audit verification status"}
                ]
            }
        else:
            # General Research / Policy / Report Swarm
            return {
                "task_summary": f"Research & Policy Analysis: {prompt}",
                "agents": [
                    {
                        "id": "MarketAnalyst",
                        "label": "Market Analyst",
                        "role_description": "Gathers background facts, data citations, and market insights",
                        "system_prompt": "You are a Market Analyst. Conduct thorough research and data collection.",
                        "primary_tool": "search_files_or_web"
                    },
                    {
                        "id": "ReportPlanner",
                        "label": "Report Planner",
                        "role_description": "Structures comparative framework and outline",
                        "system_prompt": "You are a Report Planner. Structure clear outlines and evaluation matrices.",
                        "primary_tool": "shared_memory_store"
                    },
                    {
                        "id": "ContentWriter",
                        "label": "Content Writer",
                        "role_description": "Drafts comprehensive report and analytical deliverables",
                        "system_prompt": "You are a Content Writer. Draft thorough, polished reports based on research.",
                        "primary_tool": "execute_python_code"
                    },
                    {
                        "id": "AccuracyEditor",
                        "label": "Accuracy Editor",
                        "role_description": "Audits facts, formatting, and verifies report accuracy",
                        "system_prompt": "You are an Accuracy Editor. Review reports for factual precision and security compliance.",
                        "primary_tool": "verify_schema_audit"
                    }
                ],
                "sequence": [
                    {"sender": "MarketAnalyst", "receiver": "ReportPlanner", "turn_goal": "Research findings & citations"},
                    {"sender": "ReportPlanner", "receiver": "ContentWriter", "turn_goal": "Report structure & outline"},
                    {"sender": "ContentWriter", "receiver": "AccuracyEditor", "turn_goal": "Drafted report deliverable"},
                    {"sender": "AccuracyEditor", "receiver": "ReportPlanner", "turn_goal": "Final audited deliverable"}
                ]
            }

if __name__ == "__main__":
    planner = DynamicMetaPlanner()
    plan = planner.plan_swarm("Plan a digital marketing campaign for a new app")
    print(json.dumps(plan, indent=2))
