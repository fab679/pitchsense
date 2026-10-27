import React from 'react'
import { ShieldCheck, Flame, Activity } from 'lucide-react'

export default function TVOverlay({ summary, activeCue, currentEvent, offlineMode }) {
  const score = summary?.score || { SAL: 0, BRA: 0 }
  const tCode = summary?.clock_t_code || "00:00.0"
  const momentum = summary?.momentum_diff || 0.0
  const control = summary?.control_index || { SAL: 0.5, BRA: 0.5 }

  // Momentum percentage: convert -1.0..+1.0 into 0..100%
  const homePct = Math.round(((momentum + 1.0) / 2.0) * 100)
  const awayPct = 100 - homePct

  return (
    <>
      {/* 1. Score Bug & Clock (Top-Left) */}
      <div className="absolute top-3 left-3 flex items-center gap-1.5 bg-slate-950/90 backdrop-blur-md px-3 py-1.5 rounded-lg border border-slate-700/60 shadow-lg text-xs">
        {/* Home Team */}
        <div className="flex items-center gap-1.5 font-bold text-teal-400">
          <span className="w-2.5 h-2.5 rounded-sm bg-teal-600 inline-block"></span>
          <span>SAL</span>
          <span className="text-sm font-mono text-white ml-0.5">{score.SAL}</span>
        </div>
        <span className="text-slate-500 font-mono">-</span>
        {/* Away Team */}
        <div className="flex items-center gap-1.5 font-bold text-rose-400">
          <span className="text-sm font-mono text-white mr-0.5">{score.BRA}</span>
          <span>BRA</span>
          <span className="w-2.5 h-2.5 rounded-sm bg-rose-600 inline-block"></span>
        </div>
        <div className="h-3 w-px bg-slate-700 mx-1"></div>
        {/* Clock */}
        <div className="font-mono text-amber-400 font-semibold tracking-wider">
          {tCode}
        </div>
        {offlineMode && (
          <span className="ml-1 px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-300 text-[10px] font-mono border border-amber-500/30">
            OFFLINE SEED
          </span>
        )}
      </div>

      {/* 2. Momentum & Control Strip (Top-Center) */}
      <div className="absolute top-3 left-1/2 -translate-x-1/2 hidden sm:flex flex-col items-center gap-1 bg-slate-950/80 backdrop-blur-md px-3 py-1.5 rounded-lg border border-slate-800 shadow-md">
        <div className="flex items-center justify-between w-48 text-[10px] text-slate-400 font-medium">
          <span className="text-teal-400">SAL {Math.round(control.SAL * 100)}%</span>
          <span className="text-slate-400 uppercase tracking-wider text-[9px]">Momentum</span>
          <span className="text-rose-400">{Math.round(control.BRA * 100)}% BRA</span>
        </div>
        <div className="w-48 h-1.5 bg-slate-800 rounded-full overflow-hidden flex">
          <div
            className="bg-teal-500 transition-all duration-300"
            style={{ width: `${homePct}%` }}
          ></div>
          <div
            className="bg-rose-500 transition-all duration-300"
            style={{ width: `${awayPct}%` }}
          ></div>
        </div>
      </div>

      {/* 3. Live Broadcast Lower-Third Banner (Bottom) */}
      {activeCue && (
        <div className="absolute bottom-4 left-4 right-4 bg-slate-950/95 backdrop-blur-xl border border-cyan-500/40 rounded-xl p-3 shadow-2xl transition-all duration-300 animate-in fade-in slide-in-from-bottom-2">
          <div className="flex items-start justify-between gap-3">
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-1">
                <span className={`px-2 py-0.5 text-[10px] font-bold uppercase rounded ${
                  activeCue.priority === 1 ? 'bg-amber-500 text-slate-950' :
                  activeCue.priority === 2 ? 'bg-cyan-500 text-slate-950' : 'bg-slate-700 text-slate-200'
                }`}>
                  {activeCue.ann} • {activeCue.kind.replace('_', ' ')}
                </span>
                <span className="text-xs font-bold text-white tracking-wide">
                  {activeCue.payload.headline}
                </span>
              </div>
              <p className="text-xs text-slate-300 font-sans leading-relaxed">
                {activeCue.payload.detail}
              </p>
              {activeCue.payload.why && (
                <p className="text-[11px] text-cyan-300/90 italic mt-1">
                  Tactical context: {activeCue.payload.why}
                </p>
              )}
            </div>

            {/* Evidence & Verification Badges */}
            <div className="hidden md:flex flex-col items-end gap-1 shrink-0">
              <div className="flex items-center gap-1 text-[10px] text-emerald-400 font-mono bg-emerald-950/60 border border-emerald-500/40 px-2 py-0.5 rounded">
                <ShieldCheck size={12} />
                <span>VERIFIED BY CRITIC</span>
              </div>
              <div className="flex items-center gap-1 text-[10px] text-slate-400 font-mono">
                <span>Cites:</span>
                {activeCue.payload.evidence?.slice(0, 3).map((ev, i) => (
                  <span key={i} className="bg-slate-800 px-1 py-0.2 rounded text-[9px] text-slate-300">
                    {ev}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  )
}
