import { useState } from 'react'
import type { TickerInfo, ArticleSentiment } from '../types'
import { TickerSelector } from './TickerSelector'
import { DataSourceToggle } from './DataSourceToggle'
import { SentimentSlider } from './SentimentSlider'
import { SentimentTimeline } from './SentimentTimeline'
import { ScoreCard } from './ScoreCard'

interface TickerData {
  score: number
  recommendation: string
  pipelineStep: string
  articlesProcessed: number
  articlesTotal: number
  topArticles: ArticleSentiment[]
}

interface DashboardProps {
  allTickers: TickerInfo[]
  monitoredTickers: string[]
  tickerData: Record<string, TickerData>
  dataSource: string
  onStartMonitoring: (tickers: string[]) => void
  onStopMonitoring: (ticker: string) => void
  onToggleSource: (source: 'mock' | 'live') => void
}

export function Dashboard({
  allTickers, monitoredTickers, tickerData, dataSource,
  onStartMonitoring, onStopMonitoring, onToggleSource,
}: DashboardProps) {
  const [selectedTicker, setSelectedTicker] = useState<string | null>(null)

  // Show all monitored tickers that have a score (not just 'done'), so the
  // slider stays visible during pipeline processing instead of disappearing.
  const barData = monitoredTickers
    .filter((t) => tickerData[t] != null)
    .map((t) => ({ ticker: t, score: tickerData[t].score }))

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '1rem' }}>
        <div style={{ flex: 1, minWidth: 300 }}>
          <TickerSelector
            tickers={allTickers}
            monitoredTickers={monitoredTickers}
            onStart={onStartMonitoring}
            onStop={onStopMonitoring}
          />
        </div>
        <DataSourceToggle dataSource={dataSource} onToggle={onToggleSource} />
      </div>

      <SentimentSlider scores={barData} />

      <SentimentTimeline selectedTicker={selectedTicker} />

      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
        {monitoredTickers.map((t) => {
          const data = tickerData[t]
          return (
            <div key={t} onClick={() => setSelectedTicker(t)}>
              <ScoreCard
                ticker={t}
                score={data?.score ?? 0}
                recommendation={data?.recommendation ?? 'HOLD'}
                pipelineStep={data?.pipelineStep ?? 'pending'}
                articlesProcessed={data?.articlesProcessed ?? 0}
                articlesTotal={data?.articlesTotal ?? 0}
                topArticles={data?.topArticles ?? []}
              />
            </div>
          )
        })}
      </div>

      {monitoredTickers.length === 0 && (
        <div style={{
          textAlign: 'center', padding: '4rem 2rem', color: '#71717a',
          fontSize: '0.9rem',
        }}>
          Search for tickers above and click "Monitor" to start streaming sentiment analysis.
        </div>
      )}
    </div>
  )
}
