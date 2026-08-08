import { getLocalConfig, setLocalConfig } from '@/lib/db';

export const MCP_SERVERS_KEY = 'mcp_servers';

export interface McpToolSchema {
  name: string;
  description?: string;
  inputSchema?: Record<string, unknown>;
}

export interface McpServer {
  id: string;
  name: string;
  transport: 'stdio' | 'sse' | 'http';
  command?: string;
  args?: string[];
  url?: string;
  headers?: Record<string, string>;
  enabled: boolean;
  tools: McpToolSchema[];
  createdAt: string;
}

export interface McpConfigFile {
  mcpServers?: Record<string, {
    command?: string;
    args?: string[];
    url?: string;
    headers?: Record<string, string>;
    transport?: 'stdio' | 'sse' | 'http';
    disabled?: boolean;
  }>;
}

export async function listMcpServers(): Promise<McpServer[]> {
  const servers = await getLocalConfig<McpServer[]>(MCP_SERVERS_KEY);
  return servers ?? [];
}

export async function saveMcpServers(servers: McpServer[]): Promise<void> {
  await setLocalConfig(MCP_SERVERS_KEY, servers);
}

export async function addMcpServer(server: Omit<McpServer, 'id' | 'createdAt'>): Promise<McpServer> {
  const servers = await listMcpServers();
  const created: McpServer = {
    ...server,
    id: crypto.randomUUID(),
    createdAt: new Date().toISOString(),
  };
  await saveMcpServers([...servers, created]);
  return created;
}

export async function updateMcpServer(id: string, patch: Partial<McpServer>): Promise<void> {
  const servers = await listMcpServers();
  const next = servers.map((s) => (s.id === id ? { ...s, ...patch } : s));
  await saveMcpServers(next);
}

export async function removeMcpServer(id: string): Promise<void> {
  const servers = await listMcpServers();
  await saveMcpServers(servers.filter((s) => s.id !== id));
}

export function parseMcpConfigFile(text: string): McpServer[] {
  let data: McpConfigFile;
  try {
    data = JSON.parse(text) as McpConfigFile;
  } catch {
    throw new Error('MCP 配置文件不是有效的 JSON');
  }

  if (!data.mcpServers || typeof data.mcpServers !== 'object') {
    throw new Error('MCP 配置文件缺少 mcpServers 字段');
  }

  const now = new Date().toISOString();
  const servers: McpServer[] = [];

  for (const [name, cfg] of Object.entries(data.mcpServers)) {
    const transport = cfg.transport || (cfg.url ? 'sse' : 'stdio');
    if (transport === 'stdio' && !cfg.command) {
      throw new Error(`MCP 服务器 "${name}" 缺少 command 字段`);
    }
    if ((transport === 'sse' || transport === 'http') && !cfg.url) {
      throw new Error(`MCP 服务器 "${name}" 缺少 url 字段`);
    }

    servers.push({
      id: crypto.randomUUID(),
      name,
      transport,
      command: cfg.command,
      args: cfg.args,
      url: cfg.url,
      headers: cfg.headers,
      enabled: !cfg.disabled,
      tools: [],
      createdAt: now,
    });
  }

  return servers;
}

export async function callMcpSseTool(
  server: McpServer,
  toolName: string,
  args: Record<string, unknown>
): Promise<string> {
  if (!server.url) {
    throw new Error('SSE MCP 服务器缺少 URL');
  }

  const url = new URL(toolName, server.url).toString();
  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...server.headers,
    },
    body: JSON.stringify(args),
  });

  if (!response.ok) {
    throw new Error(`MCP 工具调用失败 (${response.status})`);
  }

  const data = (await response.json()) as { result?: unknown; error?: { message?: string } };
  if (data.error) {
    throw new Error(data.error.message || 'MCP 工具返回错误');
  }
  return typeof data.result === 'string' ? data.result : JSON.stringify(data.result ?? '');
}
