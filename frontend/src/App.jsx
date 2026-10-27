import React, { useState, useEffect, useRef } from 'react'
import PitchCanvas from './components/PitchCanvas'
import TVOverlay from './components/TVOverlay'
import ProducerDesk from './components/ProducerDesk'
import ViewerMode from './components/ViewerMode'
import PlayerIntelligence from './components/PlayerIntelligence'
import ExecutiveRecap from './components/ExecutiveRecap'
import FoundryEvalsModal from './components/FoundryEvalsModal'
import { Play, Pause, RotateCcw, Activity, FileText, Award, Tv } from 'lucide-react'

export default function App() {
  const [summary, setSummary] = useState(null)
  const [currentEvent, setCurrentEvent] = useState(null)
  const [activeCue, setActiveCue] = useState(null)
  const [cues, setCues] = useState([])
  const [refusals, setRefusals] = useState([])
  const [videoAccuracy, setVideoAccuracy] = useState({ agreement_percentage: 0, total_detections: 0, agreed_detections: 0, tolerance_meters: 2.0 })
  const [videoDetection, setVideoDetection] = useState(null)
  
  const [isRunning, setIsRunning] = useState(false)
  const [speed, setSpeed] = useState(4.0)
  const [offlineMode, setOfflineMode] = useState(false)
  
  const [audience, setAudience] = useState('casual')
  const [lang, setLang] = useState('en')
  const [activeTab, setActiveTab] = useState('studio') // studio | players | recap | evals
  const [selectedTeam, setSelectedTeam] = useState(null)
  
  const wsRef = useRef(null)

  // WebSocket Connection
  useEffect(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = window.location.host
    const wsUrl = `${protocol}//${host}/ws/match`

    const ws = new WebSocket(wsUrl)
    wsRef.current = ws

    ws.onopen = () => {
      console.log('PitchSense WebSocket Connected')
    }

    ws.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data)
        if (data.type === 'init') {
          setSummary(data.summary)
          setCues(data.cues || [])
          setRefusals(data.refusals || [])
          setVideoAccuracy(data.video_accuracy || { agreement_percentage: 0, total_detections: 0, agreed_detections: 0, tolerance_meters: 2.0 })
          setIsRunning(data.is_running)
          setSpeed(data.speed || 4.0)
          setOfflineMode(data.offline_mode)
        } else if (data.type === 'tick') {
          setCurrentEvent(data.event)
          setSummary(data.summary)
          if (data.trajectory_estimate) {
            setVideoDetection(data.trajectory_estimate)
          }
          if (data.video_accuracy !== undefined) {
            setVideoAccuracy(data.video_accuracy)
          }
          if (data.cue) {
            setCues(prev => [...prev, data.cue])
            setActiveCue(data.cue)
          }
        } else if (data.type === 'cue_update') {
          setCues(prev => prev.map(c => c.cue_id === data.cue.cue_id ? data.cue : c))
          if (data.cue.status === 'onair') {
            setActiveCue(data.cue)
          } else if (activeCue?.cue_id === data.cue.cue_id && data.cue.status === 'killed') {
            setActiveCue(null)
          }
        }
      } catch (err) {
        console.error('WS Message parsing error:', err)
      }
    }

    ws.onclose = () => {
      console.log('PitchSense WebSocket closed')
    }

    return () => {
      ws.close()
    }
  }, [])

  // Auto-dismiss cues when ttl_ms expires
  useEffect(() => {
    if (activeCue && activeCue.ttl_ms) {
      const timer = setTimeout(() => {
        setActiveCue(null)
      }, activeCue.ttl_ms)
      return () => clearTimeout(timer)
    }
  }, [activeCue])

  // Playback controls
  const handlePlayPause = () => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return
    const nextRunning = !isRunning
    setIsRunning(nextRunning)
    wsRef.current.send(JSON.stringify({ action: nextRunning ? 'play' : 'pause' }))
  }

  const handleSpeedChange = (newSpeed) => {
    setSpeed(newSpeed)
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ action: 'set_speed', speed: newSpeed }))
    }
  }

  const handleRestart = () => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return
    setCues([])
    setActiveCue(null)
    setIsRunning(true)
    wsRef.current.send(JSON.stringify({ action: 'restart', seed: 21, speed }))
  }

  // Producer actions
  const handleTakeCue = async (cueId) => {
    try {
      const res = await fetch(`/api/cues/${cueId}/take`, { method: 'POST' })
      const updated = await res.json()
      setActiveCue(updated)
    } catch (err) {
      console.error('Take cue error:', err)
    }
  }

  const handleKillCue = async (cueId) => {
    try {
      await fetch(`/api/cues/${cueId}/kill`, { method: 'POST' })
      if (activeCue?.cue_id === cueId) {
        setActiveCue(null)
      }
    } catch (err) {
      console.error('Kill cue error:', err)
    }
  }

  // Ask question
  const handleAskQuestion = async (q) => {
    const res = await fetch('/api/ask', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question: q })
    })
    return await res.json()
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      {/* 1. Master Navigation Header */}
      <header className="bg-slate-900/95 border-b border-slate-800 px-4 py-2.5 flex items-center justify-between sticky top-0 z-50 backdrop-blur-md">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-cyan-400 animate-pulse"></span>
            <h1 className="text-base font-extrabold tracking-wider bg-gradient-to-r from-cyan-400 via-teal-300 to-emerald-400 bg-clip-text text-transparent">
              PITCHSENSE
            </h1>
          </div>

          {/* Navigation View Switcher */}
          <nav className="hidden md:flex items-center gap-1 bg-slate-950 p-1 rounded-lg border border-slate-800 text-xs font-semibold">
            <button
              onClick={() => setActiveTab('studio')}
              className={`flex items-center gap-1.5 px-3 py-1 rounded-md transition-colors ${
                activeTab === 'studio' ? 'bg-cyan-600 text-white' : 'text-slate-400 hover:text-white'
              }`}
            >
              <Tv size={13} />
              <span>Broadcast Studio</span>
            </button>
            <button
              onClick={() => setActiveTab('players')}
              className={`flex items-center gap-1.5 px-3 py-1 rounded-md transition-colors ${
                activeTab === 'players' ? 'bg-cyan-600 text-white' : 'text-slate-400 hover:text-white'
              }`}
            >
              <Activity size={13} />
              <span>Player Thresholds</span>
            </button>
            <button
              onClick={() => setActiveTab('recap')}
              className={`flex items-center gap-1.5 px-3 py-1 rounded-md transition-colors ${
                activeTab === 'recap' ? 'bg-cyan-600 text-white' : 'text-slate-400 hover:text-white'
              }`}
            >
              <FileText size={13} />
              <span>Executive Recap</span>
            </button>
            <button
              onClick={() => setActiveTab('evals')}
              className={`flex items-center gap-1.5 px-3 py-1 rounded-md transition-colors ${
                activeTab === 'evals' ? 'bg-cyan-600 text-white' : 'text-slate-400 hover:text-white'
              }`}
            >
              <Award size={13} />
              <span>Trust &amp; Tools</span>
            </button>
          </nav>
        </div>

        {/* Global Control Bar */}
        <div className="flex items-center gap-2">
          {/* Replay Controls */}
          <div className="flex items-center bg-slate-950 border border-slate-800 rounded-lg p-1 gap-1">
            <button
              onClick={handlePlayPause}
              className={`flex items-center gap-1.5 px-3 py-1 rounded-md text-xs font-bold transition-all active:scale-95 ${
                isRunning
                  ? 'bg-amber-600 hover:bg-amber-500 text-white'
                  : 'bg-emerald-600 hover:bg-emerald-500 text-white'
              }`}
            >
              {isRunning ? <Pause size={12} /> : <Play size={12} />}
              <span>{isRunning ? 'PAUSE' : 'PLAY'}</span>
            </button>

            <button
              onClick={handleRestart}
              className="p-1 hover:bg-slate-800 text-slate-400 hover:text-white rounded transition-colors"
              title="Restart Match Replay (Seed 21)"
            >
              <RotateCcw size={14} />
            </button>

            {/* Speed Selector */}
            <div className="flex items-center gap-0.5 border-l border-slate-800 pl-1 ml-1">
              {[1, 2, 4, 8].map(s => (
                <button
                  key={s}
                  onClick={() => handleSpeedChange(s)}
                  className={`px-1.5 py-0.5 text-[10px] font-mono rounded font-bold transition-colors ${
                    speed === s
                      ? 'bg-cyan-600 text-white'
                      : 'text-slate-400 hover:text-white'
                  }`}
                >
                  {s}x
                </button>
              ))}
            </div>
          </div>

          <div className={`hidden lg:flex items-center gap-1.5 text-[11px] font-mono px-2.5 py-1 rounded-lg border ${offlineMode ? 'text-slate-300 bg-slate-900 border-slate-700' : 'text-emerald-300 bg-emerald-950/60 border-emerald-500/40'}`}>
            <span className={`w-2 h-2 rounded-full inline-block ${offlineMode ? 'bg-slate-400' : 'bg-emerald-400 animate-pulse'}`}></span>
            <span>{offlineMode ? 'DETERMINISTIC OFFLINE MODE' : 'HOSTED MODEL ACTIVE'}</span>
          </div>
        </div>
      </header>

      {/* 2. Main Studio Content Area */}
      <main className="flex-1 p-3 md:p-5 max-w-[1720px] mx-auto w-full">
        {activeTab === 'studio' && (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
            {/* Left Column (TV Feed & HUD): 7 cols */}
            <section className="lg:col-span-7 flex flex-col gap-3">
              <div className="relative">
                <PitchCanvas
                  currentEvent={currentEvent}
                  summary={summary}
                  videoDetection={videoDetection}
                />
                <TVOverlay
                  summary={summary}
                  activeCue={activeCue}
                  currentEvent={currentEvent}
                  offlineMode={offlineMode}
                />
              </div>

              {/* Live Tactical Snapshot Strip */}
              <div className="grid grid-cols-3 gap-2 bg-slate-900/80 border border-slate-800 rounded-xl p-3 text-xs font-mono">
                <div className="flex flex-col">
                  <span className="text-[10px] text-slate-500">ACCUMULATED xG</span>
                  <span className="text-slate-100 font-bold tabular-nums">
                    SAL {summary?.xg?.SAL || '0.00'} vs {summary?.xg?.BRA || '0.00'} BRA
                  </span>
                </div>
                <div className="flex flex-col">
                  <span className="text-[10px] text-slate-500">PASS COMPLETION</span>
                  <span className="text-slate-100 font-bold tabular-nums">
                    SAL {summary?.passes?.SAL?.completed || 0} ({Math.round((summary?.passes?.SAL?.completed || 0) / Math.max(1, summary?.passes?.SAL?.attempted || 1) * 100)}%)
                  </span>
                </div>
                <div className="flex flex-col">
                  <span className="text-[10px] text-slate-500">CHAOS DENSITY</span>
                  <span className="text-cyan-400 font-bold tabular-nums">
                    {Math.round((summary?.chaos_index || 0.25) * 100)}% (7' Window)
                  </span>
                </div>
              </div>
            </section>

            {/* Right Column (The Desk + Viewer Mode): 5 cols */}
            <section className="lg:col-span-5 flex flex-col gap-5">
              <ProducerDesk
                cues={cues}
                onTakeCue={handleTakeCue}
                onKillCue={handleKillCue}
                videoAccuracy={videoAccuracy}
                refusals={refusals}
              />

              <ViewerMode
                audience={audience}
                onSelectAudience={setAudience}
                lang={lang}
                onSelectLang={setLang}
                onAskQuestion={handleAskQuestion}
              />
            </section>
          </div>
        )}

        {/* Tab 2: Player Intelligence */}
        {activeTab === 'players' && (
          <PlayerIntelligence
            players={summary?.players || []}
            selectedTeam={selectedTeam}
            onSelectTeam={setSelectedTeam}
          />
        )}

        {/* Tab 3: Executive Match Recap */}
        {activeTab === 'recap' && (
          <ExecutiveRecap lang={lang} />
        )}

        {/* Tab 4: Trust Checks & Scout Tools */}
        {activeTab === 'evals' && (
          <FoundryEvalsModal refusals={refusals} />
        )}
      </main>

      {/* 3. Footer / Audit strip */}
      <footer className="border-t border-slate-900 bg-slate-950 px-4 py-2 text-center text-[11px] text-slate-500 font-mono flex items-center justify-between">
        <span>PitchSense Studio • Deterministic metrics • Optional hosted model</span>
        <span>Crown Premier Championship (CPC) Synthetic League</span>
        <span>Service info: /.well-known/agent-card.json</span>
      </footer>
    </div>
  )
}
