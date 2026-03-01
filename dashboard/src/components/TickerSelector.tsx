import { useState } from 'react'
import type { TickerInfo } from '../types'

interface TickerSelectorProps {
  tickers: TickerInfo[]
  monitoredTickers: string[]
  onStart: (tickers: string[]) => void
  onStop: (ticker: string) => void
}

export function TickerSelector({ tickers, monitoredTickers, onStart, onStop }: TickerSelectorProps) {
  const [search, setSearch] = useState('')
  const [selected, setSelected] = useState<string[]>([])

  const filtered = tickers.filter((t) => {
    const q = search.toLowerCase()
    return (
      !monitoredTickers.includes(t.ticker) &&
      (t.ticker.toLowerCase().includes(q) ||
        t.company_name.toLowerCase().includes(q) ||
        t.sector.toLowerCase().includes(q))
    )
  }).slice(0, 8)

  const toggleSelect = (ticker: string) => {
    setSelected((prev) =>
      prev.includes(ticker) ? prev.filter((t) => t !== ticker) : [...prev, ticker]
    )
  }

  const handleStart = () => {
    if (selected.length > 0) {
      onStart(selected)
      setSelected([])
      setSearch('')
    }
  }

  return (
    <div style={{ marginBottom: '1.5rem' }}>
      {/* Monitored ticker pills */}
      {monitoredTickers.length > 0 && (
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', marginBottom: '1rem' }}>
          {monitoredTickers.map((t) => (
            <span
              key={t}
              style={{
                display: 'flex', alignItems: 'center', gap: '0.4rem',
                padding: '0.35rem 0.75rem', background: '#1a1d27',
                border: '1px solid #2a2d3a', borderRadius: '4px',
                fontSize: '0.8rem', color: '#e4e4e7',
              }}
            >
              {t}
              <button
                onClick={() => onStop(t)}
                style={{
                  background: 'none', border: 'none', color: '#71717a',
                  cursor: 'pointer', fontSize: '1rem', lineHeight: 1,
                  padding: 0, fontFamily: 'inherit',
                }}
              >
                x
              </button>
            </span>
          ))}
        </div>
      )}

      {/* Search + add */}
      <div style={{ display: 'flex', gap: '0.75rem', marginBottom: '0.5rem' }}>
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search tickers (e.g. NVDA, Apple, AI Chips)..."
          style={{
            flex: 1, padding: '0.65rem 1rem', background: '#1a1d27',
            border: '1px solid #2a2d3a', borderRadius: '6px',
            color: '#e4e4e7', fontFamily: 'inherit', fontSize: '0.85rem',
            outline: 'none',
          }}
        />
        <button
          onClick={handleStart}
          disabled={selected.length === 0}
          style={{
            padding: '0.65rem 1.25rem', background: selected.length > 0 ? '#6366f1' : '#2a2d3a',
            color: '#fff', border: 'none', borderRadius: '6px',
            cursor: selected.length > 0 ? 'pointer' : 'not-allowed',
            fontFamily: 'inherit', fontSize: '0.85rem', fontWeight: 600,
            opacity: selected.length > 0 ? 1 : 0.5,
          }}
        >
          Monitor ({selected.length})
        </button>
      </div>

      {/* Dropdown results */}
      {search && (
        <div style={{
          background: '#1a1d27', border: '1px solid #2a2d3a', borderRadius: '6px',
          maxHeight: '240px', overflow: 'auto',
        }}>
          {filtered.length === 0 ? (
            <div style={{ padding: '0.75rem 1rem', color: '#71717a', fontSize: '0.85rem' }}>
              No matches
            </div>
          ) : (
            filtered.map((t) => (
              <div
                key={t.ticker}
                onClick={() => toggleSelect(t.ticker)}
                style={{
                  display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                  padding: '0.6rem 1rem', cursor: 'pointer',
                  background: selected.includes(t.ticker) ? 'rgba(99,102,241,0.15)' : 'transparent',
                  borderBottom: '1px solid #2a2d3a',
                  transition: 'background 0.15s',
                }}
              >
                <div>
                  <span style={{ fontWeight: 600, fontSize: '0.85rem', color: '#e4e4e7' }}>{t.ticker}</span>
                  <span style={{ color: '#71717a', fontSize: '0.8rem', marginLeft: '0.75rem' }}>{t.company_name}</span>
                </div>
                <span style={{ fontSize: '0.75rem', color: '#71717a' }}>{t.sector}</span>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  )
}
