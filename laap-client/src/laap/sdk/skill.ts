/** SkillAPI — 技能系统操作接口 */
import type { AetherSDK } from './index'

export interface SkillDefinition {
  name: string
  description: string
  category: string
  enabled: boolean
  version?: string
  tags?: string[]
  fileCount?: number
}

export class SkillAPI {
  constructor(private sdk: AetherSDK) {}

  async list(): Promise<SkillDefinition[]> {
    return this.sdk.request('skill.list', {})
  }

  async get(name: string): Promise<SkillDefinition | null> {
    return this.sdk.request('skill.get', { name })
  }

  async toggle(name: string, enabled: boolean): Promise<boolean> {
    return this.sdk.request('skill.toggle', { name, enabled })
  }

  async readContent(name: string): Promise<string | null> {
    return this.sdk.request('skill.read', { name })
  }

  onUpdate(callback: (skills: SkillDefinition[]) => void): () => void {
    return this.sdk.on('skill.updated', (msg) => callback(msg.payload as SkillDefinition[]))
  }
}
