const STEPS = ['scraping', 'embedding', 'storing', 'scoring', 'done'] as const

interface PipelineProgressProps {
  step: string
}

export function PipelineProgress({ step }: PipelineProgressProps) {
  const currentIdx = STEPS.indexOf(step as typeof STEPS[number])

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
      {STEPS.slice(0, -1).map((s, i) => {
        const isActive = s === step
        const isDone = currentIdx > i || step === 'done'
        return (
          <div key={s} style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
            <span style={{
              fontSize: '0.7rem',
              color: isActive ? '#6366f1' : isDone ? '#22c55e' : '#3f3f46',
              fontWeight: isActive ? 600 : 400,
            }}>
              {isActive && (
                <span style={{
                  display: 'inline-block', width: 6, height: 6,
                  borderRadius: '50%', background: '#6366f1',
                  marginRight: '0.25rem', animation: 'pulse 1.5s infinite',
                }} />
              )}
              {s}
            </span>
            {i < 3 && (
              <span style={{ color: '#3f3f46', fontSize: '0.65rem' }}>&rarr;</span>
            )}
          </div>
        )
      })}
      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.3; }
        }
      `}</style>
    </div>
  )
}
