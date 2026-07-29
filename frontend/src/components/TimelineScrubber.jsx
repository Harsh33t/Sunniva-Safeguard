import React from 'react';
import { History, ShieldAlert, ShieldCheck, Play, ChevronRight, AlertTriangle } from 'lucide-react';

export default function TimelineScrubber({
  events = [],
  selectedEventIndex = 0,
  onSelectEvent
}) {
  const messageEvents = events.filter(e => e.type === 'MESSAGE');

  return (
    <div className="w-full bg-cardbg/80 backdrop-blur border border-borderline rounded-2xl p-4 shadow-xl flex flex-col gap-3">
      {/* Panel Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <History className="w-4 h-4 text-emerald-400" />
          <h3 className="text-sm font-bold text-white tracking-wide">Round-by-Round Timeline & Event Scrubber</h3>
        </div>
        <span className="text-xs text-slate-400 font-mono">
          {messageEvents.length} Event Rounds Captured
        </span>
      </div>

      {/* Scrubber Timeline Bar */}
      {messageEvents.length === 0 ? (
        <div className="h-16 border border-dashed border-slate-700/60 rounded-xl flex items-center justify-center text-xs text-slate-500 font-mono">
          No simulation events yet. Click "Run Simulation" to execute multi-agent pipeline.
        </div>
      ) : (
        <div className="flex items-center gap-2 overflow-x-auto pb-2 pt-1">
          {messageEvents.map((evt, idx) => {
            const isSelected = selectedEventIndex === idx;
            const isBlocked = evt.evaluation?.is_blocked;
            const isAttacked = evt.evaluation?.attack_metadata?.attack_type &&
              evt.evaluation?.attack_metadata?.attack_type !== 'none';

            return (
              <button
                key={idx}
                onClick={() => onSelectEvent(idx)}
                className={`flex-1 min-w-[170px] p-3 rounded-xl border text-left transition-all relative ${
                  isSelected
                    ? 'border-emerald-500 bg-emerald-500/10 ring-2 ring-emerald-500/30'
                    : 'border-borderline bg-darkbg/60 hover:border-slate-600'
                }`}
              >
                <div className="flex items-center justify-between text-xs mb-1">
                  <span className="font-bold text-slate-200">Round {evt.round}</span>
                  {isBlocked ? (
                    <span className="px-1.5 py-0.5 bg-rose-500/20 text-rose-400 border border-rose-500/40 rounded text-[10px] font-mono font-bold flex items-center gap-1">
                      <ShieldAlert className="w-3 h-3" /> BLOCKED
                    </span>
                  ) : isAttacked ? (
                    <span className="px-1.5 py-0.5 bg-amber-500/20 text-amber-400 border border-amber-500/40 rounded text-[10px] font-mono font-bold flex items-center gap-1">
                      <AlertTriangle className="w-3 h-3" /> ATTACKED
                    </span>
                  ) : (
                    <span className="px-1.5 py-0.5 bg-emerald-500/20 text-emerald-400 border border-emerald-500/40 rounded text-[10px] font-mono font-bold flex items-center gap-1">
                      <ShieldCheck className="w-3 h-3" /> CLEAN
                    </span>
                  )}
                </div>

                <div className="text-xs text-slate-300 font-mono flex items-center gap-1 truncate">
                  <span className="text-slate-400 font-semibold">{evt.sender}</span>
                  <ChevronRight className="w-3 h-3 text-slate-500 shrink-0" />
                  <span className="text-slate-400 font-semibold">{evt.receiver}</span>
                </div>

                <div className="mt-1 text-[11px] text-slate-400 font-mono truncate">
                  Anomaly: <span className={evt.evaluation?.anomaly_score > 0.5 ? 'text-rose-400 font-bold' : 'text-emerald-400'}>
                    {evt.evaluation?.anomaly_score || 0}
                  </span>
                </div>
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
