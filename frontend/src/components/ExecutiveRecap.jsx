import React, { useState, useEffect } from 'react'
import { FileText, Download, Check, Sparkles, RefreshCw, BarChart2 } from 'lucide-react'

export default function ExecutiveRecap({ lang }) {
  const [recap, setRecap] = useState(null)
  const [loading, setLoading] = useState(false)
  const [copied, setCopied] = useState(false)

  const fetchRecap = async () => {
    setLoading(true)
    try {
      const res = await fetch(`/api/recap?lang=${lang}`)
      const data = await res.json()
      setRecap(data)
    } catch (err) {
      console.error('Fetch recap error:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchRecap()
  }, [lang])

  const handleCopyMarkdown = () => {
    if (!recap) return
    const md = `# ${recap.headline}

## Tactical Summary
${recap.tactical_summary}

## Control vs. Chaos Dynamics
${recap.control_vs_chaos_analysis}

## Key Match Turning Points
${recap.key_milestones?.map(m => `- **${m.minute} - ${m.event}:** ${m.tactical_significance}`).join('\n')}

## Player Ratings
${recap.player_ratings?.map(p => `- **${p.player} (${p.rating}/10):** ${p.verdict}`).join('\n')}
`
    navigator.clipboard.writeText(md)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="flex flex-col gap-4 bg-slate-900/90 border border-slate-800 rounded-xl p-4 shadow-xl">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <FileText className="text-amber-400" size={18} />
          <h2 className="text-sm font-bold uppercase tracking-wider text-slate-100">
            Executive Post-Match Tactical Dossier
          </h2>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={fetchRecap}
            disabled={loading}
            className="flex items-center gap-1 text-xs text-slate-400 hover:text-white bg-slate-950 px-2.5 py-1 rounded-lg border border-slate-800 transition-colors"
          >
            <RefreshCw size={12} className={loading ? 'animate-spin' : ''} />
            <span>Generate Fresh</span>
          </button>

          <button
            onClick={handleCopyMarkdown}
            disabled={!recap}
            className="flex items-center gap-1.5 text-xs font-bold text-white bg-cyan-600 hover:bg-cyan-500 px-3 py-1 rounded-lg transition-colors"
          >
            {copied ? <Check size={12} /> : <Download size={12} />}
            <span>{copied ? 'Copied Markdown' : 'Export Dossier'}</span>
          </button>
        </div>
      </div>

      {loading && !recap ? (
        <div className="text-center py-12 text-xs font-mono text-cyan-400 animate-pulse">
          Generating a recap from the current match telemetry...
        </div>
      ) : !recap ? (
        <div className="text-center py-12 text-xs font-mono text-slate-500">
          No recap data available. Click Generate Fresh above.
        </div>
      ) : (
        <div className="flex flex-col gap-4 max-h-[520px] overflow-y-auto pr-1">
          {/* Headline Banner */}
          <div className="bg-gradient-to-r from-cyan-950/60 to-slate-900 p-3.5 rounded-xl border border-cyan-500/30">
            <span className="text-[10px] font-mono uppercase text-cyan-400 tracking-wider font-bold block mb-1">
              FULL-TIME EDITORIAL HEADLINE
            </span>
            <h3 className="text-base font-extrabold text-white leading-snug">
              {recap.headline}
            </h3>
          </div>

          {/* Tactical Summary */}
          <div className="bg-slate-950/80 p-3.5 rounded-xl border border-slate-800 flex flex-col gap-1.5">
            <span className="text-xs font-bold text-slate-200">TACTICAL NARRATIVE</span>
            <p className="text-xs text-slate-300 font-sans leading-relaxed">
              {recap.tactical_summary}
            </p>
          </div>

          {/* Control vs Chaos */}
          <div className="bg-slate-950/80 p-3.5 rounded-xl border border-slate-800 flex flex-col gap-1.5">
            <div className="flex items-center gap-1.5 text-xs font-bold text-amber-300">
              <BarChart2 size={14} />
              <span>CONTROL VS. CHAOS RHYTHM ANALYSIS</span>
            </div>
            <p className="text-xs text-slate-300 font-sans leading-relaxed">
              {recap.control_vs_chaos_analysis}
            </p>
          </div>

          {/* Key Milestones */}
          {recap.key_milestones && recap.key_milestones.length > 0 && (
            <div className="bg-slate-950/80 p-3.5 rounded-xl border border-slate-800 flex flex-col gap-2">
              <span className="text-xs font-bold text-slate-200">KEY MATCH TURNING POINTS</span>
              <div className="flex flex-col gap-2">
                {recap.key_milestones.map((m, idx) => (
                  <div key={idx} className="flex items-start gap-2 text-xs border-l-2 border-cyan-500 pl-2">
                    <span className="font-mono font-bold text-cyan-400 shrink-0">{m.minute}</span>
                    <div>
                      <div className="font-semibold text-slate-100">{m.event}</div>
                      <div className="text-[11px] text-slate-400 font-sans leading-tight mt-0.5">{m.tactical_significance}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Player Ratings */}
          {recap.player_ratings && recap.player_ratings.length > 0 && (
            <div className="bg-slate-950/80 p-3.5 rounded-xl border border-slate-800 flex flex-col gap-2">
              <span className="text-xs font-bold text-slate-200">ANALYTICAL PLAYER RATINGS</span>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {recap.player_ratings.map((p, idx) => (
                  <div key={idx} className="bg-slate-900/80 p-2.5 rounded-lg border border-slate-800 flex items-start justify-between gap-2">
                    <div>
                      <div className="text-xs font-bold text-slate-100">{p.player}</div>
                      <div className="text-[10px] text-slate-400 leading-tight mt-0.5">{p.verdict}</div>
                    </div>
                    <span className="text-xs font-mono font-bold text-emerald-400 bg-emerald-950/80 px-2 py-0.5 rounded border border-emerald-500/30">
                      {p.rating}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
