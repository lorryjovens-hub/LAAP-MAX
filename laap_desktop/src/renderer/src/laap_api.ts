const WS_URL = 'ws://localhost:8766'
const HTTP_URL = 'http://localhost:8081'

export type Message = {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: number
}

export type ChatCallbacks = {
  onToken?: (text: string) => void
  onResponse?: (text: string) => void
  onToolCall?: (name: string, args: string) => void
  onToolResult?: (name: string, result: string) => void
  onEmotion?: (name: string, intensity: number) => void
  onVitals?: (energy: number, focus: number, mood: number) => void
  onError?: (err: string) => void
  onConnected?: () => void
  onDisconnected?: () => void
}

let ws: WebSocket | null = null
let currentCallbacks: ChatCallbacks | null = null
let reconnectTimer: ReturnType<typeof setTimeout> | null = null
let reconnectAttempts = 0
const MAX_RECONNECT_ATTEMPTS = 5

function connectWS(cb: ChatCallbacks): void {
  currentCallbacks = cb

  if (ws?.readyState === WebSocket.OPEN) return
  if (ws?.readyState === WebSocket.CONNECTING) return

  try {
    ws = new WebSocket(WS_URL)

    ws.onopen = () => {
      reconnectAttempts = 0
      currentCallbacks?.onConnected?.()
      ws?.send(JSON.stringify({ type: 'status' }))
    }

    ws.onmessage = (e: MessageEvent) => {
      try {
        const d = JSON.parse(e.data as string)
        switch (d.type) {
          case 'token':
            currentCallbacks?.onToken?.(d.text)
            break
          case 'response':
            currentCallbacks?.onResponse?.(d.text)
            break
          case 'tool_call':
            currentCallbacks?.onToolCall?.(d.name, d.args || '')
            break
          case 'tool_result':
            currentCallbacks?.onToolResult?.(d.name, d.result || '')
            break
          case 'emotion':
            currentCallbacks?.onEmotion?.(d.name, d.intensity)
            break
          case 'vitals':
            currentCallbacks?.onVitals?.(d.energy, d.focus, d.mood)
            break
          case 'error':
            currentCallbacks?.onError?.(d.message || 'Unknown error')
            break
          case 'status':
            // Connected and ready
            break
        }
      } catch {
        // Ignore parse errors
      }
    }

    ws.onerror = () => {
      currentCallbacks?.onError?.('WebSocket connection error')
    }

    ws.onclose = () => {
      ws = null
      currentCallbacks?.onDisconnected?.()
      // Auto reconnect
      if (reconnectAttempts < MAX_RECONNECT_ATTEMPTS && currentCallbacks) {
        reconnectAttempts++
        reconnectTimer = setTimeout(() => connectWS(currentCallbacks!), 2000 * reconnectAttempts)
      }
    }
  } catch {
    currentCallbacks?.onError?.('Failed to create WebSocket connection')
  }
}

function disconnectWS(): void {
  if (reconnectTimer) clearTimeout(reconnectTimer)
  reconnectTimer = null
  reconnectAttempts = MAX_RECONNECT_ATTEMPTS
  if (ws) {
    ws.close()
    ws = null
  }
  currentCallbacks = null
}

// ── REST API ──

async function apiGet<T>(path: string): Promise<T | null> {
  try {
    const res = await fetch(`${HTTP_URL}${path}`, {
      headers: { 'Accept': 'application/json' },
    })
    if (!res.ok) return null
    return await res.json()
  } catch {
    return null
  }
}

async function apiPost<T>(path: string, body: unknown): Promise<T | null> {
  try {
    const res = await fetch(`${HTTP_URL}${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
    if (!res.ok) return null
    return await res.json()
  } catch {
    return null
  }
}

// ── Exported API ──

export const laap = {
  chat: (text: string, domain = 'general', use_psi = false, cb: ChatCallbacks): void => {
    connectWS(cb)
    const sendMsg = () => {
      if (ws?.readyState === WebSocket.OPEN) {
        ws!.send(JSON.stringify({ type: 'chat', text, domain, use_psi }))
      }
    }
    if (ws?.readyState === WebSocket.OPEN) {
      sendMsg()
    } else {
      // Delay until connected
      const check = setInterval(() => {
        if (ws?.readyState === WebSocket.OPEN) {
          clearInterval(check)
          sendMsg()
        }
      }, 100)
      setTimeout(() => clearInterval(check), 5000)
    }
  },

  tts: (text: string): void => {
    ws?.send(JSON.stringify({ type: 'tts', text: text.slice(0, 500) }))
  },

  // REST API methods
  getAgentState: () => apiGet<Record<string, unknown>>('/api/agent/state'),
  getCharacter: (name: string) => apiGet<Record<string, unknown>>(`/api/character/load?name=${encodeURIComponent(name)}`),
  searchCharacter: (q: string) => apiGet<Record<string, unknown>[]>(`/api/character/search?q=${encodeURIComponent(q)}`),
  saveMemory: (character: string, content: string) => apiPost('/api/character/memory', { character, content }),
  getHealth: () => apiGet<Record<string, unknown>>('/api/health'),

  disconnect: (): void => {
    disconnectWS()
  },
}
