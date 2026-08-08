/** SocialAPI — 社交平台集成接口 */
import type { AetherSDK } from './index'

export interface SocialMessage {
  id: string
  platform: 'feishu' | 'discord' | 'wechat'
  content: string
  sender: string
  timestamp: number
  channelId?: string
}

export interface SocialChannel {
  id: string
  platform: string
  name: string
  unread: number
  lastMessage?: string
}

export class SocialAPI {
  constructor(private sdk: AetherSDK) {}

  async listChannels(): Promise<SocialChannel[]> {
    return this.sdk.request('social.channels', {})
  }

  async getMessages(channelId: string, limit = 50): Promise<SocialMessage[]> {
    return this.sdk.request('social.messages', { channelId, limit })
  }

  async send(channelId: string, content: string): Promise<boolean> {
    return this.sdk.request('social.send', { channelId, content })
  }

  onMessage(callback: (msg: SocialMessage) => void): () => void {
    return this.sdk.on('social.message', (msg) => callback(msg.payload as SocialMessage))
  }
}
