import React from 'react'
import { Play, XCircle, CheckCircle2, ShieldAlert, Cpu, Eye, DollarSign } from 'lucide-react'

export default function ProducerDesk({ cues, onTakeCue, onKillCue, videoAccuracy, refusals }) {
  const activeReceipt = cues?.find(c => c.status === 'onair')?.receipt || cues?.[0]?.receipt || null

  return (
    <div className="flex flex-col gap-4 bg-slate-900/90 border border-slate-800 rounded-xl p-4 shadow-xl">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <Cpu className="text-cyan-400" size={18} />
          <h2 className="text-sm font-bold uppercase tracking-wider text-slate-100">
            Producer Control Room & Desk
          </h2>
        </div>
        <span className="text-[11px] font-mono text-cyan-400/90 bg-cyan-950/60 px-2 py-0.5 rounded border border-cyan-500/30">
          CUE ENGINE ACTIVE
        </span>
      </div>

      {/* Model Receipt Bar */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 bg-slate-950/70 p-2.5 rounded-lg border border-slate-800/80 text-xs font-mono">
        <div>
          <span className="text-[10px] text-slate-500 block">PROVIDER / MODEL</span>
          <span className="text-cyan-300 font-semibold truncate block">
            {activeReceipt ? `${activeReceipt.provider} • ${activeReceipt.model?.split('/')?.pop() || activeReceipt.model}` : 'Waiting for cue'}
          </span>
        </div>
        <div>
          <span className="text-[10px] text-slate-500 block">LATENCY / TOKENS</span>
          <span className="text-slate-200">
            {activeReceipt ? `${activeReceipt.latency_ms}ms • ${activeReceipt.in_tokens}+${activeReceipt.out_tokens}tok` : '—'}
          </span>
        </div>
        <div>
          <span className="text-[10px] text-slate-500 block">EST. COST / LINE</span>
          <span className="text-emerald-400 flex items-center gap-0.5">
            <DollarSign size={10} />
            {activeReceipt?.est_cost_usd != null ? activeReceipt.est_cost_usd.toFixed(5) : '—'}
          </span>
        </div>
        <div>
          <span className="text-[10px] text-slate-500 block">CRITIC GATEWAY</span>
          <span className="text-emerald-400 flex items-center gap-1 font-semibold">
            <CheckCircle2 size={12} />
            {activeReceipt ? (activeReceipt.validated ? 'GROUNDED' : 'UNVERIFIED') : '—'}
          </span>
        </div>
      </div>

      {/* Trajectory-to-ground-truth distance reconciliation */}
      <div className="bg-slate-950/60 border border-cyan-500/20 rounded-lg p-3">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-1.5 text-xs font-bold text-cyan-300">
            <Eye size={14} />
            <span>TRAJECTORY DISTANCE RECONCILIATION</span>
          </div>
          <span className="text-xs font-mono font-bold text-emerald-400 bg-emerald-950/80 px-2 py-0.5 rounded border border-emerald-500/40">
            {videoAccuracy?.total_detections > 0 ? `${videoAccuracy.agreement_percentage}% AGREEMENT (±${videoAccuracy.tolerance_meters}m)` : 'AWAITING MEASUREMENTS'}
          </span>
        </div>
        <div className="flex items-center justify-between text-[11px] text-slate-400 font-mono">
          <span>Measurements: {videoAccuracy?.total_detections ?? 0}</span>
          <span>Within Tolerance: {videoAccuracy?.agreed_detections ?? 0}</span>
          <span className="text-cyan-400">Trajectory-derived metrics</span>
        </div>
      </div>

      {/* Cue Inbox Queue */}
      <div className="flex flex-col gap-2">
        <div className="flex items-center justify-between text-xs text-slate-400 font-semibold px-1">
          <span>BROADCAST CUE INBOX ({cues?.length || 0})</span>
          <span>TAKE / KILL CONTROLS</span>
        </div>

        <div className="flex flex-col gap-2 max-h-56 overflow-y-auto pr-1">
          {(!cues || cues.length === 0) ? (
            <div className="text-center py-6 text-xs text-slate-500 font-mono">
              Waiting for match moments to trigger broadcast cues...
            </div>
          ) : (
            cues.slice().reverse().map(cue => (
              <div
                key={cue.cue_id}
                className={`flex items-center justify-between gap-3 p-2.5 rounded-lg border text-xs transition-all ${
                  cue.status === 'onair'
                    ? 'bg-cyan-950/50 border-cyan-500/70 shadow-md'
                    : cue.status === 'killed'
                    ? 'bg-rose-950/20 border-rose-900/40 opacity-60'
                    : 'bg-slate-950/80 border-slate-800'
                }`}
              >
                <div className="flex items-start gap-2 flex-1 min-w-0">
                  <span className={`px-1.5 py-0.5 text-[9px] font-mono font-bold rounded shrink-0 ${
                    cue.priority === 1 ? 'bg-amber-500 text-slate-950' :
                    cue.priority === 2 ? 'bg-cyan-500 text-slate-950' : 'bg-slate-700 text-slate-300'
                  }`}>
                    {cue.ann} P{cue.priority}
                  </span>
                  <div className="min-w-0">
                    <div className="font-semibold text-slate-200 truncate">
                      {cue.payload.headline}
                    </div>
                    <div className="text-[11px] text-slate-400 truncate">
                      {cue.payload.detail}
                    </div>
                  </div>
                </div>

                {/* Status & Take/Kill buttons */}
                <div className="flex items-center gap-1.5 shrink-0">
                  {cue.status === 'onair' ? (
                    <span className="text-[10px] font-bold text-cyan-400 bg-cyan-950 px-2 py-0.5 rounded border border-cyan-400/50 animate-pulse">
                      ON AIR
                    </span>
                  ) : cue.status === 'killed' ? (
                    <span className="text-[10px] font-bold text-rose-400 bg-rose-950 px-2 py-0.5 rounded border border-rose-400/50">
                      KILLED
                    </span>
                  ) : (
                    <>
                      <button
                        onClick={() => onTakeCue(cue.cue_id)}
                        className="flex items-center gap-1 bg-teal-600 hover:bg-teal-500 text-white font-bold text-[10px] px-2 py-1 rounded transition-colors"
                        title="Take to Air"
                      >
                        <Play size={10} />
                        <span>TAKE</span>
                      </button>
                      <button
                        onClick={() => onKillCue(cue.cue_id)}
                        className="flex items-center gap-1 bg-rose-900/60 hover:bg-rose-700 text-rose-200 font-bold text-[10px] px-2 py-1 rounded transition-colors"
                        title="Kill Cue"
                      >
                        <XCircle size={10} />
                        <span>KILL</span>
                      </button>
                    </>
                  )}
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Refusals Audit Counter */}
      {refusals && refusals.length > 0 && (
        <div className="flex items-center justify-between bg-amber-950/30 border border-amber-600/30 px-3 py-2 rounded-lg text-xs text-amber-300">
          <div className="flex items-center gap-1.5 font-semibold">
            <ShieldAlert size={14} />
            <span>Grounding Critic Blocked {refusals.length} Hallucinated Claim(s)</span>
          </div>
          <span className="text-[10px] font-mono text-amber-400/80">Audit Log Protected</span>
        </div>
      )}
    </div>
  )
}
