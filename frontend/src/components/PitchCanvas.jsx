import React, { useRef, useEffect, useState } from 'react'

// Base Tactical 4-3-3 Roster Coordinates (Meters: 105 x 68)
const INITIAL_SAL_PLAYERS = [
  { code: "sal_01", num: 1, x: 6, y: 34, name: "Vance", role: "GK", line: "GK" },
  { code: "sal_02", num: 2, x: 28, y: 12, name: "Holt", role: "RB", line: "DEF" },
  { code: "sal_04", num: 4, x: 22, y: 24, name: "Cross", role: "CB", line: "DEF" },
  { code: "sal_05", num: 5, x: 22, y: 44, name: "O'Rourke", role: "CB", line: "DEF" },
  { code: "sal_03", num: 3, x: 28, y: 56, name: "Finch", role: "LB", line: "DEF" },
  { code: "sal_06", num: 6, x: 42, y: 34, name: "Danvers", role: "DM", line: "MID" },
  { code: "sal_08", num: 8, x: 55, y: 22, name: "Rosmere", role: "CM", line: "MID" },
  { code: "sal_10", num: 10, x: 64, y: 44, name: "Bram", role: "AM", line: "MID" },
  { code: "sal_07", num: 7, x: 74, y: 14, name: "Thorne", role: "RW", line: "FWD" },
  { code: "sal_11", num: 11, x: 74, y: 54, name: "Vance", role: "LW", line: "FWD" },
  { code: "sal_09", num: 9, x: 82, y: 34, name: "Visser", role: "CF", line: "FWD" },
]

const INITIAL_BRA_PLAYERS = [
  { code: "bra_01", num: 1, x: 99, y: 34, name: "Cassian", role: "GK", line: "GK" },
  { code: "bra_02", num: 2, x: 77, y: 56, name: "Alder", role: "RB", line: "DEF" },
  { code: "bra_04", num: 4, x: 83, y: 44, name: "Ward", role: "CB", line: "DEF" },
  { code: "bra_05", num: 5, x: 83, y: 24, name: "Fletcher", role: "CB", line: "DEF" },
  { code: "bra_03", num: 3, x: 77, y: 12, name: "Val", role: "LB", line: "DEF" },
  { code: "bra_06", num: 6, x: 63, y: 34, name: "Rowe", role: "DM", line: "MID" },
  { code: "bra_08", num: 8, x: 50, y: 46, name: "Sterling", role: "CM", line: "MID" },
  { code: "bra_10", num: 10, x: 41, y: 24, name: "Mercer", role: "AM", line: "MID" },
  { code: "bra_07", num: 7, x: 31, y: 54, name: "Lind", role: "RW", line: "FWD" },
  { code: "bra_11", num: 11, x: 31, y: 14, name: "Diaz", role: "LW", line: "FWD" },
  { code: "bra_09", num: 9, x: 23, y: 34, name: "Vance", role: "CF", line: "FWD" },
]

