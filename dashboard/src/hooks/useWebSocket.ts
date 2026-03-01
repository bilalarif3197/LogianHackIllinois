import { useEffect, useRef, useState, useCallback } from 'react'
import type { WSMessage } from '../types'

const RECONNECT_BASE_MS = 1000
const RECONNECT_MAX_MS = 30000

export function useWebSocket(
  url: string,
  onMessage: (msg: WSMessage) => void,
) {
  const [connected, setConnected] = useState(false)
  const wsRef = useRef<WebSocket | null>(null)
  const retriesRef = useRef(0)
  const onMessageRef = useRef(onMessage)
  onMessageRef.current = onMessage

  const connect = useCallback(() => {
    try {
      const ws = new WebSocket(url)
      wsRef.current = ws

      ws.onopen = () => {
        setConnected(true)
        retriesRef.current = 0
      }

      ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data) as WSMessage
          onMessageRef.current(msg)
        } catch {
          // ignore malformed messages
        }
      }

      ws.onclose = () => {
        setConnected(false)
        wsRef.current = null
        // Reconnect with exponential backoff
        const delay = Math.min(
          RECONNECT_BASE_MS * 2 ** retriesRef.current,
          RECONNECT_MAX_MS,
        )
        retriesRef.current++
        setTimeout(connect, delay)
      }

      ws.onerror = () => {
        ws.close()
      }
    } catch {
      // retry on next cycle
    }
  }, [url])

  useEffect(() => {
    connect()
    return () => {
      if (wsRef.current) {
        wsRef.current.onclose = null // prevent reconnect on cleanup
        wsRef.current.close()
      }
    }
  }, [connect])

  return { connected }
}
