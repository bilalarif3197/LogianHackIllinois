interface SentimentSliderProps {
  scores: { ticker: string; score: number }[]
}

function getZone(score: number): { label: string; color: string } {
  if (score >= 0.3)  return { label: 'BUY',  color: '#22c55e' }
  if (score <= -0.3) return { label: 'SELL', color: '#ef4444' }
  return                     { label: 'HOLD', color: '#eab308' }
}

function Gauge({ score }: { score: number }) {
  const pct = ((score + 1) / 2) * 100
  const { color } = getZone(score)

  return (
    <div style={{ position: 'relative', padding: '0 10px' }}>
      {/* Track shell */}
      <div style={{
        position: 'relative', height: 10, borderRadius: 999,
        overflow: 'visible',
        background: 'rgba(255,255,255,0.06)',
        boxShadow: 'inset 0 1px 3px rgba(0,0,0,0.5)',
      }}>
        {/* Full gradient track (dimmed) */}
        <div style={{
          position: 'absolute', inset: 0, borderRadius: 999,
          background: 'linear-gradient(to right, #ef4444 0%, #f97316 25%, #eab308 50%, #84cc16 75%, #22c55e 100%)',
          opacity: 0.2,
        }} />

        {/* Filled gradient (vivid, clipped to pct) */}
        <div style={{
          position: 'absolute', top: 0, left: 0, bottom: 0,
          width: `${pct}%`, borderRadius: '999px 0 0 999px',
          background: 'linear-gradient(to right, #ef4444 0%, #f97316 25%, #eab308 50%, #84cc16 75%, #22c55e 100%)',
          backgroundSize: `${10000 / Math.max(pct, 1)}%`,
          opacity: 0.9,
          transition: 'width 0.55s cubic-bezier(0.4,0,0.2,1)',
        }} />

        {/* Zone boundary ticks */}
        {[35, 50, 65].map((t) => (
          <div key={t} style={{
            position: 'absolute', top: -3, bottom: -3,
            left: `${t}%`, transform: 'translateX(-50%)',
            width: 1.5, background: 'rgba(0,0,0,0.6)',
            borderRadius: 1, zIndex: 1,
          }} />
        ))}

        {/* Thumb */}
        <div style={{
          position: 'absolute', top: '50%',
          left: `${pct}%`,
          transform: 'translate(-50%, -50%)',
          width: 20, height: 20, borderRadius: '50%',
          background: `radial-gradient(circle at 35% 35%, #fff2, transparent 60%), ${color}`,
          border: '2.5px solid #0f1117',
          boxShadow: `0 0 0 1.5px ${color}66, 0 2px 8px rgba(0,0,0,0.5), 0 0 14px ${color}55`,
          zIndex: 2,
          transition: 'left 0.55s cubic-bezier(0.4,0,0.2,1), background 0.4s ease, box-shadow 0.4s ease',
        }} />
      </div>

      {/* Zone labels */}
      <div style={{
        display: 'flex', justifyContent: 'space-between',
        marginTop: '0.45rem', userSelect: 'none',
      }}>
        <span style={{ fontSize: '0.6rem', fontWeight: 700, color: '#ef4444', opacity: 0.75 }}>SELL −1</span>
        <span style={{ fontSize: '0.6rem', fontWeight: 700, color: '#52525b' }}>0</span>
        <span style={{ fontSize: '0.6rem', fontWeight: 700, color: '#22c55e', opacity: 0.75 }}>BUY +1</span>
      </div>
    </div>
  )
}

export function SentimentSlider({ scores }: SentimentSliderProps) {
  return (
    <div style={{
      background: '#1a1d27', border: '1px solid #2a2d3a', borderRadius: '8px',
      padding: '1.25rem', marginBottom: '1.5rem',
    }}>
      <div style={{ fontSize: '0.85rem', fontWeight: 600, marginBottom: '1rem', color: '#e4e4e7' }}>
        Sentiment Scores
      </div>

      {scores.length === 0 ? (
        <div style={{
          color: '#3f3f46', fontSize: '0.8rem', textAlign: 'center',
          padding: '0.75rem 0', letterSpacing: '0.02em',
        }}>
          Waiting for scores...
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          {scores.map(({ ticker, score }) => {
            const { label, color } = getZone(score)
            return (
              <div key={ticker}>
                <div style={{
                  display: 'flex', justifyContent: 'space-between',
                  alignItems: 'center', marginBottom: '0.65rem',
                }}>
                  <span style={{ fontSize: '0.82rem', fontWeight: 700, color: '#e4e4e7', letterSpacing: '0.04em' }}>
                    {ticker}
                  </span>
                  <span style={{
                    fontSize: '0.7rem', fontWeight: 700, color,
                    background: `${color}1a`, border: `1px solid ${color}44`,
                    borderRadius: 5, padding: '0.18rem 0.55rem',
                    letterSpacing: '0.07em',
                  }}>
                    {label} &nbsp;{score >= 0 ? '+' : ''}{score.toFixed(3)}
                  </span>
                </div>
                <Gauge score={score} />
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
