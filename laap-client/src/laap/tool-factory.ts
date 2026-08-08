/**
 * Tool Factory — 从描述动态生成工具调用 schema
 *
 * Adapted from BaiLongma's src/tooling/tool-factory.js
 *
 * Given a natural-language capability description, ToolFactory produces an
 * OpenAI-compatible function/tool schema. It can also maintain a hot-registry
 * of generated tools so the agent can discover and call them at runtime.
 */

export interface ToolParameter {
  name: string
  type: 'string' | 'number' | 'boolean' | 'array' | 'object'
  description: string
  required?: boolean
  enum?: string[]
  items?: { type: string }
}

export interface ToolSchema {
  type: 'function'
  function: {
    name: string
    description: string
    parameters: {
      type: 'object'
      properties: Record<string, unknown>
      required: string[]
    }
  }
}

export interface GeneratedTool {
  id: string
  name: string
  description: string
  category: string
  parameters: ToolParameter[]
  schema: ToolSchema
  handler?: (args: Record<string, unknown>) => unknown | Promise<unknown>
  enabled: boolean
  createdAt: number
}

export type ToolRegistryChange =
  | { type: 'registered'; tool: GeneratedTool }
  | { type: 'unregistered'; toolId: string }
  | { type: 'toggled'; toolId: string; enabled: boolean }

export type ToolRegistryListener = (event: ToolRegistryChange) => void

function sanitizeName(name: string): string {
  return name
    .toLowerCase()
    .replace(/[^a-z0-9_\s-]/g, '')
    .replace(/[\s-]+/g, '_')
    .slice(0, 64)
}

function inferParameters(description: string): ToolParameter[] {
  const params: ToolParameter[] = []
  const mentions = description.match(/\b([a-zA-Z_][a-zA-Z0-9_\s]*?)\b/g) || []
  const seen = new Set<string>()

  for (const mention of mentions) {
    const name = mention.trim().toLowerCase().replace(/\s+/g, '_')
    if (!name || name.length < 3) continue
    if (seen.has(name)) continue
    if (['the', 'and', 'for', 'with', 'from', 'this', 'that', 'use', 'using', 'call', 'tool'].includes(name)) continue
    seen.add(name)

    const isNumber = /\b(count|number|amount|limit|offset|size|page|age|year|id)\b/i.test(name)
    const isBoolean = /\b(enable|disable|active|visible|force|strict|async)\b/i.test(name)
    const isArray = /\b(list|items|tags|ids|names|urls|paths)\b/i.test(name)

    let type: ToolParameter['type'] = 'string'
    if (isArray) type = 'array'
    else if (isBoolean) type = 'boolean'
    else if (isNumber) type = 'number'

    params.push({
      name,
      type,
      description: `The ${name.replace(/_/g, ' ')} for this tool call.`,
      required: false,
    })
  }

  if (params.length === 0) {
    params.push({
      name: 'query',
      type: 'string',
      description: 'The primary input for this tool call.',
      required: true,
    })
  }

  return params
}

function buildSchema(name: string, description: string, parameters: ToolParameter[]): ToolSchema {
  const properties: Record<string, unknown> = {}
  const required: string[] = []

  for (const param of parameters) {
    const prop: Record<string, unknown> = { type: param.type, description: param.description }
    if (param.enum) prop.enum = param.enum
    if (param.type === 'array' && param.items) prop.items = param.items
    properties[param.name] = prop
    if (param.required) required.push(param.name)
  }

  return {
    type: 'function',
    function: {
      name,
      description,
      parameters: { type: 'object', properties, required },
    },
  }
}

export class ToolFactory {
  private registry = new Map<string, GeneratedTool>()
  private listeners = new Set<ToolRegistryListener>()
  private nextId = 1

  /**
   * Generate a tool from a natural-language capability description.
   */
  generate(description: string, category = 'generated'): GeneratedTool {
    const name = sanitizeName(description.split(/[.，。]/)[0])
    const parameters = inferParameters(description)
    const schema = buildSchema(name, description, parameters)

    const tool: GeneratedTool = {
      id: `tool-${this.nextId++}`,
      name,
      description,
      category,
      parameters,
      schema,
      enabled: true,
      createdAt: Date.now(),
    }

    this.registry.set(tool.id, tool)
    this.emit({ type: 'registered', tool })
    return tool
  }

  /**
   * Register a fully-specified tool (e.g. from a JSON definition).
   */
  register(tool: Omit<GeneratedTool, 'id' | 'createdAt'> & { id?: string }): GeneratedTool {
    const full: GeneratedTool = {
      ...tool,
      id: tool.id ?? `tool-${this.nextId++}`,
      createdAt: Date.now(),
    }
    this.registry.set(full.id, full)
    this.emit({ type: 'registered', tool: full })
    return full
  }

  /**
   * Unregister a tool by id.
   */
  unregister(toolId: string): boolean {
    const existed = this.registry.delete(toolId)
    if (existed) this.emit({ type: 'unregistered', toolId })
    return existed
  }

  /**
   * Toggle enablement.
   */
  toggle(toolId: string, enabled: boolean): boolean {
    const tool = this.registry.get(toolId)
    if (!tool) return false
    tool.enabled = enabled
    this.emit({ type: 'toggled', toolId, enabled })
    return true
  }

  /**
   * Get a registered tool.
   */
  get(toolId: string): GeneratedTool | undefined {
    return this.registry.get(toolId)
  }

  /**
   * List all registered tools.
   */
  list(): GeneratedTool[] {
    return [...this.registry.values()]
  }

  /**
   * List enabled tools only.
   */
  listEnabled(): GeneratedTool[] {
    return this.list().filter((t) => t.enabled)
  }

  /**
   * Get OpenAI-compatible function schemas for enabled tools.
   */
  getSchemas(): ToolSchema[] {
    return this.listEnabled().map((t) => t.schema)
  }

  /**
   * Attach a handler to a tool.
   */
  setHandler(toolId: string, handler: GeneratedTool['handler']): boolean {
    const tool = this.registry.get(toolId)
    if (!tool) return false
    tool.handler = handler
    return true
  }

  /**
   * Execute a tool by name with given arguments.
   */
  async execute(name: string, args: Record<string, unknown>): Promise<unknown> {
    const tool = this.list().find((t) => t.name === name)
    if (!tool) throw new Error(`Tool not found: ${name}`)
    if (!tool.enabled) throw new Error(`Tool disabled: ${name}`)
    if (!tool.handler) throw new Error(`Tool has no handler: ${name}`)
    return tool.handler(args)
  }

  onChange(listener: ToolRegistryListener): () => void {
    this.listeners.add(listener)
    return () => this.listeners.delete(listener)
  }

  private emit(event: ToolRegistryChange): void {
    for (const listener of this.listeners) {
      listener(event)
    }
  }
}

export const toolFactory = new ToolFactory()
