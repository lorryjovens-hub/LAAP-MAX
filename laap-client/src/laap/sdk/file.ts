/** FileAPI — 文件系统操作接口 */
import type { AetherSDK } from './index'

export interface FileEntry {
  name: string
  path: string
  type: 'file' | 'dir'
  size?: number
  modifiedAt?: number
  children?: FileEntry[]
}

export class FileAPI {
  constructor(private sdk: AetherSDK) {}

  async list(dir: string): Promise<FileEntry[]> {
    return this.sdk.request('file.list', { dir })
  }

  async read(path: string): Promise<string | null> {
    return this.sdk.request('file.read', { path })
  }

  async write(path: string, content: string): Promise<boolean> {
    return this.sdk.request('file.write', { path, content })
  }

  async delete(path: string): Promise<boolean> {
    return this.sdk.request('file.delete', { path })
  }

  async search(pattern: string, dir?: string): Promise<FileEntry[]> {
    return this.sdk.request('file.search', { pattern, dir })
  }
}
