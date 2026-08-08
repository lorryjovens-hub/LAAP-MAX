/**
 * SceneClient — WebSocket client with gap detection
 *
 * Adapted from BaiLongma's src/ui/scene-shell/client.js
 *
 * Connects to the scene WebSocket, manages revision tracking,
 * detects gaps, and triggers resync.
 */

import type { CoreMessage, ShellMessage, Scene, ScenePatch } from './types'
import { SCENE_PROTOCOL_VERSION, SCENE_CAPABILITIES } from './types'

export type SceneClientStatus = 'disconnected' | 'connecting' | 'connected' | 'error'

export interface SceneClientCallbacks {
  onScene: (scene: Scene) => void
  onPatch: (patch: ScenePatch) => void
  onStatus: (status: SceneClientStatus) => void
  onError: (error: string) => void
}

export class SceneClient {
  private ws: WebSocket | null = null
  private url: string
  private callbacks: SceneClientCallbacks
  private currentRevision = 0
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null
  private reconnectAttempts = 0
  private maxReconnectAttempts = 10
  private baseDelay = 1000
  private destroyed = false

  constructor(url: string, callbacks: SceneClientCallbacks) {
    this.url = url
    this.callbacks = callbacks
  }

  /** Connect to the scene WebSocket */
  connect(): void {
    if (this.destroyed || this.ws?.readyState === WebSocket.OPEN) return
    this.callbacks.onStatus('connecting')

    try {
      this.ws = new WebSocket(this.url)
      this.ws.onopen = () => this.handleOpen()
      this.ws.onclose = () => this.handleClose()
      this.ws.onerror = () => this.handleError()
      this.ws.onmessage = (event) => this.handleMessage(event)
    } catch (err) {
      this.callbacks.onStatus('error')
      this.callbacks.onError(`WebSocket connection failed: ${err}`)
      this.scheduleReconnect()
    }
  }

  /** Disconnect */
  disconnect(): void {
    this.destroyed = true
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }
    this.ws?.close()
    this.ws = null
    this.callbacks.onStatus('disconnected')
  }

  /** Send an intent to the core */
  sendIntent(surface: string, name: string, data: unknown): void {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) return

    const msg: ShellMessage = {
      type: 'intent',
      surface,
      name,
      data,
      timestamp: Date.now(),
    }
    this.ws.send(JSON.stringify(msg))
  }

  /** Request scene resync */
  requestResync(reason: 'gap' | 'init' | 'error'): void {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) return

    const msg: ShellMessage = {
      type: 'resync',
      reason,
    }
    this.ws.send(JSON.stringify(msg))
  }

  private handleOpen(): void {
    this.reconnectAttempts = 0
    this.callbacks.onStatus('connected')

    // Send handshake
    const hello: ShellMessage = {
      type: 'hello',
      version: SCENE_PROTOCOL_VERSION,
      shell: 'laap-client',
      capabilities: [...SCENE_CAPABILITIES],
    }
    this.ws!.send(JSON.stringify(hello))
  }

  private handleClose(): void {
    this.ws = null
    this.callbacks.onStatus('disconnected')
    if (!this.destroyed) {
      this.scheduleReconnect()
    }
  }

  private handleError(): void {
    this.callbacks.onStatus('error')
    this.callbacks.onError('WebSocket error')
  }

  private handleMessage(event: MessageEvent): void {
    try {
      const msg: CoreMessage = JSON.parse(event.data)

      switch (msg.type) {
        case 'welcome':
          this.currentRevision = msg.revision
          break

        case 'scene':
          this.currentRevision = msg.revision
          this.callbacks.onScene({
            revision: msg.revision,
            surfaces: msg.surfaces,
          })
          break

        case 'scene.patch':
          // Gap detection
          if (msg.base !== this.currentRevision) {
            this.callbacks.onError(
              `Revision gap: expected ${msg.base}, have ${this.currentRevision}. Requesting resync.`,
            )
            this.requestResync('gap')
            return
          }
          this.currentRevision = msg.revision
          this.callbacks.onPatch(msg)
          break
      }
    } catch (err) {
      this.callbacks.onError(`Failed to parse scene message: ${err}`)
    }
  }

  private scheduleReconnect(): void {
    if (this.destroyed) return
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      this.callbacks.onError('Max reconnection attempts reached')
      return
    }

    const delay = this.baseDelay * Math.pow(2, this.reconnectAttempts) + Math.random() * 1000
    this.reconnectAttempts++

    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null
      this.connect()
    }, delay)
  }
}
