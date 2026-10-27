import React, { useState } from 'react'
import { Award, ShieldCheck, Terminal } from 'lucide-react'

export default function FoundryEvalsModal({ refusals }) {
  const [mcpResult, setMcpResult] = useState(null)
  const [testingTool, setTestingTool] = useState(false)

  const testMcpTool = async (toolName, args = {}) => {
    setTestingTool(true)
    try {
      const res = await fetch('/api/mcp', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tool: toolName, arguments: args })
      })
      const data = await res.json()
      setMcpResult({ tool: toolName, data })
    } catch (err) {
      setMcpResult({ tool: toolName, error: String(err) })
    } finally {
      setTestingTool(false)
    }
  }

  return (
    <div className="flex flex-col gap-4 bg-slate-900/90 border border-slate-800 rounded-xl p-4 shadow-xl">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <Award className="text-cyan-400" size={18} />
          <h2 className="text-sm font-bold uppercase tracking-wider text-slate-100">
            Grounding Checks & Scout Tools
          </h2>
        </div>
        <span className="text-[11px] font-mono text-emerald-400 bg-emerald-950/80 px-2 py-0.5 rounded border border-emerald-500/40">
          CODE-ENFORCED
        </span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-center font-mono">
        <div className="bg-slate-950/80 p-3 rounded-xl border border-slate-800">
          <span className="text-[10px] text-slate-400 block mb-1">NUMERICAL CLAIMS</span>
          <span className="text-sm font-extrabold text-emerald-400">Checked against match facts</span>
          <span className="text-[9px] text-slate-500 block mt-0.5">Unverified values are rejected</span>
        </div>
        <div className="bg-slate-950/80 p-3 rounded-xl border border-slate-800">
          <span className="text-[10px] text-slate-400 block mb-1">EVIDENCE CITATIONS</span>
          <span className="text-sm font-extrabold text-cyan-400">Fact IDs validated</span>
          <span className="text-[9px] text-slate-500 block mt-0.5">Cues require known evidence</span>
        </div>
      </div>

      {/* Interactive MCP Tools Inspector */}
      <div className="bg-slate-950/80 p-3 rounded-xl border border-slate-800 flex flex-col gap-2">
        <div className="flex items-center justify-between text-xs text-cyan-300 font-semibold">
          <div className="flex items-center gap-1.5">
            <Terminal size={14} />
            <span>INTERACTIVE SCOUT TOOL API</span>
          </div>
          <span className="text-[10px] text-slate-400 font-mono">POST /api/mcp</span>
        </div>

        <div className="flex flex-wrap gap-2 pt-1">
          <button
            onClick={() => testMcpTool('get_match_summary')}
            disabled={testingTool}
            className="text-xs bg-slate-900 hover:bg-slate-800 border border-slate-700 px-3 py-1.5 rounded-lg text-slate-200 transition-colors"
          >
            Run `get_match_summary`
          </button>
          <button
            onClick={() => testMcpTool('get_player_stats', { player_code: 'sal_08' })}
            disabled={testingTool}
            className="text-xs bg-slate-900 hover:bg-slate-800 border border-slate-700 px-3 py-1.5 rounded-lg text-slate-200 transition-colors"
          >
            Run `get_player_stats(sal_08)`
          </button>
          <button
            onClick={() => testMcpTool('get_auto_eventing_accuracy')}
            disabled={testingTool}
            className="text-xs bg-slate-900 hover:bg-slate-800 border border-slate-700 px-3 py-1.5 rounded-lg text-slate-200 transition-colors"
          >
            Run `get_auto_eventing_accuracy`
          </button>
        </div>

        {mcpResult && (
          <div className="mt-2 bg-slate-900 p-2.5 rounded-lg border border-slate-800 text-[11px] font-mono text-cyan-200 max-h-40 overflow-y-auto">
            <div className="text-[10px] text-slate-500 mb-1">OUTPUT FROM {mcpResult.tool}:</div>
            <pre className="whitespace-pre-wrap">{JSON.stringify(mcpResult.data || mcpResult.error, null, 2)}</pre>
          </div>
        )}
      </div>

      {/* Grounding Critic Refusal Log */}
      <div className="bg-slate-950/80 p-3 rounded-xl border border-slate-800 flex flex-col gap-2">
        <div className="flex items-center justify-between text-xs font-semibold">
          <div className="flex items-center gap-1.5 text-amber-300">
            <ShieldCheck size={14} />
            <span>GROUNDING CRITIC AUDIT LOG ({refusals?.length || 0} BLOCKED CLAIMS)</span>
          </div>
          <span className="text-[10px] font-mono text-emerald-400">Grounding checks run before cue acceptance</span>
        </div>

        <div className="flex flex-col gap-2 max-h-48 overflow-y-auto pr-1">
          {(!refusals || refusals.length === 0) ? (
            <div className="text-center py-6 text-xs text-slate-500 font-mono">
              No blocked claims have been recorded in this session.
            </div>
          ) : (
            refusals.map((ref, idx) => (
              <div key={idx} className="bg-slate-900/90 p-2.5 rounded-lg border border-amber-900/40 text-xs">
                <div className="flex items-center justify-between text-[10px] font-mono text-amber-400 mb-1">
                  <span>MOMENT {ref.moment_id}</span>
                  <span>{ref.t_code}</span>
                </div>
                <div className="text-slate-300 line-through text-[11px] mb-1">
                  "{ref.headline}"
                </div>
                <div className="text-[10px] text-rose-400/90 font-mono">
                  Reason: {ref.refusal_reason}
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  )
}
