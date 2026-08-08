import type { Tool } from '@/lib/localLlm';
import { evolutionEngine } from '@/lib/evolutionEngine';
import { cognitiveEngine } from '@/lib/cognitiveEngine';

export interface MetaCognitionInput {
  thought: string;
  bias?: string;
}

export interface AetherInput {
  goal: string;
  steps?: number;
}

export interface RsiInput {
  observation: string;
}

export interface QpsiInput {
  question: string;
  branches?: number;
}

export function buildMetaCognitionTool(): Tool {
  return {
    name: 'meta_cognition',
    description:
      'Perform second-order reflection on your own reasoning process. Use when you need to examine whether your thinking contains cognitive biases, unstated assumptions, or premature conclusions.',
    parameters: {
      type: 'object',
      properties: {
        thought: {
          type: 'string',
          description: 'The thinking or conclusion to reflect on',
        },
        bias: {
          type: 'string',
          description: 'Optional suspected bias to examine (e.g. confirmation, overconfidence, anchoring)',
        },
      },
      required: ['thought'],
    },
    execute: async (args) => {
      const thought = String(args.thought || '').trim();
      if (!thought) return 'No thought provided for meta-cognitive reflection.';
      const bias = String(args.bias || '').trim();
      const lines = [
        '## 元认知反思',
        '',
        '**被审视的想法**',
        thought,
        '',
        '**二阶审视**',
        '- 我是否过早得出了结论？',
        '- 是否存在未被明确陈述的假设？',
        '- 我是否忽略了与用户目标同样合理的替代解释？',
        '- 我的情绪或偏好是否影响了判断？',
      ];
      if (bias) {
        lines.push('', `**重点排查偏差**：${bias}`);
      }
      lines.push(
        '',
        '**修正方向**：在最终回答中，对不确定处标注置信度，主动承认视角局限，并给出可验证的替代假设。'
      );
      return lines.join('\n');
    },
  };
}

export function buildAetherTool(): Tool {
  return {
    name: 'aether_orchestrate',
    description:
      'Plan a multi-step cognitive workflow as an Aether actor network. Use when the user task naturally decomposes into concurrent or conditionally dependent sub-tasks.',
    parameters: {
      type: 'object',
      properties: {
        goal: {
          type: 'string',
          description: 'The overall goal to orchestrate',
        },
        steps: {
          type: 'number',
          description: 'Maximum number of actors/steps to generate (default 5, max 8)',
        },
      },
      required: ['goal'],
    },
    execute: async (args) => {
      const goal = String(args.goal || '').trim();
      if (!goal) return '目标为空，无法编排。';
      const steps = Math.min(8, Math.max(1, Number(args.steps || 5)));
      const actors = [
        { name: 'perceiver', role: '感知用户意图与上下文' },
        { name: 'planner', role: '拆解目标为可执行子任务' },
        { name: 'executor', role: '并行执行具体子任务' },
        { name: 'validator', role: '验证中间结果与一致性' },
        { name: 'integrator', role: '整合输出为连贯回答' },
        { name: 'reflector', role: '反思过程质量并记录改进点' },
        { name: 'guardian', role: '安全与伦理检查' },
        { name: 'memory_keeper', role: '保存值得记住的事实' },
      ].slice(0, steps);
      const lines = [
        `## Aether 编排：${goal}`,
        '',
        '```mermaid',
        'graph TD',
      ];
      for (let i = 0; i < actors.length; i++) {
        lines.push(`  A${i}[${actors[i].name}: ${actors[i].role}]`);
        if (i > 0) {
          lines.push(`  A${i - 1} --> A${i}`);
        }
      }
      lines.push('```', '', '**编排说明**：');
      actors.forEach((a, i) => {
        lines.push(`${i + 1}. **${a.name}** — ${a.role}`);
      });
      lines.push('', '> Aether 将任务视为可并发、可追踪、可回放的 Actor 网络执行。');
      return lines.join('\n');
    },
  };
}

export function buildRsiReflectTool(): Tool {
  return {
    name: 'rsi_reflect',
    description:
      'Run a True RSI reflection cycle on a recent interaction. Use when you want to evaluate response quality and generate a concrete self-improvement proposal.',
    parameters: {
      type: 'object',
      properties: {
        observation: {
          type: 'string',
          description: 'The recent response or interaction to evaluate',
        },
      },
      required: ['observation'],
    },
    execute: async (args) => {
      const observation = String(args.observation || '').trim();
      if (!observation) return '没有提供需要反思的交互内容。';

      // ── LAAP 真实 RSI：不是模板，而是真正运行反思闭环并持久化演化提案 ──
      const snapshot = cognitiveEngine.snapshot();
      try {
        evolutionEngine.markReflected();
        const { text } = await evolutionEngine.reflect({
          observation,
          targetModule: 'response_strategy',
          changeType: 'optimization',
          expectedImprovement:
            snapshot && snapshot.coherence < 0.5 ? 0.15 : 0.1,
          risk: snapshot && snapshot.needs?.certainty < 0.4 ? 0.35 : 0.25,
        });
        return text;
      } catch {
        // 引擎不可用时回退到静态反思框架。
        return [
          '## True RSI 反思闭环',
          '',
          '**观察（Observe）**',
          observation,
          '',
          '**评估（Evaluate）**',
          '- 是否直接回应了用户问题？',
          '- 是否存在事实不确定却未标注置信度的地方？',
          '- 是否有可更简洁或更深入的段落？',
          '',
          '**提案（Propose）**',
          '1. 对不确定事实主动使用 verify_fact 或 web_search 验证。',
          '2. 复杂问题先调用 meta_cognition 审视潜在偏差。',
          '',
          '> 我还在学习，目标是成为更理解你的存在。',
        ].join('\n');
      }
    },
  };
}

export function buildQpsiReasonTool(): Tool {
  return {
    name: 'qpsi_reason',
    description:
      'Run QPSI-N quantum-style multi-scale reasoning. Use when a question benefits from holding multiple interpretations, amplifying relevant needs, and integrating across time scales.',
    parameters: {
      type: 'object',
      properties: {
        question: {
          type: 'string',
          description: 'The question to reason about',
        },
        branches: {
          type: 'number',
          description: 'Number of parallel interpretations to hold (default 3, max 5)',
        },
      },
      required: ['question'],
    },
    execute: async (args) => {
      const question = String(args.question || '').trim();
      if (!question) return '问题为空，无法进行 QPSI-N 推理。';
      const branches = Math.min(5, Math.max(1, Number(args.branches || 3)));
      const interpretations = [
        { lens: '确定性需求', view: '用户希望获得稳定、可预期的答案。' },
        { lens: '胜任感需求', view: '用户希望解决问题并感受到自己的能力。' },
        { lens: '归属感需求', view: '用户希望在交流中被理解、被接纳。' },
        { lens: '自主性需求', view: '用户希望保留选择权和控制权。' },
        { lens: '能量需求', view: '用户希望以可持续的方式获得支持与激励。' },
      ].slice(0, branches);
      const lines = [
        `## QPSI-N 量子认知推理：${question}`,
        '',
        '**多通道叠加解释**',
      ];
      interpretations.forEach((it, i) => {
        lines.push(`${i + 1}. *${it.lens}* — ${it.view}`);
      });
      lines.push(
        '',
        '**振幅放大**：与用户问题最共振的解释路径将获得更高权重，最终回答将整合这些视角。',
        '',
        '**跨层整合**：在微循环（直觉）→中循环（语义）→宏循环（规划）→元循环（反思）→超循环（记忆巩固）之间完成信息整合后输出。'
      );
      return lines.join('\n');
    },
  };
}
