"""
FastAPI Server & Real-Time Event Bus for Agent Watchdog
Hosts WebSocket telemetry stream and REST APIs for Watchdog control & benchmark triggers.
"""

import os
import json
import asyncio
from typing import Dict, List, Any
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from real_watchdog import RealWatchdogEngine
from real_attacks import RealAttackSimulator
from real_orchestrator import RealMultiAgentPipeline
from real_benchmark import RealBenchmarkSuite
from dynamic_orchestrator import DynamicMultiAgentPipeline

app = FastAPI(
    title="Sunniva Safeguard API",
    description="Real-Time Security Watchdog & Live Dashboard Backend for Multi-Agent AI Teams",
    version="2.0.0"
)

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global State Singletons using Real LLM Engine & Dynamic Swarms
global_watchdog = RealWatchdogEngine(threshold=0.55, active=True)
global_attack_sim = RealAttackSimulator(attack_type="none")
global_pipeline = DynamicMultiAgentPipeline(global_watchdog, global_attack_sim)
global_benchmark = RealBenchmarkSuite()

class ConnectionManager:
    """Manages active WebSocket connections to frontend dashboard."""
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: Dict[str, Any]):
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except Exception:
                self.disconnect(connection)

manager = ConnectionManager()

class RunRequest(BaseModel):
    task_prompt: str = "Analyze system security & build multi-agent pipeline."
    attack_type: str = "none"
    watchdog_active: bool = True

class ToggleWatchdogRequest(BaseModel):
    active: bool

class SetAttackRequest(BaseModel):
    attack_type: str

@app.get("/api/status")
def get_status():
    """Returns current state of Watchdog, trust scores, and attack configuration."""
    return {
        "watchdog_active": global_watchdog.active,
        "attack_type": global_attack_sim.attack_type,
        "trust_scores": global_watchdog.agent_trust_scores,
        "quarantined_edges": global_watchdog.quarantined_edges,
        "threshold": global_watchdog.threshold
    }

@app.post("/api/toggle-watchdog")
async def toggle_watchdog(req: ToggleWatchdogRequest):
    """Enables or disables Watchdog active defense."""
    global_watchdog.set_active(req.active)
    event = {
        "type": "STATE_CHANGE",
        "watchdog_active": global_watchdog.active,
        "attack_type": global_attack_sim.attack_type,
        "trust_scores": global_watchdog.agent_trust_scores
    }
    await manager.broadcast(event)
    return {"status": "success", "watchdog_active": global_watchdog.active}

@app.post("/api/set-attack")
async def set_attack(req: SetAttackRequest):
    """Sets active attack scenario."""
    if req.attack_type not in RealAttackSimulator.ATTACK_TYPES:
        raise HTTPException(status_code=400, detail=f"Invalid attack type. Choose from {RealAttackSimulator.ATTACK_TYPES}")
    global_attack_sim.set_attack_type(req.attack_type)
    event = {
        "type": "STATE_CHANGE",
        "watchdog_active": global_watchdog.active,
        "attack_type": global_attack_sim.attack_type,
        "trust_scores": global_watchdog.agent_trust_scores
    }
    await manager.broadcast(event)
    return {"status": "success", "attack_type": global_attack_sim.attack_type}

@app.post("/api/run")
async def run_simulation(req: RunRequest):
    """Triggers a live multi-agent simulation run and broadcasts telemetry events."""
    global_watchdog.set_active(req.watchdog_active)
    global_attack_sim.set_attack_type(req.attack_type)

    async def broadcast_event(event: Dict[str, Any]):
        await manager.broadcast(event)

    # Broadcast START event
    start_event = {
        "type": "PIPELINE_START",
        "task_prompt": req.task_prompt,
        "attack_type": req.attack_type,
        "watchdog_active": req.watchdog_active
    }
    await manager.broadcast(start_event)

    result = await global_pipeline.run_prompt_driven_pipeline(req.task_prompt, event_callback=broadcast_event)
    return {
        "status": "completed",
        "events_count": len(result["events"]),
        "final_deliverable": result["final_deliverable"],
        "swarm_plan": result["swarm_plan"]
    }

@app.get("/api/benchmark")
async def run_benchmark(runs: int = 30):
    """Runs automated benchmark suite and returns metrics comparison."""
    results = await global_benchmark.run_benchmark(num_runs=runs)
    return results

@app.websocket("/ws/telemetry")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket telemetry endpoint for live React dashboard connection."""
    await manager.connect(websocket)
    try:
        # Send initial status snapshot upon connection
        init_event = {
            "type": "INIT_STATE",
            "watchdog_active": global_watchdog.active,
            "attack_type": global_attack_sim.attack_type,
            "trust_scores": global_watchdog.agent_trust_scores
        }
        await websocket.send_json(init_event)
        while True:
            data = await websocket.receive_text()
            # Can receive client ping/commands if needed
    except WebSocketDisconnect:
        manager.disconnect(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
