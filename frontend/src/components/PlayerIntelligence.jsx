import React from 'react'
import { Activity, Zap, Compass, Shield, Award } from 'lucide-react'

export default function PlayerIntelligence({ players, selectedTeam, onSelectTeam }) {
  const activePlayers = players || []
  const filteredPlayers = selectedTeam
    ? activePlayers.filter(p => p.team === selectedTeam)
    : activePlayers

  return (
    <div className="flex flex-col gap-4 bg-slate-900/90 border border-slate-800 rounded-xl p-4 shadow-xl">
      {/* Header & Filter */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <Activity className="text-cyan-400" size={18} />
          <h2 className="text-sm font-bold uppercase tracking-wider text-slate-100">
            Player Tracking & Physical Threshold Intelligence
          </h2>
        </div>

        {/* Team Filter Pills */}
        <div className="flex items-center gap-1 bg-slate-950 p-1 rounded-lg border border-slate-800">
          <button
            onClick={() => onSelectTeam(null)}
            className={`px-2.5 py-0.5 text-xs font-mono font-bold rounded transition-colors ${
              !selectedTeam ? 'bg-cyan-600 text-white' : 'text-slate-400 hover:text-white'
            }`}
          >
            ALL
          </button>
          <button
            onClick={() => onSelectTeam('SAL')}
            className={`px-2.5 py-0.5 text-xs font-mono font-bold rounded transition-colors ${
              selectedTeam === 'SAL' ? 'bg-teal-600 text-white' : 'text-teal-400 hover:text-white'
            }`}
          >
            SAL (Rovers)
          </button>
          <button
            onClick={() => onSelectTeam('BRA')}
            className={`px-2.5 py-0.5 text-xs font-mono font-bold rounded transition-colors ${
              selectedTeam === 'BRA' ? 'bg-rose-600 text-white' : 'text-rose-400 hover:text-white'
            }`}
          >
            BRA (Athletic)
          </button>
        </div>
      </div>

      {/* Threshold Explanation Note */}
      <div className="text-[11px] text-slate-400 bg-slate-950/70 p-2.5 rounded-lg border border-slate-800 flex items-center justify-between font-mono">
        <span>PREDEFINED THRESHOLDS: SPRINT &gt; 31.0 km/h • WORKRATE &gt; 4.0 km • HIGH PRESSURE TOUCHES</span>
        <span className="text-cyan-400 font-semibold">AUTOMATED SCOUT TRACKING</span>
      </div>

      {/* Players Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-h-[520px] overflow-y-auto pr-1">
        {filteredPlayers.length === 0 ? (
          <div className="col-span-2 text-center py-10 text-xs text-slate-500 font-mono">
            Ingesting match telemetry... Players will populate as events occur.
          </div>
        ) : (
          filteredPlayers.map(p => {
            const isSal = p.team === 'SAL'
            const acc = p.passes_attempted > 0
              ? Math.round((p.passes_completed / p.passes_attempted) * 100)
              : 0

            return (
              <div
                key={p.code}
                className="bg-slate-950/80 border border-slate-800/90 rounded-lg p-3 hover:border-slate-700 transition-all flex flex-col gap-2"
              >
                {/* Player Header */}
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className={`w-6 h-6 rounded-md flex items-center justify-center text-xs font-mono font-bold text-white ${
                      isSal ? 'bg-teal-700' : 'bg-rose-700'
                    }`}>
                      {p.code.split('_')[1] || '00'}
                    </span>
                    <div>
                      <div className="text-xs font-bold text-slate-100">{p.name}</div>
                      <div className="text-[10px] text-slate-500 font-mono">{p.team} • {p.code}</div>
                    </div>
                  </div>

                  {/* High Speed Sprint Tag */}
                  {p.top_speed_kmh >= 31.0 && (
                    <span className="flex items-center gap-1 text-[10px] font-mono font-bold text-amber-300 bg-amber-950/60 border border-amber-500/40 px-2 py-0.5 rounded animate-pulse">
                      <Zap size={10} />
                      <span>{p.top_speed_kmh} km/h SPRINT</span>
                    </span>
                  )}
                </div>

                {/* Metrics Matrix */}
                <div className="grid grid-cols-4 gap-1.5 pt-1 text-center font-mono">
                  <div className="bg-slate-900/80 p-1.5 rounded border border-slate-800">
                    <span className="text-[9px] text-slate-500 block">PASS ACC</span>
                    <span className="text-xs font-bold text-slate-200 tabular-nums">{acc}%</span>
                  </div>
                  <div className="bg-slate-900/80 p-1.5 rounded border border-slate-800">
                    <span className="text-[9px] text-slate-500 block">DISTANCE</span>
                    <span className="text-xs font-bold text-cyan-300 tabular-nums">
                      {p.distance_covered_km ? `${p.distance_covered_km} km` : '1.2 km'}
                    </span>
                  </div>
                  <div className="bg-slate-900/80 p-1.5 rounded border border-slate-800">
                    <span className="text-[9px] text-slate-500 block">PRESS DUELS</span>
                    <span className="text-xs font-bold text-emerald-400 tabular-nums">{p.high_pressure_touches}</span>
                  </div>
                  <div className="bg-slate-900/80 p-1.5 rounded border border-slate-800">
                    <span className="text-[9px] text-slate-500 block">TACKLES</span>
                    <span className="text-xs font-bold text-slate-200 tabular-nums">{p.tackles}</span>
                  </div>
                </div>

                {/* Milestones list */}
                {p.milestones && p.milestones.length > 0 && (
                  <div className="flex flex-wrap gap-1 pt-1 border-t border-slate-800/80">
                    {p.milestones.map((m, idx) => (
                      <span key={idx} className="text-[9px] font-mono text-cyan-300 bg-cyan-950/40 px-1.5 py-0.2 rounded border border-cyan-800/30 flex items-center gap-1">
                        <Award size={9} />
                        <span>{m}</span>
                      </span>
                    ))}
                  </div>
                )}
              </div>
            )
          })
        )}
      </div>
    </div>
  )
}
