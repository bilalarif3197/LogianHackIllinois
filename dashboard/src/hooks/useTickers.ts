import { useEffect, useState } from 'react'
import type { TickerInfo } from '../types'

export function useTickers() {
  const [tickers, setTickers] = useState<TickerInfo[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch('/api/tickers')
      .then((r) => r.json())
      .then((data: TickerInfo[]) => {
        setTickers(data)
        setLoading(false)
      })
      .catch(() => setLoading(false))
  }, [])

  return { tickers, loading }
}
