interface DataSourceToggleProps {
  dataSource: string
  onToggle: (source: 'mock' | 'live') => void
}

export function DataSourceToggle({ dataSource, onToggle }: DataSourceToggleProps) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
      <span style={{ fontSize: '0.85rem', color: '#71717a' }}>Data Source:</span>
      <div style={{
        display: 'flex', background: '#1a1d27', borderRadius: '6px',
        border: '1px solid #2a2d3a', overflow: 'hidden',
      }}>
        <button
          onClick={() => onToggle('mock')}
          style={{
            padding: '0.5rem 1rem', border: 'none', cursor: 'pointer',
            fontFamily: 'inherit', fontSize: '0.8rem',
            background: dataSource === 'mock' ? '#6366f1' : 'transparent',
            color: dataSource === 'mock' ? '#fff' : '#71717a',
            transition: 'all 0.2s',
          }}
        >
          Mock Feed
        </button>
        <button
          onClick={() => onToggle('live')}
          style={{
            padding: '0.5rem 1rem', border: 'none', cursor: 'pointer',
            fontFamily: 'inherit', fontSize: '0.8rem',
            background: dataSource === 'live' ? '#6366f1' : 'transparent',
            color: dataSource === 'live' ? '#fff' : '#71717a',
            transition: 'all 0.2s',
          }}
        >
          Yahoo Finance
        </button>
      </div>
    </div>
  )
}
