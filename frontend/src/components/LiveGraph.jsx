import React, { useEffect, useRef } from 'react';
import * as d3 from 'd3-force';
import { ShieldAlert, ShieldCheck, Zap } from 'lucide-react';

const DEFAULT_NODES = [
  { id: 'Researcher', label: 'Researcher', role: 'Data & Context Gathering' },
  { id: 'Planner', label: 'Planner', role: 'Task Allocation & Strategy' },
  { id: 'Executor', label: 'Executor', role: 'Code & Tool Execution' },
  { id: 'Reviewer', label: 'Reviewer', role: 'Quality Audit & Safety Check' },
];

const DEFAULT_LINKS = [
  { source: 'Researcher', target: 'Planner' },
  { source: 'Planner', target: 'Executor' },
  { source: 'Executor', target: 'Reviewer' },
  { source: 'Reviewer', target: 'Planner' },
];

export default function LiveGraph({
  trustScores = {},
  activeEvent = null,
  watchdogActive = true,
  attackType = 'none',
  dynamicPlan = null
}) {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');

    let animationFrameId;
    let particles = [];
    let poisonPulses = [];

    // Build node array dynamically
    let rawNodes = DEFAULT_NODES;
    let rawLinks = DEFAULT_LINKS;

    if (dynamicPlan && dynamicPlan.agents && dynamicPlan.agents.length > 0) {
      rawNodes = dynamicPlan.agents.map(a => ({
        id: a.id,
        label: a.label || a.id,
        role: a.role_description || a.label
      }));

      if (dynamicPlan.sequence && dynamicPlan.sequence.length > 0) {
        rawLinks = dynamicPlan.sequence.map(s => ({
          source: s.sender,
          target: s.receiver
        }));
      }
    }

    // Position nodes evenly in a layout ring
    const centerX = canvas.width / 2;
    const centerY = canvas.height / 2;
    const radius = Math.min(centerX, centerY) - 70;

    const nodes = rawNodes.map((d, idx) => {
      const angle = (idx / rawNodes.length) * 2 * Math.PI - Math.PI / 2;
      return {
        ...d,
        x: centerX + radius * Math.cos(angle),
        y: centerY + radius * Math.sin(angle)
      };
    });

    const links = rawLinks.map(l => ({
      source: nodes.find(n => n.id === l.source) || nodes[0],
      target: nodes.find(n => n.id === l.target) || nodes[1]
    })).filter(l => l.source && l.target);

    const simulation = d3.forceSimulation(nodes)
      .force('link', d3.forceLink(links).id(d => d.id).distance(170))
      .force('charge', d3.forceManyBody().strength(-250))
      .force('center', d3.forceCenter(centerX, centerY))
      .alphaTarget(0.05);

    // Particle / Poison animation on active event
    if (activeEvent && activeEvent.sender && activeEvent.receiver) {
      const srcNode = nodes.find(n => n.id === activeEvent.sender);
      const tgtNode = nodes.find(n => n.id === activeEvent.receiver);

      if (srcNode && tgtNode) {
        const isAttacked = activeEvent.evaluation?.attack_metadata?.attack_type &&
          activeEvent.evaluation?.attack_metadata?.attack_type !== 'none';
        const isBlocked = activeEvent.evaluation?.is_blocked;

        particles.push({
          x: srcNode.x,
          y: srcNode.y,
          targetX: tgtNode.x,
          targetY: tgtNode.y,
          progress: 0,
          speed: 0.02,
          isBlocked,
          isAttacked
        });

        if (isAttacked) {
          poisonPulses.push({
            x: srcNode.x,
            y: srcNode.y,
            targetX: tgtNode.x,
            targetY: tgtNode.y,
            radius: 10,
            maxRadius: 70,
            opacity: 0.9,
            isBlocked
          });
        }
      }
    }

    const render = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      // 1. Draw Links / Directed Edges
      links.forEach(link => {
        const isQuarantined = activeEvent?.evaluation?.is_quarantined &&
          ((link.source.id === activeEvent.sender && link.target.id === activeEvent.receiver) ||
           (link.source.id === activeEvent.receiver && link.target.id === activeEvent.sender));

        ctx.beginPath();
        ctx.moveTo(link.source.x, link.source.y);
        ctx.lineTo(link.target.x, link.target.y);

        if (isQuarantined && watchdogActive) {
          ctx.strokeStyle = '#ef4444';
          ctx.lineWidth = 3;
          ctx.setLineDash([8, 6]);
        } else {
          ctx.strokeStyle = '#1e293b';
          ctx.lineWidth = 2;
          ctx.setLineDash([]);
        }
        ctx.stroke();
        ctx.setLineDash([]);

        // Direction Arrow
        const dx = link.target.x - link.source.x;
        const dy = link.target.y - link.source.y;
        const angle = Math.atan2(dy, dx);
        const arrowDist = 42;
        const ax = link.target.x - arrowDist * Math.cos(angle);
        const ay = link.target.y - arrowDist * Math.sin(angle);

        ctx.beginPath();
        ctx.fillStyle = isQuarantined ? '#ef4444' : '#334155';
        ctx.arc(ax, ay, 4, 0, 2 * Math.PI);
        ctx.fill();
      });

      // 2. Render Poison Pulses
      for (let i = poisonPulses.length - 1; i >= 0; i--) {
        const p = poisonPulses[i];
        p.radius += 1.5;
        p.opacity -= 0.015;

        ctx.beginPath();
        ctx.arc(p.x, p.y, p.radius, 0, 2 * Math.PI);
        ctx.fillStyle = p.isBlocked
          ? `rgba(16, 185, 129, ${Math.max(0, p.opacity)})`
          : `rgba(239, 68, 68, ${Math.max(0, p.opacity)})`;
        ctx.fill();

        if (p.opacity <= 0 || p.radius >= p.maxRadius) {
          poisonPulses.splice(i, 1);
        }
      }

      // 3. Render Message Particles
      for (let i = particles.length - 1; i >= 0; i--) {
        const p = particles[i];
        p.progress += p.speed;
        const currX = p.x + (p.targetX - p.x) * p.progress;
        const currY = p.y + (p.targetY - p.y) * p.progress;

        ctx.beginPath();
        ctx.arc(currX, currY, p.isAttacked ? 8 : 6, 0, 2 * Math.PI);
        if (p.isBlocked) {
          ctx.fillStyle = '#f59e0b';
        } else if (p.isAttacked) {
          ctx.fillStyle = '#ef4444';
        } else {
          ctx.fillStyle = '#10b981';
        }
        ctx.fill();

        ctx.shadowColor = ctx.fillStyle;
        ctx.shadowBlur = 10;
        ctx.fill();
        ctx.shadowBlur = 0;

        if (p.progress >= 1.0) {
          particles.splice(i, 1);
        }
      }

      // 4. Render Nodes / Custom Dynamic Agents
      nodes.forEach(node => {
        const score = trustScores[node.id] !== undefined ? trustScores[node.id] : 1.0;

        let nodeColor = '#10b981';
        if (score < 0.4) nodeColor = '#ef4444';
        else if (score < 0.8) nodeColor = '#f59e0b';

        const isCompromised = score < 0.5;

        // Outer halo ring
        ctx.beginPath();
        ctx.arc(node.x, node.y, 34, 0, 2 * Math.PI);
        ctx.fillStyle = isCompromised ? 'rgba(239, 68, 68, 0.15)' : 'rgba(16, 185, 129, 0.10)';
        ctx.fill();

        // Node Circle Body
        ctx.beginPath();
        ctx.arc(node.x, node.y, 26, 0, 2 * Math.PI);
        ctx.fillStyle = '#111827';
        ctx.strokeStyle = nodeColor;
        ctx.lineWidth = 3;
        ctx.fill();
        ctx.stroke();

        // Trust score indicator dot
        ctx.beginPath();
        ctx.arc(node.x + 18, node.y - 18, 9, 0, 2 * Math.PI);
        ctx.fillStyle = nodeColor;
        ctx.fill();

        // Node Label
        ctx.font = 'bold 12px Inter, sans-serif';
        ctx.fillStyle = '#f8fafc';
        ctx.textAlign = 'center';
        ctx.fillText(node.label, node.x, node.y + 44);

        // Trust % Text
        ctx.font = '11px Fira Code, monospace';
        ctx.fillStyle = nodeColor;
        ctx.fillText(`Trust: ${Math.round(score * 100)}%`, node.x, node.y + 59);
      });

      animationFrameId = requestAnimationFrame(render);
    };

    render();

    return () => {
      cancelAnimationFrame(animationFrameId);
      simulation.stop();
    };
  }, [trustScores, activeEvent, watchdogActive, dynamicPlan]);

  return (
    <div className="relative w-full h-[420px] bg-cardbg/80 backdrop-blur border border-borderline rounded-2xl p-4 shadow-2xl flex flex-col justify-between overflow-hidden">
      {/* Top Header overlay */}
      <div className="flex items-center justify-between z-10">
        <div className="flex items-center gap-2">
          <div className="p-2 bg-emerald-500/10 border border-emerald-500/30 rounded-lg text-emerald-400">
            <Zap className="w-5 h-5 animate-pulse" />
          </div>
          <div>
            <h2 className="text-base font-bold text-white tracking-wide">
              {dynamicPlan ? `Dynamic Swarm: ${dynamicPlan.task_summary || 'Custom Pipeline'}` : 'Prompt-Driven Multi-Agent Swarm Graph'}
            </h2>
            <p className="text-xs text-slate-400 font-mono">
              {dynamicPlan ? `${dynamicPlan.agents?.length || 4} Dynamic Agents Generated by Meta-Planner` : 'Real-Time Dynamic Node Topology & Telemetry'}
            </p>
          </div>
        </div>

        {/* Status badges */}
        <div className="flex items-center gap-3">
          <div className={`px-3 py-1 rounded-full text-xs font-semibold flex items-center gap-1.5 border ${
            watchdogActive
              ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400'
              : 'bg-rose-500/10 border-rose-500/30 text-rose-400'
          }`}>
            {watchdogActive ? <ShieldCheck className="w-3.5 h-3.5" /> : <ShieldAlert className="w-3.5 h-3.5" />}
            {watchdogActive ? 'Watchdog Active' : 'Unprotected Mode'}
          </div>

          {attackType !== 'none' && (
            <div className="px-3 py-1 bg-rose-500/20 border border-rose-500/40 text-rose-300 rounded-full text-xs font-mono font-medium animate-pulse">
              ⚠️ Attack Active: {attackType.replace('_', ' ').toUpperCase()}
            </div>
          )}
        </div>
      </div>

      {/* HTML5 Canvas Graph */}
      <canvas
        ref={canvasRef}
        width={800}
        height={320}
        className="w-full h-full cursor-crosshair"
      />

      {/* Graph Legend Footer */}
      <div className="flex items-center justify-between text-xs text-slate-400 border-t border-borderline pt-2 z-10">
        <div className="flex items-center gap-4">
          <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-emerald-500"></span> High Trust (&gt;80%)</span>
          <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-amber-500"></span> Trust Warning (40-80%)</span>
          <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-rose-500"></span> Compromised (&lt;40%)</span>
        </div>
        <div className="font-mono text-[11px] text-slate-500">
          SentenceTransformers Vector Watchdog • &lt;20ms Scorer
        </div>
      </div>
    </div>
  );
}
