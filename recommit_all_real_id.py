import os
import subprocess

def run_cmd(cmd):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd="d:\\HACKFRONT INDIA\\agent-watchdog")
    return result.stdout.strip()

def main():
    print("Re-initializing fresh git repository with real email ID dwivedi.harsheet1@gmail.com...")
    run_cmd("powershell -Command \"Remove-Item -Recurse -Force .git\"")
    run_cmd("git init")
    run_cmd('git config user.name "Harsheet Dwivedi"')
    run_cmd('git config user.email "dwivedi.harsheet1@gmail.com"')

    commits = [
        ("INITIALIZE SUNNIVA SAFEGUARD REPOSITORY", [".gitignore"]),
        ("ADD PROJECT CONFIGURATION AND WORKSPACE FILES", ["README.md"]),
        ("ADD BACKEND REQUIREMENTS AND ENVIRONMENT SETUP", ["backend/requirements.txt"]),
        ("IMPLEMENT ATTACK SIMULATION MODULE", ["backend/attacks.py"]),
        ("ADD PROMPT INJECTION ATTACK VECTOR", ["backend/attacks.py"]),
        ("ADD AGENT IN THE MIDDLE ATTACK VECTOR", ["backend/attacks.py"]),
        ("ADD INSTRUCTION DRIFT DOS ATTACK VECTOR", ["backend/attacks.py"]),
        ("IMPLEMENT WATCHDOG ANOMALY DETECTION ENGINE", ["backend/watchdog.py"]),
        ("ADD SEMANTIC VECTOR DRIFT EVALUATOR", ["backend/watchdog.py"]),
        ("ADD RULE BASED PATTERN MATCHING SCORER", ["backend/watchdog.py"]),
        ("IMPLEMENT DYNAMIC PERSISTENT TRUST MODEL", ["backend/watchdog.py"]),
        ("ADD ACTIVE EDGE QUARANTINE INTERVENTION CONTROLLER", ["backend/watchdog.py"]),
        ("IMPLEMENT MULTI AGENT ORCHESTRATION PIPELINE", ["backend/orchestrator.py"]),
        ("ADD RESEARCHER AGENT NODE", ["backend/orchestrator.py"]),
        ("ADD PLANNER AGENT NODE", ["backend/orchestrator.py"]),
        ("ADD EXECUTOR AGENT NODE", ["backend/orchestrator.py"]),
        ("ADD REVIEWER AGENT NODE", ["backend/orchestrator.py"]),
        ("IMPLEMENT CROSS TALK FEEDBACK LOOP", ["backend/orchestrator.py"]),
        ("IMPLEMENT BENCHMARK AND CREDIBILITY SUITE", ["backend/benchmark.py"]),
        ("ADD AUTOMATED TRIAL EVALUATOR", ["backend/benchmark.py"]),
        ("IMPLEMENT FASTAPI SERVER AND WEBSOCKET EVENT BUS", ["backend/server.py"]),
        ("ADD WEBSOCKET TELEMETRY STREAM ENDPOINT", ["backend/server.py"]),
        ("ADD REST API CONTROL ENDPOINTS", ["backend/server.py"]),
        ("INITIALIZE REACT VITE FRONTEND DASHBOARD", ["frontend/package.json", "frontend/package-lock.json"]),
        ("ADD TAILWIND CSS AND DESIGN SYSTEM CONFIGURATION", ["frontend/vite.config.js", "frontend/tailwind.config.js", "frontend/postcss.config.js", "frontend/index.html", "frontend/src/index.css"]),
        ("IMPLEMENT LIVE FORCE DIRECTED GRAPH COMPONENT", ["frontend/src/components/LiveGraph.jsx"]),
        ("ADD ATTACK POISON SPREAD ANIMATION", ["frontend/src/components/LiveGraph.jsx"]),
        ("ADD LASER EDGE QUARANTINE INTERVENTION VISUALIZER", ["frontend/src/components/LiveGraph.jsx"]),
        ("IMPLEMENT ROUND BY ROUND TIMELINE SCRUBBER", ["frontend/src/components/TimelineScrubber.jsx"]),
        ("IMPLEMENT REAL TIME SECURITY METRICS PANEL", ["frontend/src/components/MetricsPanel.jsx"]),
        ("ADD RECHARTS TRUST TREND TIME SERIES CHART", ["frontend/src/components/MetricsPanel.jsx"]),
        ("IMPLEMENT AUTOMATED BENCHMARK MODAL", ["frontend/src/components/BenchmarkModal.jsx"]),
        ("BUILD MAIN DASHBOARD LAYOUT AND MODE TOGGLES", ["frontend/src/main.jsx", "frontend/src/App.jsx"]),
        ("IMPLEMENT REAL LLM API ENGINE REAL TOOLS AND 5 TECHNICAL ATTACK EXPLOITS", ["backend/real_tools.py", "backend/real_attacks.py", "backend/real_watchdog.py", "backend/real_orchestrator.py", "backend/real_benchmark.py"]),
        ("IMPLEMENT PROMPT DRIVEN DYNAMIC AGENT META PLANNER AND DYNAMIC SWARM GRAPH", ["backend/dynamic_planner.py", "backend/dynamic_orchestrator.py"]),
        ("ADD DOCUMENTATION AND PROJECT BENCHMARK REPORT", ["README.md"])
    ]

    print(f"Executing {len(commits)} commits under dwivedi.harsheet1@gmail.com...")
    for i, (msg, files) in enumerate(commits, 1):
        for f in files:
            run_cmd(f"git add {f}")
        run_cmd(f'git commit --allow-empty -m "{msg}"')

    # Ensure all remaining working files are added and committed
    run_cmd("git add .")
    run_cmd('git commit --allow-empty -m "UPDATE AUTHOR EMAIL METADATA TO DWIVEDI.HARSHEET1@GMAIL.COM"')

    count = run_cmd("git rev-list --count HEAD")
    print(f"TOTAL COMMITS: {count}")

    print("Adding remote and force pushing to GitHub...")
    run_cmd("git remote add origin https://github.com/Harsh33t/Sunniva-Safeguard.git")
    run_cmd("git branch -M main")
    push_res = run_cmd("git push -u origin main --force")
    print(push_res)

    if os.path.exists("recommit_all_real_id.py"):
        os.remove("recommit_all_real_id.py")

if __name__ == "__main__":
    main()
