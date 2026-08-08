/**
 * AetherSDK — LAAP 前端 TypeScript SDK
 * ========================================
 * 
 * 在 CognitiveBus WebSocket 之上提供 typed API 层。
 * 每个 domain 对应一个 API 模块，统一通过 AetherSDK 访问。
 *
 * 用法:
 *   const sdk = new AetherSDK(bus)
 *   const memories = await sdk.memory.search("论文")
 *   const tools = await sdk.tool.list()
 *   sdk.replay.onUpdate((report) => setReport(report))
 */

import type { CognitiveBusClient } from '../bus'
import type { AetherMessage } from '../types'
import { MemoryAPI } from './memory'
import { ToolAPI } from './tool'
import { AgentAPI } from './agent'
import { SkillAPI } from './skill'
import { FileAPI } from './file'
import { ReplayAPI } from './replay'
import { CostAPI } from './cost'
import { SocialAPI } from './social'

export type { MemoryAPI, MemoryEntry, MemorySearchResult } from './memory'
export type { ToolAPI, ToolDefinition, ToolCallRequest } from './tool'
export type { AgentAPI, AgentInfo, AgentMetrics } from './agent'
export type { SkillAPI, SkillDefinition } from './skill'
export type { FileAPI, FileEntry } from './file'
export type { ReplayAPI, ReplayReport, BenchmarkResult } from './replay'
export type { CostAPI, CostSummary } from './cost'
export type { SocialAPI, SocialMessage } from './social'

export interface AetherSDKOptions {
  /** API 请求超时 (ms) */
  requestTimeout?: number
  /** 是否启用控制台调试日志 */
  debug?: boolean
}

/**
 * AetherSDK 主入口
 */
export class AetherSDK {
  readonly memory: MemoryAPI
  readonly tool: ToolAPI
  readonly agent: AgentAPI
  readonly skill: SkillAPI
  readonly file: FileAPI
  readonly replay: ReplayAPI
  readonly cost: CostAPI
  readonly social: SocialAPI

  readonly bus: CognitiveBusClient
  readonly options: Required<AetherSDKOptions>

  constructor(bus: CognitiveBusClient, options: AetherSDKOptions = {}) {
    this.bus = bus
    this.options = {
      requestTimeout: options.requestTimeout ?? 10000,
      debug: options.debug ?? false,
    }
    this.memory = new MemoryAPI(this)
    this.tool = new ToolAPI(this)
    this.agent = new AgentAPI(this)
    this.skill = new SkillAPI(this)
    this.file = new FileAPI(this)
    this.replay = new ReplayAPI(this)
    this.cost = new CostAPI(this)
    this.social = new SocialAPI(this)
  }

  /**
   * 通过 CognitiveBus 发送请求并等待响应
   * 适用于 request/response 模式
   */
  request<T = unknown>(topic: string, payload: unknown, timeout?: number): Promise<T> {
    return new Promise((resolve, reject) => {
      const requestId = `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`
      const timer = setTimeout(() => {
        unsub()
        reject(new Error(`AetherSDK request timed out: ${topic}`))
      }, timeout ?? this.options.requestTimeout)

      const unsub = this.bus.subscribe(`response.${requestId}`, (msg) => {
        clearTimeout(timer)
        unsub()
        resolve(msg.payload as T)
      })

      this.bus.sendAetherMessage({
        id: requestId,
        type: 'request',
        topic,
        payload,
        timestamp: Date.now(),
        sender: 'laap-client',
      })

      if (this.options.debug) {
        console.log(`[AetherSDK] -> ${topic}`, payload)
      }
    })
  }

  /**
   * 发送请求但不等待响应（fire-and-forget）
   */
  send(topic: string, payload: unknown): void {
    this.bus.sendAetherMessage({
      id: `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`,
      type: 'command',
      topic,
      payload,
      timestamp: Date.now(),
      sender: 'laap-client',
    })
    if (this.options.debug) {
      console.log(`[AetherSDK] -> ${topic} (fire-and-forget)`)
    }
  }

  /**
   * 订阅 topic 并返回取消函数
   */
  on(topic: string, callback: (msg: AetherMessage) => void): () => void {
    return this.bus.subscribe(topic, callback)
  }
}

export default AetherSDK
