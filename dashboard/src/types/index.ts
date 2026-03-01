export interface TickerInfo {
  ticker: string
  company_name: string
  sector: string
  descriptor: string
}

export interface ArticleSentiment {
  headline: string
  label: string
  confidence: number
  sentiment_score: number
  source: string
}

export interface TickerScore {
  ticker: string
  score: number
  recommendation: string
  timestamp: string
  articles_processed: number
  articles_total: number
  pipeline_step: string
  top_articles: ArticleSentiment[]
}

export interface ScorePoint {
  timestamp: string
  score: number
}

export interface WSScoreUpdate {
  type: 'score_update'
  data: {
    ticker: string
    score: number
    recommendation: string
    timestamp: string
    articles_processed: number
    articles_total: number
    top_articles: ArticleSentiment[]
  }
}

export interface WSPipelineProgress {
  type: 'pipeline_progress'
  data: {
    ticker: string
    step: string
  }
}

export interface WSInitialState {
  type: 'initial_state'
  data: {
    monitored_tickers: string[]
    data_source: string
    models_loaded: boolean
    scores: Record<string, {
      score: number
      recommendation: string
      pipeline_step: string
      timestamp: string
    }>
  }
}

export interface WSEngineStatus {
  type: 'engine_status'
  data: {
    monitoring_active: boolean
    data_source: string
    monitored_tickers: string[]
    models_loaded: boolean
  }
}

export type WSMessage = WSScoreUpdate | WSPipelineProgress | WSInitialState | WSEngineStatus
