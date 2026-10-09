# Sunniva Safeguard (formerly Agent Watchdog)
> **Author & Lead Architect**: Harsheet Dwivedi (`dwivedi.harsheet1@gmail.com`)  
> **Repository**: [https://github.com/Harsh33t/Sunniva-Safeguard](https://github.com/Harsh33t/Sunniva-Safeguard)  
> **Version**: 2.0.0 (2026 Release)

**Sunniva Safeguard** is a real-time security monitoring, graph-based anomaly detection, and active intervention system for multi-agent AI teams. It watches messages passed between AI agents, models their communication topology as a dynamic force-directed graph, detects when agents are manipulated or propagating malicious instructions, dynamically maintains persistent trust scores per agent, and actively blocks/quarantines attack vectors in real-time (< 20ms).

---

##  Key Features

1. **Multi-Agent Orchestration Layer**:
   - 4-Agent Pipeline (`Researcher` → `Planner` → `Executor` → `Reviewer` + cross-talk feedback loop).
   - Real-time inter-agent event telemetry streamed via WebSockets.

2. **3 Attack Simulation Vectors**:
   - **Prompt Injection**: Malicious system instruction override & data exfiltration payloads.
   - **Agent-in-the-Middle (AiTM)**: Intercepts in-flight inter-agent messages and alters task parameters.
   - **Instruction Drift / DoS**: Recursive loop injection & refusal payloads forcing multi-agent denial of service.

3. **Real-Time Watchdog Engine**:
   - **<20ms Anomaly Scorer**: Cosine semantic vector drift (`SentenceTransformer`) + keyword pattern matching + graph fan-out anomaly detection.
   - **Dynamic Persistent Trust Modeling**: Maintains per-agent trust scores (0.0 to 1.0) with trust decay on anomaly and gradual recovery on clean turns.
   - **Active Edge Quarantine & Intervention**: Intercepts anomalous payloads and cuts communication links before attacks propagate downstream.

4. **Live Force-Directed Dashboard**:
   - Interactive HTML5 Canvas / D3 force-directed node graph.
   - **Poison Spread Animation**: Visual red wave radiating across graph edges when an attack triggers.
   - **Laser Edge Cut**: Animated glowing red laser shear and quarantine shield when Sunniva Safeguard intervenes.
   - **Timeline Scrubber**: Round-by-round event replay scrubber.
   - **Metrics Panel**: Live task success rate, average trust score, blocked attack counter, and latency widgets.

5. **Automated Benchmark & Credibility Suite**:
   - Automated 50-trial simulation harness comparing **Unprotected Swarm** vs **Sunniva Safeguard Active**.
   - Computes Attack Success Rate (ASR), Attacks Blocked Rate, False Positive Rate (FPR), and Detection Latency.

---

## 🛠️ Tech Stack

- **Backend**: Python 3.10+, FastAPI, WebSockets, SentenceTransformers (`all-MiniLM-L6-v2`), NetworkX, PyTorch.
- **Frontend**: React 18, Vite, Tailwind CSS, HTML5 Canvas / D3-Force, Recharts, Lucide React.
- **LLM API**: OpenRouter API / OpenAI API.

---

## 🚀 Quick Start

### 1. Install Backend Dependencies & Start Server
```powershell
cd backend
pip install -r requirements.txt

$env:OPENAI_API_KEY="your-openrouter-api-key"
$env:BASE_URL="https://openrouter.ai/api/v1"
python -m uvicorn server:app --host 0.0.0.0 --port 8000
```

### 2. Install Frontend Dependencies & Start Dashboard
```powershell
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000` in your browser.

---

## 📚 Citation & Author Information

```bibtex
@software{dwivedi2026sunnivasafeguard,
  author = {Dwivedi, Harsheet},
  title = {Sunniva Safeguard: Real-Time Security Watchdog and Live Observability for Multi-Agent AI Teams},
  year = {2026},
  publisher = {GitHub},
  journal = {GitHub repository},
  howpublished = {\url{https://github.com/harsheet-dwivedi/Sunniva-Safeguard}}
}
```
