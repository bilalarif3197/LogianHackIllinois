interface StatusBarProps {
  connected: boolean
  modelsLoaded: boolean
  dataSource: string
  monitoredCount: number
}

export function StatusBar({ connected, modelsLoaded, dataSource, monitoredCount }: StatusBarProps) {
  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      gap: '1.5rem',
      padding: '0.75rem 1.25rem',
      background: '#1a1d27',
      borderRadius: '8px',
      fontSize: '0.8rem',
      color: '#71717a',
      marginBottom: '1.5rem',
    }}>
      <span style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
        <span style={{
          width: 8, height: 8, borderRadius: '50%',
          background: connected ? '#22c55e' : '#ef4444',
          display: 'inline-block',
        }} />
        {connected ? 'Connected' : 'Disconnected'}
      </span>
      <span>Models: {modelsLoaded ? 'Loaded' : 'Loading...'}</span>
      <span>Source: {dataSource === 'mock' ? 'Mock Feed' : 'Yahoo Finance'}</span>
      <span>Monitoring: {monitoredCount} tickers</span>
    </div>
  )
}
