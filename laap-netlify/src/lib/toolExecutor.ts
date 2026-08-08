import { ToolRegistry } from '@/lib/toolRegistry';
import type { HistoryMessage, ToolCall } from '@/lib/localLlm';

// Minimal local mirror of StreamEvent to avoid a circular import with chat.ts.
export interface StreamEvent {
  type: 'reasoning_step' | 'tool_result' | 'response' | 'done';
  data: Record<string, unknown>;
}

export interface ToolCallIntent {
  id: string;
  name: string;
  arguments: string; // raw JSON string
}

export interface ToolExecutionRecord {
  id: string;
  name: string;
  args: Record<string, unknown>;
  result: string;
}

export interface ToolExecutorOptions {
  maxRounds?: number;
  timeoutMs?: number;
  maxResultLength?: number;
  onToolResult?: (record: ToolExecutionRecord) => void;
  onEvent?: (event: StreamEvent) => void; // 向前端发送 tool_result 事件
}

export function repairJson(raw: string): string {
  let s = raw.trim();
  // Remove trailing commas before closing braces or brackets.
  s = s.replace(/,\s*([}\]])/g, '$1');

  const openBraces = (s.match(/\{/g) || []).length;
  const closeBraces = (s.match(/\}/g) || []).length;
  s += '}'.repeat(Math.max(0, openBraces - closeBraces));

  const openBrackets = (s.match(/\[/g) || []).length;
  const closeBrackets = (s.match(/\]/g) || []).length;
  s += ']'.repeat(Math.max(0, openBrackets - closeBrackets));

  // Close an odd number of quotes with a trailing quote as a last resort.
  const quoteCount = (s.match(/"/g) || []).length;
  if (quoteCount % 2 !== 0) {
    s += '"';
  }

  return s;
}

function generateHermesId(index: number): string {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    try {
      return crypto.randomUUID();
    } catch {
      // fall through
    }
  }
  return `hermes_${index}`;
}

export function parseHermesToolCalls(content: string): ToolCallIntent[] {
  const regex = /<tool_call>([\s\S]*?)<\/tool_call>/g;
  const intents: ToolCallIntent[] = [];
  let match: RegExpExecArray | null = null;
  let index = 0;

  while ((match = regex.exec(content)) !== null) {
    const rawJson = match[1].trim();
    if (!rawJson) continue;

    let parsed: Record<string, unknown> | null = null;
    try {
      parsed = JSON.parse(rawJson) as Record<string, unknown>;
    } catch {
      try {
        parsed = JSON.parse(repairJson(rawJson)) as Record<string, unknown>;
      } catch {
        parsed = null;
      }
    }

    if (!parsed || typeof parsed.name !== 'string') continue;

    let args: Record<string, unknown>;
    if (
      parsed.arguments &&
      typeof parsed.arguments === 'object' &&
      !Array.isArray(parsed.arguments)
    ) {
      args = parsed.arguments as Record<string, unknown>;
    } else {
      // Treat every field except "name" and "id" as top-level arguments.
      const rest = { ...parsed };
      delete rest.name;
      delete rest.id;
      args = rest;
    }

    intents.push({
      id: typeof parsed.id === 'string' ? parsed.id : generateHermesId(index),
      name: parsed.name,
      arguments: JSON.stringify(args),
    });
    index++;
  }

  return intents;
}

export class ToolExecutor {
  private registry: ToolRegistry;
  private options: Required<Pick<ToolExecutorOptions, 'maxRounds' | 'timeoutMs' | 'maxResultLength'>> &
    Pick<ToolExecutorOptions, 'onToolResult' | 'onEvent'>;

  constructor(registry: ToolRegistry, options?: ToolExecutorOptions) {
    this.registry = registry;
    this.options = {
      maxRounds: options?.maxRounds ?? 5,
      timeoutMs: options?.timeoutMs ?? 15000,
      maxResultLength: options?.maxResultLength ?? 4000,
      onToolResult: options?.onToolResult,
      onEvent: options?.onEvent,
    };
  }

  async execute(
    messages: HistoryMessage[],
    rawToolCalls?: unknown[],
    assistantContent?: string
  ): Promise<{ messages: HistoryMessage[]; toolCalls: ToolExecutionRecord[] }> {
    const currentMessages = [...messages];

    let calls = rawToolCalls;
    if ((!calls || calls.length === 0) && assistantContent && assistantContent.includes('<tool_call>')) {
      const hermesIntents = parseHermesToolCalls(assistantContent);
      calls = hermesIntents.map((intent) => ({
        id: intent.id,
        type: 'function' as const,
        function: {
          name: intent.name,
          arguments: intent.arguments,
        },
      }));
    }

    if (!calls || calls.length === 0) {
      // When the model returns content without tool calls, the caller is
      // responsible for generating or capturing the final assistant response.
      // Pushing the content here would cause duplicate assistant messages.
      return { messages: currentMessages, toolCalls: [] };
    }

    const intents = this.parseIntents(calls);
    const records = await this.scheduleAndExecute(intents);
    const toolMessages = this.buildToolMessages(records);

    currentMessages.push({
      role: 'assistant',
      content: assistantContent ?? '',
      tool_calls: calls as ToolCall[],
    });
    currentMessages.push(...toolMessages);

    return { messages: currentMessages, toolCalls: records };
  }

