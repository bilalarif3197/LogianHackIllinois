import { useEffect, useState } from 'react'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, ReferenceLine,
  Tooltip, ResponsiveContainer,
} from 'recharts'
import type { ScorePoint } from '../types'

interface SentimentTimelineProps {
  selectedTicker: string | null
}

export function SentimentTimeline({ selectedTicker }: SentimentTimelineProps) {
  const [history, setHistory] = useState<ScorePoint[]>([])

  useEffect(() => {
    if (!selectedTicker) {
      setHistory([])
      return
    }

    fetch(`/api/history/${selectedTicker}`)
      .then((r) => r.json())
      .then((data) => setHistory(data.history || []))
      .catch(() => setHistory([]))
  }, [selectedTicker])

  if (!selectedTicker) return null
  if (history.length < 2) {
    return (
      <div style={{
        background: '#1a1d27', border: '1px solid #2a2d3a', borderRadius: '8px',
        padding: '1.25rem', marginBottom: '1.5rem', color: '#71717a',
        fontSize: '0.85rem', textAlign: 'center',
      }}>
        Waiting for more data points for {selectedTicker}...
      </div>
    )
  }

  const formatted = history.map((p) => ({
    ...p,
    time: new Date(p.timestamp).toLocaleTimeString(),
  }))

  return (
    <div style={{
      background: '#1a1d27', border: '1px solid #2a2d3a', borderRadius: '8px',
      padding: '1.25rem', marginBottom: '1.5rem',
    }}>
      <div style={{ fontSize: '0.85rem', fontWeight: 600, marginBottom: '1rem', color: '#e4e4e7' }}>
        Sentiment Timeline — {selectedTicker}
      </div>
      <ResponsiveContainer width="100%" height={200}>
        <LineChart data={formatted} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#2a2d3a" />
          <XAxis dataKey="time" tick={{ fill: '#71717a', fontSize: 10 }} />
          <YAxis domain={[-1, 1]} tick={{ fill: '#71717a', fontSize: 11 }} />
          <Tooltip
            contentStyle={{
              background: '#1a1d27', border: '1px solid #2a2d3a',
              borderRadius: '6px', fontSize: '0.8rem', color: '#e4e4e7',
            }}
          />
          <ReferenceLine y={0.3} stroke="#22c55e" strokeDasharray="4 4" strokeOpacity={0.4} />
          <ReferenceLine y={-0.3} stroke="#ef4444" strokeDasharray="4 4" strokeOpacity={0.4} />
          <ReferenceLine y={0} stroke="#3f3f46" />
          <Line
            type="monotone" dataKey="score" stroke="#6366f1"
            strokeWidth={2} dot={{ r: 3, fill: '#6366f1' }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
