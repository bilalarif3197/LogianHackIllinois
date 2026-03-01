import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, ReferenceLine,
  Tooltip, ResponsiveContainer, Cell,
} from 'recharts'

interface ScoreBarChartProps {
  scores: { ticker: string; score: number }[]
}

function getBarColor(score: number) {
  if (score >= 0.3) return '#22c55e'
  if (score <= -0.3) return '#ef4444'
  return '#eab308'
}

export function ScoreBarChart({ scores }: ScoreBarChartProps) {
  if (scores.length === 0) return null

  return (
    <div style={{
      background: '#1a1d27', border: '1px solid #2a2d3a', borderRadius: '8px',
      padding: '1.25rem', marginBottom: '1.5rem',
    }}>
      <div style={{ fontSize: '0.85rem', fontWeight: 600, marginBottom: '1rem', color: '#e4e4e7' }}>
        Current Sentiment Scores
      </div>
      <ResponsiveContainer width="100%" height={200}>
        <BarChart data={scores} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#2a2d3a" />
          <XAxis dataKey="ticker" tick={{ fill: '#71717a', fontSize: 11 }} />
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
          <Bar dataKey="score" radius={[4, 4, 0, 0]}>
            {scores.map((entry, idx) => (
              <Cell key={idx} fill={getBarColor(entry.score)} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