export default function PitchCanvas({ currentEvent, summary, videoDetection }) {
  const canvasRef = useRef(null)
  const trailRef = useRef([])
  const animFrameRef = useRef(null)

  // Current interpolated animated positions
  const positionsRef = useRef({
    sal: INITIAL_SAL_PLAYERS.map(p => ({ ...p, curX: p.x, curY: p.y })),
    bra: INITIAL_BRA_PLAYERS.map(p => ({ ...p, curX: p.x, curY: p.y })),
    ball: { curX: 52.5, curY: 34.0 }
  })

  const [showTacticalLines, setShowTacticalLines] = useState(true)

  // Calculate dynamic target positions based on ball phase and active actors
  const computeTargets = (event) => {
    const ballX = event?.pos?.x ?? 52.5
    const ballY = event?.pos?.y ?? 34.0
    const endX = event?.end_pos?.x ?? ballX
    const endY = event?.end_pos?.y ?? ballY

    // Pitch center displacement
    const dx = ballX - 52.5
    const dy = ballY - 34.0

    const actorCode = event?.actor
    const recipientCode = event?.recipient

    // 1. Calculate Saltmarsh Rovers targets (attacking left to right)
    const salTargets = INITIAL_SAL_PLAYERS.map(p => {
      // If this player is the active ball carrier, place directly on ball
      if (p.code === actorCode) {
        return { ...p, targetX: ballX, targetY: ballY, isActor: true }
      }
      // If this player is receiving the pass, move toward pass end position
      if (p.code === recipientCode && event?.end_pos) {
        return { ...p, targetX: endX, targetY: endY, isRecipient: true }
      }

      // Dynamic unit shifting with ball progression
      let shiftWeightX = 0.45
      let shiftWeightY = 0.30

      if (p.line === 'GK') {
        shiftWeightX = 0.12
        shiftWeightY = 0.15
      } else if (p.line === 'DEF') {
        shiftWeightX = 0.40
      } else if (p.line === 'MID') {
        shiftWeightX = 0.52
      } else if (p.line === 'FWD') {
        shiftWeightX = 0.60
      }

      let tx = p.x + (dx * shiftWeightX)
      let ty = p.y + (dy * shiftWeightY)

      // Keep within boundaries
      tx = Math.max(3.0, Math.min(101.0, tx))
      ty = Math.max(4.0, Math.min(64.0, ty))

      return { ...p, targetX: tx, targetY: ty, isActor: false, isRecipient: false }
    })

    // 2. Calculate Brackfield Athletic targets (attacking right to left)
    const braTargets = INITIAL_BRA_PLAYERS.map(p => {
      // If this player is the active ball carrier
      if (p.code === actorCode) {
        return { ...p, targetX: ballX, targetY: ballY, isActor: true }
      }
      // If this player is receiving
      if (p.code === recipientCode && event?.end_pos) {
        return { ...p, targetX: endX, targetY: endY, isRecipient: true }
      }

      // If opponent is making a tackle, move nearest defender near the ball
      if (event?.type === 'tackle' && p.role === 'CB' && Math.abs(p.x - ballX) < 15) {
        return { ...p, targetX: ballX + 1.2, targetY: ballY - 0.8, isPressing: true }
      }

      // Dynamic unit shifting with ball progression
      let shiftWeightX = 0.45
      let shiftWeightY = 0.30

      if (p.line === 'GK') {
        shiftWeightX = 0.10
        shiftWeightY = 0.15
      } else if (p.line === 'DEF') {
        shiftWeightX = 0.38
      } else if (p.line === 'MID') {
        shiftWeightX = 0.50
      } else if (p.line === 'FWD') {
        shiftWeightX = 0.58
      }

      let tx = p.x + (dx * shiftWeightX)
      let ty = p.y + (dy * shiftWeightY)

      tx = Math.max(4.0, Math.min(102.0, tx))
      ty = Math.max(4.0, Math.min(64.0, ty))

      return { ...p, targetX: tx, targetY: ty, isActor: false, isRecipient: false }
    })

    return { salTargets, braTargets, ballTarget: { x: ballX, y: ballY } }
  }

  // Animation Loop: smoothly lerp players toward targets on each frame
  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    const width = canvas.width
    const height = canvas.height

    const scaleX = (x) => (Math.max(0, Math.min(105, x)) / 105) * width
    const scaleY = (y) => (Math.max(0, Math.min(68, y)) / 68) * height

    let isRunning = true

    const render = () => {
      if (!isRunning) return

      const targets = computeTargets(currentEvent)

      // Lerp speeds (smooth athletic motion)
      const playerLerp = 0.18
      const ballLerp = 0.25

      // Update positions
      positionsRef.current.sal.forEach((p, i) => {
        const t = targets.salTargets[i]
        p.curX += (t.targetX - p.curX) * playerLerp
        p.curY += (t.targetY - p.curY) * playerLerp
        p.isActor = t.isActor
        p.isRecipient = t.isRecipient
      })

      positionsRef.current.bra.forEach((p, i) => {
        const t = targets.braTargets[i]
        p.curX += (t.targetX - p.curX) * playerLerp
        p.curY += (t.targetY - p.curY) * playerLerp
        p.isActor = t.isActor
        p.isRecipient = t.isRecipient
      })

      const ball = positionsRef.current.ball
      ball.curX += (targets.ballTarget.x - ball.curX) * ballLerp
      ball.curY += (targets.ballTarget.y - ball.curY) * ballLerp

      // --- CLEAR & DRAW PITCH ---
      ctx.fillStyle = '#065f46' // Deep pitch emerald
      ctx.fillRect(0, 0, width, height)

      // Grass mowing stripes
      ctx.fillStyle = '#047857'
      const stripes = 10
      const stripeW = width / stripes
      for (let i = 0; i < stripes; i += 2) {
        ctx.fillRect(i * stripeW, 0, stripeW, height)
      }

      // Pitch lines
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.75)'
      ctx.lineWidth = 2

      const pad = 12
      ctx.strokeRect(pad, pad, width - pad * 2, height - pad * 2)

      // Halfway line
      ctx.beginPath()
      ctx.moveTo(width / 2, pad)
      ctx.lineTo(width / 2, height - pad)
      ctx.stroke()

      // Center circle & spot
      ctx.beginPath()
      ctx.arc(width / 2, height / 2, (9.15 / 105) * width, 0, Math.PI * 2)
      ctx.stroke()
      ctx.beginPath()
      ctx.arc(width / 2, height / 2, 3, 0, Math.PI * 2)
      ctx.fillStyle = '#ffffff'
      ctx.fill()

      // Penalty areas (16.5m box)
      const penW = (16.5 / 105) * width
      const penH = (40.32 / 68) * height
      const penY = (height - penH) / 2
      ctx.strokeRect(pad, penY, penW, penH)
      ctx.strokeRect(width - pad - penW, penY, penW, penH)

      // Goal boxes (5.5m box)
      const goalBoxW = (5.5 / 105) * width
      const goalBoxH = (18.32 / 68) * height
      const goalBoxY = (height - goalBoxH) / 2
      ctx.strokeRect(pad, goalBoxY, goalBoxW, goalBoxH)
      ctx.strokeRect(width - pad - goalBoxW, goalBoxY, goalBoxW, goalBoxH)

      // --- OPTIONAL TACTICAL UNIT CONNECTORS ---
      if (showTacticalLines) {
        // Saltmarsh defensive line (Teal dashed)
        const salDefs = positionsRef.current.sal.filter(p => p.line === 'DEF')
        if (salDefs.length >= 2) {
          ctx.beginPath()
          ctx.strokeStyle = 'rgba(45, 212, 191, 0.25)'
          ctx.lineWidth = 1.5
          ctx.setLineDash([3, 3])
          salDefs.forEach((p, idx) => {
            const px = scaleX(p.curX)
            const py = scaleY(p.curY)
            if (idx === 0) ctx.moveTo(px, py)
            else ctx.lineTo(px, py)
          })
          ctx.stroke()
          ctx.setLineDash([])
        }

        // Brackfield defensive line (Rose dashed)
        const braDefs = positionsRef.current.bra.filter(p => p.line === 'DEF')
        if (braDefs.length >= 2) {
          ctx.beginPath()
          ctx.strokeStyle = 'rgba(244, 63, 94, 0.25)'
          ctx.lineWidth = 1.5
          ctx.setLineDash([3, 3])
          braDefs.forEach((p, idx) => {
            const px = scaleX(p.curX)
            const py = scaleY(p.curY)
            if (idx === 0) ctx.moveTo(px, py)
            else ctx.lineTo(px, py)
          })
          ctx.stroke()
          ctx.setLineDash([])
        }
      }

      // --- DRAW PASS / SHOT VECTOR ---
      if (currentEvent && currentEvent.pos && currentEvent.end_pos) {
        const sx = scaleX(currentEvent.pos.x)
        const sy = scaleY(currentEvent.pos.y)
        const ex = scaleX(currentEvent.end_pos.x)
        const ey = scaleY(currentEvent.end_pos.y)

        ctx.beginPath()
        ctx.moveTo(sx, sy)
        ctx.lineTo(ex, ey)
        ctx.strokeStyle = currentEvent.type === 'goal'
          ? '#22c55e'
          : (currentEvent.type === 'shot' ? '#f59e0b' : '#38bdf8')
        ctx.lineWidth = 3
        ctx.setLineDash([4, 4])
        ctx.stroke()
        ctx.setLineDash([])

        // Arrow head
        const angle = Math.atan2(ey - sy, ex - sx)
        ctx.beginPath()
        ctx.moveTo(ex, ey)
        ctx.lineTo(ex - 10 * Math.cos(angle - Math.PI / 6), ey - 10 * Math.sin(angle - Math.PI / 6))
        ctx.lineTo(ex - 10 * Math.cos(angle + Math.PI / 6), ey - 10 * Math.sin(angle + Math.PI / 6))
        ctx.fillStyle = ctx.strokeStyle
        ctx.fill()
      }

      // --- DRAW SALTMARSH PLAYERS (Marine Teal) ---
      positionsRef.current.sal.forEach(p => {
        const px = scaleX(p.curX)
        const py = scaleY(p.curY)

        // Ball Carrier Aura
        if (p.isActor) {
          ctx.beginPath()
          ctx.arc(px, py, 15, 0, Math.PI * 2)
          ctx.strokeStyle = '#2dd4bf'
          ctx.lineWidth = 2
          ctx.stroke()
        }

        // Recipient Halo
        if (p.isRecipient) {
          ctx.beginPath()
          ctx.arc(px, py, 14, 0, Math.PI * 2)
          ctx.strokeStyle = 'rgba(56, 189, 248, 0.8)'
          ctx.lineWidth = 1.5
          ctx.setLineDash([2, 2])
          ctx.stroke()
          ctx.setLineDash([])
        }

        // Player Circle
        ctx.beginPath()
        ctx.arc(px, py, 9, 0, Math.PI * 2)
        ctx.fillStyle = p.isActor ? '#0d9488' : '#0f766e'
        ctx.fill()
        ctx.lineWidth = 1.5
        ctx.strokeStyle = '#ffffff'
        ctx.stroke()

        // Squad Number
        ctx.fillStyle = '#ffffff'
        ctx.font = 'bold 9px sans-serif'
        ctx.textAlign = 'center'
        ctx.textBaseline = 'middle'
        ctx.fillText(p.num, px, py)

        // Compact Player Label (Below Dot)
        ctx.fillStyle = 'rgba(255, 255, 255, 0.85)'
        ctx.font = '8px sans-serif'
        ctx.fillText(p.name, px, py + 14)
      })

      // --- DRAW BRACKFIELD PLAYERS (Vermilion / Rose) ---
      positionsRef.current.bra.forEach(p => {
        const px = scaleX(p.curX)
        const py = scaleY(p.curY)

        // Ball Carrier Aura
        if (p.isActor) {
          ctx.beginPath()
          ctx.arc(px, py, 15, 0, Math.PI * 2)
          ctx.strokeStyle = '#fb7185'
          ctx.lineWidth = 2
          ctx.stroke()
        }

        // Recipient Halo
        if (p.isRecipient) {
          ctx.beginPath()
          ctx.arc(px, py, 14, 0, Math.PI * 2)
          ctx.strokeStyle = 'rgba(251, 113, 133, 0.8)'
          ctx.lineWidth = 1.5
          ctx.setLineDash([2, 2])
          ctx.stroke()
          ctx.setLineDash([])
        }

        // Player Circle
        ctx.beginPath()
        ctx.arc(px, py, 9, 0, Math.PI * 2)
        ctx.fillStyle = p.isActor ? '#be123c' : '#e11d48'
        ctx.fill()
        ctx.lineWidth = 1.5
        ctx.strokeStyle = '#ffffff'
        ctx.stroke()

        // Squad Number
        ctx.fillStyle = '#ffffff'
        ctx.font = 'bold 9px sans-serif'
        ctx.textAlign = 'center'
        ctx.textBaseline = 'middle'
        ctx.fillText(p.num, px, py)

        // Compact Player Label (Below Dot)
        ctx.fillStyle = 'rgba(255, 255, 255, 0.85)'
        ctx.font = '8px sans-serif'
        ctx.fillText(p.name, px, py + 14)
      })

      // --- DRAW BALL & MOTION TRAIL ---
      const bx = scaleX(ball.curX)
      const by = scaleY(ball.curY)

      trailRef.current.push({ x: bx, y: by })
      if (trailRef.current.length > 8) trailRef.current.shift()

      // Motion Trail
      trailRef.current.forEach((pt, idx) => {
        const alpha = ((idx + 1) / trailRef.current.length) * 0.4
        ctx.beginPath()
        ctx.arc(pt.x, pt.y, 4, 0, Math.PI * 2)
        ctx.fillStyle = `rgba(250, 204, 21, ${alpha})`
        ctx.fill()
      })

      // Ball Outer Glow & Core
      ctx.beginPath()
      ctx.arc(bx, by, 7, 0, Math.PI * 2)
      ctx.fillStyle = '#facc15'
      ctx.fill()
      ctx.beginPath()
      ctx.arc(bx, by, 4, 0, Math.PI * 2)
      ctx.fillStyle = '#ffffff'
      ctx.fill()
      ctx.lineWidth = 1
      ctx.strokeStyle = '#000000'
      ctx.stroke()

      // Trajectory estimate indicator
      if (videoDetection && currentEvent?.pos) {
        ctx.beginPath()
        ctx.arc(bx, by, 18, 0, Math.PI * 2)
        ctx.strokeStyle = '#38bdf8'
        ctx.lineWidth = 1.5
        ctx.setLineDash([3, 3])
        ctx.stroke()
        ctx.setLineDash([])
      }

      animFrameRef.current = requestAnimationFrame(render)
    }

    animFrameRef.current = requestAnimationFrame(render)

    return () => {
      isRunning = false
      if (animFrameRef.current) {
        cancelAnimationFrame(animFrameRef.current)
      }
    }
  }, [currentEvent, summary, videoDetection, showTacticalLines])

  return (
    <div className="relative w-full aspect-[16/10] bg-emerald-950 rounded-xl overflow-hidden border border-emerald-800/40 shadow-2xl">
      <canvas
        ref={canvasRef}
        width={700}
        height={440}
        className="w-full h-full object-contain"
      />

      {/* Tactical formation controls */}
      <div className="absolute top-3 right-3 flex items-center gap-2">
        <button
          onClick={() => setShowTacticalLines(prev => !prev)}
          className="bg-slate-950/80 backdrop-blur-md px-2 py-0.5 rounded border border-slate-700/50 text-[10px] font-mono text-slate-300 hover:text-white transition-colors"
          title="Toggle Tactical Formation Lines"
        >
          {showTacticalLines ? "LINES ON" : "LINES OFF"}
        </button>

        <div className="flex items-center gap-2 bg-slate-950/80 backdrop-blur-md px-2.5 py-1 rounded-md border border-cyan-500/30 text-[11px] font-mono text-cyan-400">
          <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse"></span>
          <span>DYNAMIC 4-3-3 TACTICAL SHIFT</span>
        </div>
      </div>
    </div>
  )
}
