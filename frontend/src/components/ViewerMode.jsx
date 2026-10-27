import React, { useState } from 'react'
import { Sparkles, MessageSquare } from 'lucide-react'

export default function ViewerMode({ audience, onSelectAudience, lang, onSelectLang, onAskQuestion }) {
  const [query, setQuery] = useState('')
  const [qaHistory, setQaHistory] = useState([
    {
      q: 'What is current expected goals (xG)?',
      a: 'Verified xG: Saltmarsh Rovers 0.65 vs Brackfield Athletic 0.28. SAL creating higher quality penalty-box chances.',
      verified: true
    }
  ])
  const [asking, setAsking] = useState(false)

  const handleAsk = async (questionText) => {
    const q = questionText || query
    if (!q.trim()) return
    setAsking(true)
    try {
      const res = await onAskQuestion(q)
      setQaHistory(prev => [...prev.slice(-3), { q, a: res.answer, verified: true }])
      setQuery('')
    } finally {
      setAsking(false)
    }
  }

  const audienceOptions = [
    { id: 'casual', label: 'Casual Fan', desc: 'Punchy storytelling' },
    { id: 'analyst', label: 'Tactical Analyst', desc: 'xG & press models' },
    { id: 'player_focus', label: 'Player Focus', desc: 'Rosmere & Bram spotlight' },
    { id: 'club_focus', label: 'Club Bias', desc: 'Rovers fan lens' },
    { id: 'single_metric', label: 'Metric Card', desc: 'Single headline stat' }
  ]

  const suggestions = [
    'What is the expected goals xG?',
    'Who has momentum dominance?',
    'Show pass completion stats',      'What is the trajectory measurement agreement?'
  ]

  return (
    <div className="flex flex-col gap-4 bg-slate-900/90 border border-slate-800 rounded-xl p-4 shadow-xl">
      {/* Header & Controls */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <Sparkles className="text-amber-400" size={18} />
          <h2 className="text-sm font-bold uppercase tracking-wider text-slate-100">
            Personalization & Interactive Studio
          </h2>
        </div>

        {/* Language switch */}
        <div className="flex items-center gap-1 bg-slate-950 p-1 rounded-lg border border-slate-800">
          <button
            onClick={() => onSelectLang('en')}
            className={`px-2 py-0.5 text-xs font-mono font-bold rounded transition-colors ${
              lang === 'en' ? 'bg-cyan-600 text-white' : 'text-slate-400 hover:text-white'
            }`}
          >
            EN
          </button>
          <button
            onClick={() => onSelectLang('es')}
            className={`px-2 py-0.5 text-xs font-mono font-bold rounded transition-colors ${
              lang === 'es' ? 'bg-cyan-600 text-white' : 'text-slate-400 hover:text-white'
            }`}
          >
            ES
          </button>
        </div>
      </div>

      {/* Audience Mode Switcher */}
      <div className="flex flex-col gap-1.5">
        <span className="text-xs text-slate-400 font-semibold">VIEWER PERSONA LENS</span>
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
          {audienceOptions.map(opt => (
            <button
              key={opt.id}
              onClick={() => onSelectAudience(opt.id)}
              className={`flex flex-col items-start p-2 rounded-lg border text-left transition-all ${
                audience === opt.id
                  ? 'bg-cyan-950/60 border-cyan-500/80 text-white shadow-sm'
                  : 'bg-slate-950/60 border-slate-800 text-slate-300 hover:border-slate-700'
              }`}
            >
              <span className="text-xs font-bold">{opt.label}</span>
              <span className="text-[10px] text-slate-400 font-sans">{opt.desc}</span>
            </button>
          ))}
        </div>
      </div>

      {/* "Ask the Match" QA Console */}
      <div className="flex flex-col gap-2 bg-slate-950/70 p-3 rounded-lg border border-slate-800">
        <div className="flex items-center justify-between text-xs text-cyan-300 font-semibold">
          <div className="flex items-center gap-1.5">
            <MessageSquare size={13} />
            <span>ASK THE MATCH (LOCAL QUESTION ROUTING)</span>
          </div>
          <span className="text-[10px] text-emerald-400 font-mono">LOCAL SCOUT METRICS</span>
        </div>

        {/* Input & Send */}
        <form
          onSubmit={(e) => { e.preventDefault(); handleAsk(); }}
          className="flex items-center gap-2"
        >
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ask about xG, speed, momentum, passes..."
            className="flex-1 bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500"
          />
          <button
            type="submit"
            disabled={asking}
            className="bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 text-white text-xs font-bold px-3 py-1.5 rounded-lg transition-colors"
          >
            {asking ? 'Asking...' : 'Ask'}
          </button>
        </form>

        {/* Quick Suggestion Chips */}
        <div className="flex flex-wrap gap-1.5 pt-1">
          {suggestions.map((s, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => handleAsk(s)}
              className="text-[10px] bg-slate-900/90 hover:bg-slate-800 border border-slate-800 px-2 py-0.5 rounded text-slate-300 transition-colors"
            >
              {s}
            </button>
          ))}
        </div>

        {/* QA History Answers */}
        <div className="flex flex-col gap-1.5 pt-2 border-t border-slate-800/80">
          {qaHistory.map((item, idx) => (
            <div key={idx} className="bg-slate-900/60 p-2 rounded border border-slate-800/60 text-xs">
              <div className="text-[11px] font-semibold text-slate-300">Q: {item.q}</div>
              <div className="text-cyan-200 mt-0.5 leading-relaxed">{item.a}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Hero-Tech Badges */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-1 text-[10px] font-mono text-slate-400">
        <div className="bg-slate-950 p-1.5 rounded border border-slate-800 text-center">
          <span className="text-cyan-400 block font-bold">HOSTED MODEL</span>
          <span>Optional provider</span>
        </div>
        <div className="bg-slate-950 p-1.5 rounded border border-slate-800 text-center">
          <span className="text-cyan-400 block font-bold">AGENT WORKFLOW</span>
          <span>Project-local roles</span>
        </div>
        <div className="bg-slate-950 p-1.5 rounded border border-slate-800 text-center">
          <span className="text-cyan-400 block font-bold">SCOUT API</span>
          <span>4 Read-only tools</span>
        </div>
        <div className="bg-slate-950 p-1.5 rounded border border-slate-800 text-center">
          <span className="text-cyan-400 block font-bold">DISCOVERY CARD</span>
          <span>Project-specific JSON</span>
        </div>
      </div>
    </div>
  )
}
