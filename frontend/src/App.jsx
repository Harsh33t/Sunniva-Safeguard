import React, { useState, useEffect, useRef } from 'react';
import {
  Shield, ShieldCheck, ShieldAlert, Zap, Play, Award,
  Bug, Terminal, AlertOctagon, CheckCircle2, ChevronRight, Activity, FileText, Sparkles
} from 'lucide-react';

import LiveGraph from './components/LiveGraph';
import TimelineScrubber from './components/TimelineScrubber';
import MetricsPanel from './components/MetricsPanel';
import BenchmarkModal from './components/BenchmarkModal';

const PRESET_PROMPTS = [
  "Research the top 3 CRM tools and draft a comprehensive comparison report.",
  "Plan a multi-channel digital marketing campaign for a new mobile fitness app.",
  "Debug and summarize error stack traces in a Python web backend codebase.",
  "Research and write a concise policy brief on renewable energy regulations."
];

export default function App() {
  const [watchdogActive, setWatchdogActive] = useState(true);
  const [attackType, setAttackType] = useState('none');
  const [taskPrompt, setTaskPrompt] = useState(PRESET_PROMPTS[0]);
  const [isRunning, setIsRunning] = useState(false);
  const [events, setEvents] = useState([]);
  const [selectedEventIndex, setSelectedEventIndex] = useState(0);
  const [dynamicPlan, setDynamicPlan] = useState(null);
  const [finalDeliverable, setFinalDeliverable] = useState(null);
  const [trustScores, setTrustScores] = useState({});
  const [showBenchmarkModal, setShowBenchmarkModal] = useState(false);
  const socketRef = useRef(null);

  // Connect WebSocket to FastAPI backend
  useEffect(() => {
    const connectWS = () => {
      const ws = new WebSocket('ws://localhost:8000/ws/telemetry');
      socketRef.current = ws;

      ws.onmessage = (evt) => {
        const msg = JSON.parse(evt.data);
        if (msg.type === 'DYNAMIC_PLAN_CREATED') {
          setDynamicPlan({
            task_summary: msg.task_summary,
            agents: msg.agents,
            sequence: msg.sequence
          });
          if (msg.trust_scores) setTrustScores(msg.trust_scores);
        } else if (msg.type === 'MESSAGE') {
          setEvents(prev => [...prev, msg]);
          if (msg.evaluation?.all_trust_scores) {
            setTrustScores(msg.evaluation.all_trust_scores);
          }
        } else if (msg.type === 'STATE_CHANGE') {
          setWatchdogActive(msg.watchdog_active);
          setAttackType(msg.attack_type);
          if (msg.trust_scores) setTrustScores(msg.trust_scores);
        } else if (msg.type === 'PIPELINE_START') {
          setEvents([]);
          setSelectedEventIndex(0);
          setFinalDeliverable(null);
          setIsRunning(true);
        } else if (msg.type === 'PIPELINE_COMPLETE') {
          setEvents(prev => [...prev, msg]);
          if (msg.final_deliverable) {
            setFinalDeliverable(msg.final_deliverable);
          }
          setIsRunning(false);
        }
      };

      ws.onclose = () => {
        setTimeout(connectWS, 3000);
      };
    };

    connectWS();

    return () => {
      if (socketRef.current) socketRef.current.close();
    };
  }, []);

  const handleToggleWatchdog = async () => {
    const nextState = !watchdogActive;
    setWatchdogActive(nextState);
    try {
      await fetch('http://localhost:8000/api/toggle-watchdog', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ active: nextState })
      });
    } catch (e) {
      console.warn('API sync warning:', e);
    }
  };

  const handleSelectAttack = async (type) => {
    setAttackType(type);
    try {
      await fetch('http://localhost:8000/api/set-attack', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ attack_type: type })
      });
    } catch (e) {
      console.warn('API sync warning:', e);
    }
  };

  const handleRunSimulation = async () => {
    if (!taskPrompt || !taskPrompt.trim()) return;
    setIsRunning(true);
    setEvents([]);
    setFinalDeliverable(null);
    setSelectedEventIndex(0);

    try {
      const res = await fetch('http://localhost:8000/api/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          task_prompt: taskPrompt,
          attack_type: attackType,
          watchdog_active: watchdogActive
        })
      });
      const data = await res.json();
      if (data.final_deliverable) {
        setFinalDeliverable(data.final_deliverable);
      }
      if (data.swarm_plan) {
        setDynamicPlan(data.swarm_plan);
      }
    } catch (e) {
      console.error('Run execution error:', e);
    } finally {
      setIsRunning(false);
    }
  };

  const messageEvents = events.filter(e => e.type === 'MESSAGE');
  const activeEvent = messageEvents[selectedEventIndex] || messageEvents[messageEvents.length - 1] || null;

  return (
    <div className="min-h-screen bg-darkbg text-slate-100 flex flex-col font-sans selection:bg-emerald-500 selection:text-white">
      {/* 1. Header Navbar */}
      <header className="border-b border-borderline bg-cardbg/90 backdrop-blur sticky top-0 z-40 px-6 py-3.5 flex items-center justify-between shadow-xl">
        <div className="flex items-center gap-3">
          <div className="p-2.5 bg-gradient-to-tr from-emerald-600 to-teal-500 rounded-xl text-white shadow-lg shadow-emerald-500/20">
            <Shield className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-black tracking-tight text-white">SUNNIVA SAFEGUARD</h1>
              <span className="px-2 py-0.5 bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 rounded text-[10px] font-mono font-bold">
                PROMPT-DRIVEN ENGINE
              </span>
            </div>
            <p className="text-xs text-slate-400 font-mono">Real-Time Security Watchdog & Observability Engine by Harsheet Dwivedi</p>
          </div>
        </div>

        {/* Header Controls */}
        <div className="flex items-center gap-4">
          <button
            onClick={handleToggleWatchdog}
            className={`px-4 py-2 rounded-xl border text-xs font-bold transition flex items-center gap-2 shadow-lg ${
              watchdogActive
                ? 'bg-emerald-500/10 border-emerald-500/40 text-emerald-400 hover:bg-emerald-500/20'
                : 'bg-rose-500/10 border-rose-500/40 text-rose-400 hover:bg-rose-500/20'
            }`}
          >
            {watchdogActive ? <ShieldCheck className="w-4 h-4" /> : <ShieldAlert className="w-4 h-4" />}
            MODE: {watchdogActive ? 'WATCHDOG ACTIVE (ON)' : 'UNPROTECTED (OFF)'}
          </button>

          <button
            onClick={() => setShowBenchmarkModal(true)}
            className="px-4 py-2 bg-indigo-600/20 border border-indigo-500/40 hover:bg-indigo-600/30 text-indigo-300 text-xs font-bold rounded-xl transition flex items-center gap-2"
          >
            <Award className="w-4 h-4" />
            Benchmark Suite
          </button>
        </div>
      </header>

      {/* 2. Main Dashboard Layout */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-6 flex flex-col gap-6">
        {/* Prominent Task Prompt Entry Bar */}
        <div className="bg-cardbg/90 backdrop-blur border border-borderline rounded-2xl p-5 shadow-2xl flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-emerald-400 animate-pulse" />
              <h2 className="text-base font-bold text-white tracking-wide">Enter Custom Multi-Agent Task Prompt</h2>
            </div>
            <span className="text-xs text-slate-400 font-mono">Meta-Planner LLM will dynamically generate agents & task topology</span>
          </div>

          <div className="flex flex-col md:flex-row gap-3">
            <textarea
              rows={2}
              value={taskPrompt}
              onChange={(e) => setTaskPrompt(e.target.value)}
              placeholder="e.g. Research top 3 CRM tools and draft a comparison report..."
              className="flex-1 bg-darkbg border border-borderline focus:border-emerald-500 rounded-xl p-3 text-xs text-slate-100 placeholder:text-slate-500 focus:outline-none font-sans leading-relaxed resize-none"
            />
            <button
              onClick={handleRunSimulation}
              disabled={isRunning || !taskPrompt.trim()}
              className="px-6 py-3 bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-400 hover:to-teal-500 text-white font-bold text-xs rounded-xl shadow-lg shadow-emerald-500/20 flex items-center justify-center gap-2 transition disabled:opacity-50 shrink-0"
            >
              {isRunning ? <Zap className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4 fill-white" />}
              {isRunning ? 'Meta-Planner Executing...' : 'Run Custom Task'}
            </button>
          </div>

          {/* Quick Preset Prompts */}
          <div className="flex flex-wrap items-center gap-2 pt-1 border-t border-borderline/60">
            <span className="text-[11px] text-slate-400 font-mono">Preset Prompts:</span>
            {PRESET_PROMPTS.map((preset, idx) => (
              <button
                key={idx}
                onClick={() => setTaskPrompt(preset)}
                className="px-2.5 py-1 bg-darkbg/60 border border-borderline hover:border-slate-500 text-[11px] font-mono text-slate-300 rounded-lg truncate max-w-[260px] transition"
              >
                {preset}
              </button>
            ))}
          </div>
        </div>

        {/* Technical Attack Scenario Selector */}
        <div className="bg-cardbg/80 backdrop-blur border border-borderline rounded-2xl p-4 shadow-xl flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <span className="text-xs font-bold text-slate-300 uppercase tracking-wider font-mono">Select Technical Exploit:</span>
            <div className="flex flex-wrap items-center gap-2">
              {[
                { id: 'none', label: 'Clean Run (Normal)', icon: CheckCircle2 },
                { id: 'prompt_injection_tool_output', label: 'Tool Output Injection', icon: Bug },
                { id: 'man_in_the_middle_tamper', label: 'AiTM Message Tamper', icon: AlertOctagon },
                { id: 'malicious_tool_api_response', label: 'Malicious Tool JSON', icon: Zap },
                { id: 'memory_context_poisoning', label: 'Memory Store Poison', icon: Terminal },
                { id: 'instruction_conflict_goal_hijack', label: 'Goal Conflict Hijack', icon: AlertOctagon },
              ].map(item => {
                const isSelected = attackType === item.id;
                const Icon = item.icon;
                return (
                  <button
                    key={item.id}
                    onClick={() => handleSelectAttack(item.id)}
                    className={`px-2.5 py-1.5 rounded-xl border text-[11px] font-semibold flex items-center gap-1.5 transition ${
                      isSelected
                        ? 'bg-slate-800 border-emerald-500 text-white shadow-md ring-1 ring-emerald-500/30'
                        : 'bg-darkbg/40 border-borderline text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    <Icon className={`w-3.5 h-3.5 ${isSelected ? 'text-emerald-400' : 'text-slate-500'}`} />
                    {item.label}
                  </button>
                );
              })}
            </div>
          </div>
        </div>

        {/* Dynamic Meta-Planner Swarm Breakdown Card (If Generated) */}
        {dynamicPlan && (
          <div className="bg-cardbg/80 backdrop-blur border border-borderline rounded-2xl p-4 shadow-xl flex flex-col gap-3 font-mono text-xs">
            <div className="flex items-center justify-between border-b border-borderline pb-2">
              <span className="font-bold text-emerald-400 uppercase tracking-wider flex items-center gap-1.5">
                <Sparkles className="w-4 h-4" /> Meta-Planner Generated Swarm Topology: {dynamicPlan.task_summary}
              </span>
              <span className="text-slate-400">{dynamicPlan.agents?.length || 0} Dynamic Agents Generated</span>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
              {dynamicPlan.agents?.map((agent, idx) => (
                <div key={idx} className="p-3 bg-darkbg/70 border border-borderline rounded-xl flex flex-col gap-1">
                  <span className="font-bold text-white">{agent.label} ({agent.id})</span>
                  <p className="text-[11px] text-slate-400 line-clamp-2">{agent.role_description}</p>
                  <span className="text-[10px] text-emerald-400/80 mt-1">Tool: {agent.primary_tool}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Middle Grid: Dynamic Force Graph & Real-Time Metrics */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <LiveGraph
              trustScores={trustScores}
              activeEvent={activeEvent}
              watchdogActive={watchdogActive}
              attackType={attackType}
              dynamicPlan={dynamicPlan}
            />
          </div>
          <div>
            <MetricsPanel
              trustScores={trustScores}
              events={events}
              watchdogActive={watchdogActive}
              attackType={attackType}
            />
          </div>
        </div>

        {/* Timeline & Scrubber Panel */}
        <TimelineScrubber
          events={events}
          selectedEventIndex={selectedEventIndex}
          onSelectEvent={setSelectedEventIndex}
        />

        {/* Deliverable Results Panel */}
        {finalDeliverable && (
          <div className="bg-cardbg/90 backdrop-blur border border-emerald-500/40 rounded-2xl p-6 shadow-2xl flex flex-col gap-3 font-sans">
            <div className="flex items-center justify-between border-b border-borderline pb-3">
              <div className="flex items-center gap-2">
                <FileText className="w-5 h-5 text-emerald-400" />
                <h3 className="text-base font-bold text-white tracking-wide">Final Deliverable Output Panel</h3>
              </div>
              <span className="px-2.5 py-1 bg-emerald-500/20 text-emerald-400 border border-emerald-500/40 rounded-full text-xs font-mono font-bold">
                Task Completed
              </span>
            </div>
            <div className="bg-darkbg/90 border border-borderline rounded-xl p-4 text-xs text-slate-200 font-mono whitespace-pre-wrap leading-relaxed max-h-96 overflow-y-auto">
              {finalDeliverable}
            </div>
          </div>
        )}

        {/* Selected Event Payload Terminal Inspector */}
        {activeEvent && (
          <div className="bg-cardbg/80 backdrop-blur border border-borderline rounded-2xl p-5 shadow-xl flex flex-col gap-3 font-mono">
            <div className="flex items-center justify-between border-b border-borderline pb-2">
              <div className="flex items-center gap-2">
                <Terminal className="w-4 h-4 text-emerald-400" />
                <h4 className="text-xs font-bold text-white uppercase tracking-wider">
                  Turn Payload Inspector — Round {activeEvent.round} ({activeEvent.sender} → {activeEvent.receiver})
                </h4>
              </div>
              <span className={`text-[11px] font-bold px-2 py-0.5 rounded border ${
                activeEvent.evaluation?.is_blocked
                  ? 'bg-rose-500/20 border-rose-500/40 text-rose-400'
                  : 'bg-emerald-500/20 border-emerald-500/40 text-emerald-400'
              }`}>
                {activeEvent.evaluation?.is_blocked ? 'BLOCKED & QUARANTINED' : 'CLEAN PASSTHROUGH'}
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
              <div className="p-3 bg-darkbg/80 border border-borderline rounded-xl flex flex-col gap-1.5">
                <span className="text-[11px] text-slate-400 font-semibold uppercase">Raw Inter-Agent Message Payload</span>
                <p className="text-slate-300 whitespace-pre-wrap leading-relaxed">
                  {activeEvent.raw_payload}
                </p>
              </div>

              <div className="p-3 bg-darkbg/80 border border-borderline rounded-xl flex flex-col gap-2">
                <span className="text-[11px] text-slate-400 font-semibold uppercase">Watchdog Intercepted & Sanitized Payload</span>
                <p className={`whitespace-pre-wrap leading-relaxed ${
                  activeEvent.evaluation?.is_blocked ? 'text-amber-400 font-bold' : 'text-slate-300'
                }`}>
                  {activeEvent.payload}
                </p>
                <div className="mt-2 pt-2 border-t border-borderline/60 flex items-center justify-between text-[11px] text-slate-400">
                  <span>Anomaly Score: <strong className="text-rose-400">{activeEvent.evaluation?.anomaly_score}</strong></span>
                  <span>Sender Trust: <strong className="text-emerald-400">{Math.round((activeEvent.evaluation?.sender_trust_score || 1.0) * 100)}%</strong></span>
                  <span>Latency: <strong className="text-indigo-400">{activeEvent.evaluation?.eval_latency_ms} ms</strong></span>
                </div>
              </div>
            </div>
          </div>
        )}
      </main>

      <BenchmarkModal
        isOpen={showBenchmarkModal}
        onClose={() => setShowBenchmarkModal(false)}
      />
    </div>
  );
}
