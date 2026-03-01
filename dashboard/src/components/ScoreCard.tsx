import { useState } from 'react'
import type { ArticleSentiment } from '../types'
import { ArticleList } from './ArticleList'
import { PipelineProgress } from './PipelineProgress'

interface ScoreCardProps {
  ticker: string
  score: number
  recommendation: string
  pipelineStep: string
  articlesProcessed: number
  articlesTotal: number
  topArticles: ArticleSentiment[]
}

function getColor(score: number) {
  if (score >= 0.3) return { bg: 'rgba(34,197,94,0.12)', text: '#22c55e', label: 'BUY' }
  if (score <= -0.3) return { bg: 'rgba(239,68,68,0.12)', text: '#ef4444', label: 'SELL' }
  return { bg: 'rgba(234,179,8,0.12)', text: '#eab308', label: 'HOLD' }
}

export function ScoreCard({
  ticker, score, recommendation, pipelineStep,
  articlesProcessed, articlesTotal, topArticles,
}: ScoreCardProps) {
  const [expanded, setExpanded] = useState(false)
  const color = getColor(score)
  const isDone = pipelineStep === 'done'

  return (
    <div
      onClick={() => setExpanded(!expanded)}
      style={{
        background: '#1a1d27', border: '1px solid #2a2d3a', borderRadius: '8px',
        padding: '1rem 1.25rem', cursor: 'pointer', transition: 'border-color 0.2s',
      }}
      onMouseEnter={(e) => (e.currentTarget.style.borderColor = '#6366f1')}
      onMouseLeave={(e) => (e.currentTarget.style.borderColor = '#2a2d3a')}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <span style={{ fontWeight: 700, fontSize: '1.1rem' }}>{ticker}</span>
          {isDone ? (
            <span style={{
              fontSize: '1rem', fontWeight: 600,
              color: color.text,
            }}>
              {score >= 0 ? '+' : ''}{score.toFixed(4)}
            </span>
          ) : (
            <PipelineProgress step={pipelineStep} />
          )}
        </div>
        {isDone && (
          <span style={{
            padding: '0.3rem 0.75rem', borderRadius: '4px',
            fontSize: '0.75rem', fontWeight: 700,
            background: color.bg, color: color.text,
          }}>
            {recommendation}
          </span>
        )}
      </div>

      {isDone && (
        <div style={{ fontSize: '0.8rem', color: '#71717a', marginTop: '0.5rem' }}>
          {articlesProcessed} articles processed
        </div>
      )}

      {expanded && topArticles.length > 0 && (
        <div style={{ marginTop: '1rem', borderTop: '1px solid #2a2d3a', paddingTop: '1rem' }}>
          <ArticleList articles={topArticles} />
        </div>
      )}
    </div>
  )
}
