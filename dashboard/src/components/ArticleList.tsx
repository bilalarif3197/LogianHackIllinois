import type { ArticleSentiment } from '../types'

interface ArticleListProps {
  articles: ArticleSentiment[]
}

export function ArticleList({ articles }: ArticleListProps) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
      {articles.map((a, i) => {
        const labelColor =
          a.label === 'positive' ? '#22c55e' :
          a.label === 'negative' ? '#ef4444' : '#eab308'

        return (
          <div key={i} style={{ fontSize: '0.8rem' }}>
            <div style={{ fontWeight: 600, color: '#e4e4e7', marginBottom: '0.25rem' }}>
              {i + 1}. {a.headline}
            </div>
            <div style={{ color: '#71717a', display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
              <span>
                Sentiment: <span style={{ color: labelColor, fontWeight: 600 }}>{a.label.toUpperCase()}</span>
              </span>
              <span>Confidence: {(a.confidence * 100).toFixed(1)}%</span>
              <span>Score: {a.sentiment_score >= 0 ? '+' : ''}{a.sentiment_score.toFixed(4)}</span>
              {a.source && <span>Source: {a.source}</span>}
            </div>
          </div>
        )
      })}
    </div>
  )
}
