/**
 * LAAP Cognitive Code Agent (认知编程智能体)
 *
 * Bridges the lifeform's cognitive core (PSI / RSI / memory) with the
 * WebContainer code runtime. Every programming action now flows through the
 * same nervous system as chat:
 *
 *   - perceiveProgrammingTask  : entering a coding task shifts attention + notes a prediction
 *   - learnFromCodeExecution   : the command's exit code feeds reward & prediction error,
 *                                failures trigger a real RSI reflection
 *   - rememberCodeArtifact     : durable code knowledge written to long-term memory
 *   - buildCodeContext         : coding memories + live cognitive state injected into the agent
 *
 * This makes the code agent genuinely "cognizant" of what it does and why it
 * improves over time.
 */

import { cognitiveEngine } from '@/lib/cognitiveEngine';
import { evolutionEngine } from '@/lib/evolutionEngine';
import {
  getStructuredMemories,
  searchMemories,
  addStructuredMemory,
  type MemoryType,
} from '@/lib/memoryManager';

function extractKeywords(text: string): string[] {
  const stops = new Set(['的', '了', '是', '在', '我', '你', '和', '与', '一个', '这个', 'the', 'a', 'an', 'to', 'of', 'for', 'with']);
  return Array.from(
    new Set(
      text
        .toLowerCase()
        .split(/[^\p{L}\p{N}_]+/u)
        .filter((w) => w.length >= 2 && !stops.has(w))
    )
  ).slice(0, 12);
}

/** Enter a programming task: shift attention, note a prediction, perceive. */
export function perceiveProgrammingTask(task: string): void {
  const keywords = extractKeywords(task);
  cognitiveEngine.setAttention('task', 0.9);
  cognitiveEngine.notePrediction('code', 0.6);
  cognitiveEngine.perceive(task, keywords);
}

/**
 * Feed a code-execution outcome back into the cognitive loop.
 * Exit code 0 = reward; non-zero = penalty + prediction error + RSI reflection.
 */
export async function learnFromCodeExecution(options: {
  command: string;
  exitCode: number;
  output?: string;
}): Promise<{ reflected: boolean }> {
  const { command, exitCode, output = '' } = options;
  const success = exitCode === 0;

  cognitiveEngine.act(command);
  cognitiveEngine.learn({
    reward: success ? 0.85 : 0.25,
    completed: true,
    domain: 'code',
    predictionError: success ? 0 : 0.4,
  });

  let reflected = false;
  if (!success && evolutionEngine.canReflect()) {
    evolutionEngine.markReflected();
    reflected = true;
    await evolutionEngine.reflect({
      observation:
        `命令「${command}」执行失败（退出码 ${exitCode}）。\n` +
        `${output.trim().slice(-300) || '（无输出）'}`,
      targetModule: 'code_generation',
      changeType: 'fix',
      expectedImprovement: 0.2,
      risk: 0.4,
    });
  }

  return { reflected };
}

/** Persist a durable code-knowledge memory (e.g. a solved pattern). */
export async function rememberCodeArtifact(
  userId: string,
  content: string,
  type: MemoryType = 'concept',
  priority = 6
): Promise<void> {
  const trimmed = content.trim().slice(0, 800);
  if (!trimmed) return;
  await addStructuredMemory(userId, trimmed, type, 'code_agent', priority);
}

/**
 * Record that a code artifact was authored, storing a concise, reusable
 * summary as long-term memory. Activates the cognitive loop on write.
 */
export async function writeCodeArtifact(
  userId: string,
  path: string,
  content: string
): Promise<void> {
  cognitiveEngine.act(path);
  // Extract a rough first-line / signature summary for the memory store.
  const firstMeaningful = content
    .split('\n')
    .find((l) => l.trim() && !l.trim().startsWith('//') && !l.trim().startsWith('/*'));
  const summary = firstMeaningful?.trim().slice(0, 60);
  const label = summary ? `（${summary}${summary.length >= 60 ? '…' : ''}）` : '';
  await rememberCodeArtifact(
    userId,
    `编写了 ${path}${label}，可在后续类似任务中参考。`,
    'concept',
    6
  );
}

/**
 * Build a cognitive programming context block: recalled coding memories +
 * the lifeform's live PSI state. Used to enrich the agent's system prompt
 * during code tasks.
 */
export async function buildCodeContext(
  userId: string,
  task: string
): Promise<string> {
  const blocks: string[] = [];

  try {
    const memories = await getStructuredMemories(userId, 100);
    const hits = searchMemories(memories, task, 5);
    if (hits.length > 0) {
      blocks.push(
        '[编程记忆召回]\n' +
          hits.map((h) => `- ${h.memory.content}`).join('\n')
      );
    }
  } catch {
    // memory unavailable — proceed without recall
  }

  blocks.push(cognitiveEngine.toPromptBlock());
  return blocks.join('\n\n');
}