import { useState, useCallback } from 'react'
import { useWebSocket } from './hooks/useWebSocket'
import { useTickers } from './hooks/useTickers'
import { StatusBar } from './components/StatusBar'
import { Dashboard } from './components/Dashboard'
import type { WSMessage, ArticleSentiment } from './types'

interface TickerData {
  score: number
  recommendation: string
  pipelineStep: string
  articlesProcessed: number
  articlesTotal: number
  topArticles: ArticleSentiment[]
}

const wsUrl = `${window.location.protocol === 'https:' ? 'wss' : 'ws'}://${window.location.host}/ws`

export default function App() {
  const { tickers } = useTickers()
  const [monitoredTickers, setMonitoredTickers] = useState<string[]>([])
  const [tickerData, setTickerData] = useState<Record<string, TickerData>>({})
  const [dataSource, setDataSource] = useState('mock')
  const [modelsLoaded, setModelsLoaded] = useState(false)

  const handleMessage = useCallback((msg: WSMessage) => {
    switch (msg.type) {
      case 'score_update':
        setTickerData((prev) => ({
          ...prev,
          [msg.data.ticker]: {
            score: msg.data.score,
            recommendation: msg.data.recommendation,
            pipelineStep: 'done',
            articlesProcessed: msg.data.articles_processed,
            articlesTotal: msg.data.articles_total,
            topArticles: msg.data.top_articles as ArticleSentiment[],
          },
        }))
        break

      case 'pipeline_progress':
        setTickerData((prev) => ({
          ...prev,
          [msg.data.ticker]: {
            ...prev[msg.data.ticker],
            pipelineStep: msg.data.step,
          },
        }))
        break

      case 'initial_state':
        setDataSource(msg.data.data_source)
        setModelsLoaded(msg.data.models_loaded)
        if (msg.data.monitored_tickers.length > 0) {
          setMonitoredTickers(msg.data.monitored_tickers)
        }
        if (msg.data.scores) {
          const newData: Record<string, TickerData> = {}
          for (const [ticker, s] of Object.entries(msg.data.scores)) {
            newData[ticker] = {
              score: s.score,
              recommendation: s.recommendation,
              pipelineStep: s.pipeline_step,
              articlesProcessed: 0,
              articlesTotal: 0,
              topArticles: [],
            }
          }
          setTickerData((prev) => ({ ...prev, ...newData }))
        }
        break

      case 'engine_status':
        setModelsLoaded(msg.data.models_loaded)
        setDataSource(msg.data.data_source)
        break
    }
  }, [])

  const { connected } = useWebSocket(wsUrl, handleMessage)

  const handleStartMonitoring = async (tickers: string[]) => {
    setMonitoredTickers((prev) => [...new Set([...prev, ...tickers])])
    for (const t of tickers) {
      setTickerData((prev) => ({
        ...prev,
        [t]: prev[t] || {
          score: 0, recommendation: 'HOLD', pipelineStep: 'pending',
          articlesProcessed: 0, articlesTotal: 0, topArticles: [],
        },
      }))
    }

    await fetch('/api/monitor', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ tickers, action: 'start' }),
    })
  }

  const handleStopMonitoring = async (ticker: string) => {
    setMonitoredTickers((prev) => prev.filter((t) => t !== ticker))
    setTickerData((prev) => {
      const next = { ...prev }
      delete next[ticker]
      return next
    })

    await fetch('/api/monitor', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ tickers: [ticker], action: 'stop' }),
    })
  }

  const handleToggleSource = async (source: 'mock' | 'live') => {
    setDataSource(source)
    await fetch('/api/source', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ source }),
    })
  }

  return (
    <div style={{
      fontFamily: "'SF Mono', 'Fira Code', 'Consolas', monospace",
      background: '#0f1117', color: '#e4e4e7',
      minHeight: '100vh', padding: '2rem',
    }}>
      <h1 style={{ fontSize: '1.5rem', marginBottom: '0.25rem' }}>
        Logian Sentiment Dashboard
      </h1>
      <p style={{ color: '#71717a', fontSize: '0.85rem', marginBottom: '1.5rem' }}>
        Real-time stock sentiment analysis — scrape, embed, store, score
      </p>

      <StatusBar
        connected={connected}
        modelsLoaded={modelsLoaded}
        dataSource={dataSource}
        monitoredCount={monitoredTickers.length}
      />

      <Dashboard
        allTickers={tickers}
        monitoredTickers={monitoredTickers}
        tickerData={tickerData}
        dataSource={dataSource}
        onStartMonitoring={handleStartMonitoring}
        onStopMonitoring={handleStopMonitoring}
        onToggleSource={handleToggleSource}
      />
    </div>
  )
}