  parseIntents(rawToolCalls: unknown[]): ToolCallIntent[] {
    const intents: ToolCallIntent[] = [];
    for (const raw of rawToolCalls) {
      if (!raw || typeof raw !== 'object') {
        continue;
      }
      const call = raw as Record<string, unknown>;
      const id = String(call.id || '');
      const fn = call.function as Record<string, unknown> | undefined;
      const rawName = fn?.name;
      const rawArgs = fn?.arguments;
      if (!id || typeof rawName !== 'string' || typeof rawArgs !== 'string') {
        continue;
      }
      const name = this.registry.normalizeToolName(rawName);
      intents.push({ id, name, arguments: rawArgs });
    }
    return intents;
  }

  async scheduleAndExecute(intents: ToolCallIntent[]): Promise<ToolExecutionRecord[]> {
    const records: ToolExecutionRecord[] = new Array(intents.length);

    let i = 0;
    while (i < intents.length) {
      const intent = intents[i];
      const tool = this.registry.get(intent.name);
      const isReadonly = tool ? tool.readonly !== false : false;

      if (isReadonly) {
        const batch: { intent: ToolCallIntent; index: number }[] = [];
        while (i < intents.length) {
          const current = intents[i];
          const currentTool = this.registry.get(current.name);
          if (!currentTool || currentTool.readonly === false) {
            break;
          }
          batch.push({ intent: current, index: i });
          i++;
        }
        await Promise.all(
          batch.map(({ intent, index }) =>
            this.executeOne(intent).then((record) => {
              records[index] = record;
            })
          )
        );
      } else {
        records[i] = await this.executeOne(intent);
        i++;
      }
    }

    return records;
  }

  async executeOne(intent: ToolCallIntent): Promise<ToolExecutionRecord> {
    const tool = this.registry.get(intent.name);
    if (!tool) {
      const record: ToolExecutionRecord = {
        id: intent.id,
        name: intent.name,
        args: {},
        result: `工具 "${intent.name}" 未找到`,
      };
      this.notify(record);
      return record;
    }

    let args: Record<string, unknown>;
    try {
      args = this.parseArguments(intent.arguments);
    } catch (err) {
      const record: ToolExecutionRecord = {
        id: intent.id,
        name: intent.name,
        args: {},
        result: `参数解析失败：${err instanceof Error ? err.message : String(err)}`,
      };
      this.notify(record);
      return record;
    }

    try {
      const rawResult = await Promise.race([
        tool.execute(args),
        new Promise<never>((_, reject) => {
          setTimeout(
            () => reject(new Error(`工具执行超时（${this.options.timeoutMs}ms）`)),
            this.options.timeoutMs
          );
        }),
      ]);
      const result = this.truncateResult(String(rawResult ?? ''));
      const record: ToolExecutionRecord = { id: intent.id, name: intent.name, args, result };
      this.notify(record);
      return record;
    } catch (err) {
      const record: ToolExecutionRecord = {
        id: intent.id,
        name: intent.name,
        args,
        result: `执行失败：${err instanceof Error ? err.message : String(err)}`,
      };
      this.notify(record);
      return record;
    }
  }

  buildToolMessages(records: ToolExecutionRecord[]): HistoryMessage[] {
    return records.map((record) => ({
      role: 'tool',
      content: record.result,
      tool_call_id: record.id,
      name: record.name,
    }));
  }

  private parseArguments(raw: string): Record<string, unknown> {
    try {
      return JSON.parse(raw) as Record<string, unknown>;
    } catch {
      const repaired = repairJson(raw);
      return JSON.parse(repaired) as Record<string, unknown>;
    }
  }

  private truncateResult(result: string): string {
    const max = this.options.maxResultLength;
    if (result.length <= max) return result;
    return result.slice(0, max) + '...（已裁剪）';
  }

  private notify(record: ToolExecutionRecord): void {
    this.options.onToolResult?.(record);
    this.options.onEvent?.({
      type: 'tool_result',
      data: {
        id: record.id,
        name: record.name,
        args: record.args,
        result: record.result,
      },
    });
  }
}
