import type { Tool } from '@/lib/localLlm';

export interface ToolDefinition extends Tool {
  readonly?: boolean;
  agentLevel?: boolean;
  toolset?: string;
}

export interface Toolset {
  name: string;
  description: string;
  tools: ToolDefinition[];
  enabled: boolean;
}

export class ToolRegistry {
  private tools = new Map<string, ToolDefinition>();
  private toolsets = new Map<string, Toolset>();

  register(tool: ToolDefinition): void {
    if (this.tools.has(tool.name)) {
      console.warn(`Tool "${tool.name}" is already registered and will be overwritten.`);
    }
    this.tools.set(tool.name, tool);
  }

  registerToolset(toolset: Toolset): void {
    this.toolsets.set(toolset.name, toolset);
    for (const tool of toolset.tools) {
      this.register({
        ...tool,
        toolset: toolset.name,
      });
    }
  }

  get(name: string): ToolDefinition | undefined {
    return this.tools.get(name);
  }

  list(): ToolDefinition[] {
    return Array.from(this.tools.values()).filter((tool) => {
      const toolsetName = tool.toolset;
      if (!toolsetName) return true;
      const toolset = this.toolsets.get(toolsetName);
      return toolset ? toolset.enabled : true;
    });
  }

  listAll(): ToolDefinition[] {
    return Array.from(this.tools.values());
  }

  setToolsetEnabled(name: string, enabled: boolean): void {
    const toolset = this.toolsets.get(name);
    if (toolset) {
      toolset.enabled = enabled;
    }
  }

  isToolsetEnabled(name: string): boolean {
    const toolset = this.toolsets.get(name);
    return toolset ? toolset.enabled : false;
  }

  normalizeToolName(name: string): string {
    return sanitizeToolName(name);
  }
}

export const toolRegistry = new ToolRegistry();

export function sanitizeToolName(name: string): string {
  return name.replace(/[^a-zA-Z0-9_-]/g, '_').slice(0, 32);
}
