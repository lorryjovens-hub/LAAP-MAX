import { getLocalConfig, setLocalConfig } from '@/lib/db';
import type { LLMConfig } from '@/lib/config';
import type { LlmConfig } from '@/lib/llmConfig';
import { completeRawChat } from '@/lib/localLlm';

export type TaskStatus = 'pending' | 'in_progress' | 'completed' | 'blocked' | 'skipped';

export interface TaskNode {
  id: string;
  title: string;
  description: string;
  status: TaskStatus;
  dependencies: string[];
  estimatedMinutes?: number;
  acceptanceCriteria?: string[];
  notes?: string;
  startedAt?: string;
  completedAt?: string;
}

export interface TaskPlan {
  id: string;
  title: string;
  goal: string;
  mode: 'plan' | 'spec';
  createdAt: string;
  updatedAt: string;
  tasks: TaskNode[];
  milestones: string[];
  deadline?: string;
}

export interface SpecDefinition {
  title: string;
  goal: string;
  requirements: string[];
  acceptanceCriteria: string[];
  deliverables: string[];
  timeline: string;
  risks: string[];
}

const ACTIVE_PLAN_KEY = 'laap_active_task_plan';

export function parseCommand(text: string): { mode: 'plan' | 'spec' | null; query: string } {
  const trimmed = text.trim();
  if (trimmed.startsWith('/plan ')) {
    return { mode: 'plan', query: trimmed.slice(6).trim() };
  }
  if (trimmed.startsWith('/spec ')) {
    return { mode: 'spec', query: trimmed.slice(6).trim() };
  }
  if (trimmed === '/plan') return { mode: 'plan', query: '' };
  if (trimmed === '/spec') return { mode: 'spec', query: '' };
  return { mode: null, query: trimmed };
}

export function generatePlanFromText(text: string): TaskPlan {
  const lines = text.split('\n').map((l) => l.trim()).filter(Boolean);
  const title = lines[0] || '未命名计划';
  const goal = lines.find((l) => l.startsWith('目标：') || l.startsWith('Goal:'))?.replace(/^目标：|^Goal:/, '').trim() || title;

  const tasks: TaskNode[] = [];
  let currentTask: Partial<TaskNode> | null = null;

  for (const line of lines) {
    const stepMatch = line.match(/^(?:步骤|Step|Task)\s*(\d+)[-.:\u3001]\s*(.+)/i);
    if (stepMatch) {
      if (currentTask && currentTask.title) {
        tasks.push(createTaskNode(currentTask as Partial<TaskNode>));
      }
      currentTask = { title: stepMatch[2].trim() };
      continue;
    }

    if (!currentTask) continue;

    if (line.startsWith('描述：') || line.startsWith('Description:')) {
      currentTask.description = line.replace(/^描述：|^Description:/, '').trim();
    } else if (line.startsWith('依赖：') || line.startsWith('Dependencies:')) {
      const depText = line.replace(/^依赖：|^Dependencies:/, '').trim();
      currentTask.dependencies = depText ? depText.split(/[,，]/).map((s) => s.trim()) : [];
    } else if (line.startsWith('验收：') || line.startsWith('Acceptance:')) {
      const crit = line.replace(/^验收：|^Acceptance:/, '').trim();
      currentTask.acceptanceCriteria = crit ? crit.split(/[,，;；]/).map((s) => s.trim()) : [];
    } else if (line.startsWith('预计：') || line.startsWith('Estimate:')) {
      const minMatch = line.match(/(\d+)\s*(分钟|min|hour|小时)/i);
      if (minMatch) {
        const value = parseInt(minMatch[1], 10);
        currentTask.estimatedMinutes = /小时|hour/i.test(minMatch[2]) ? value * 60 : value;
      }
    }
  }

  if (currentTask && currentTask.title) {
    tasks.push(createTaskNode(currentTask as Partial<TaskNode>));
  }

  // Fallback: if no structured tasks found, create a simple sequential plan.
  if (tasks.length === 0) {
    const chunks = text.split(/[。！？\n]/).filter((s) => s.trim().length > 5);
    for (let i = 0; i < Math.min(chunks.length, 6); i++) {
      tasks.push(createTaskNode({ title: chunks[i].slice(0, 60), description: chunks[i] }));
    }
  }

  // Auto-link sequential dependencies.
  for (let i = 1; i < tasks.length; i++) {
    if (tasks[i].dependencies.length === 0) {
      tasks[i].dependencies = [tasks[i - 1].id];
    }
  }

  return {
    id: crypto.randomUUID(),
    title,
    goal,
    mode: 'plan',
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
    tasks,
    milestones: tasks.filter((_, i) => i > 0 && (i + 1) % 3 === 0).map((t) => `完成 ${t.title}`),
  };
}

function createTaskNode(partial: Partial<TaskNode>): TaskNode {
  return {
    id: partial.id || crypto.randomUUID(),
    title: partial.title || '未命名任务',
    description: partial.description || '',
    status: partial.status || 'pending',
    dependencies: partial.dependencies || [],
    estimatedMinutes: partial.estimatedMinutes,
    acceptanceCriteria: partial.acceptanceCriteria || [],
    notes: partial.notes || '',
  };
}

export function generateSpecFromText(text: string): SpecDefinition {
  const lines = text.split('\n').map((l) => l.trim()).filter(Boolean);
  const title = lines[0] || '未命名规格';
  const goal = lines.find((l) => l.startsWith('目标：') || l.startsWith('Goal:'))?.replace(/^目标：|^Goal:/, '').trim() || title;

  const extractSection = (markers: string[]): string[] => {
    const result: string[] = [];
    let capturing = false;
    for (const line of lines) {
      if (markers.some((m) => line.startsWith(m))) {
        capturing = true;
        continue;
      }
      if (capturing) {
        if (/^(目标|需求|验收|交付物|风险|时间线|Goal|Requirements|Acceptance|Deliverables|Risks|Timeline)/.test(line)) {
          break;
        }
        result.push(line.replace(/^[-*•]\s*/, '').trim());
      }
    }
    return result.filter(Boolean);
  };

  return {
    title,
    goal,
    requirements: extractSection(['需求：', '需求', 'Requirements:', 'Requirements']),
    acceptanceCriteria: extractSection(['验收标准：', '验收', 'Acceptance Criteria:', 'Acceptance']),
    deliverables: extractSection(['交付物：', '交付物', 'Deliverables:', 'Deliverables']),
    timeline: extractSection(['时间线：', '时间线', 'Timeline:', 'Timeline']).join('\n') || '未指定',
    risks: extractSection(['风险：', '风险', 'Risks:', 'Risks']),
  };
}

export async function saveActivePlan(plan: TaskPlan | null): Promise<void> {
  await setLocalConfig(ACTIVE_PLAN_KEY, plan);
}

export async function loadActivePlan(): Promise<TaskPlan | null> {
  return getLocalConfig<TaskPlan>(ACTIVE_PLAN_KEY);
}

export function updateTaskStatus(plan: TaskPlan, taskId: string, status: TaskStatus): TaskPlan {
  const now = new Date().toISOString();
  return {
    ...plan,
    updatedAt: now,
    tasks: plan.tasks.map((t) =>
      t.id === taskId
        ? {
            ...t,
            status,
            startedAt: status === 'in_progress' && !t.startedAt ? now : t.startedAt,
            completedAt: status === 'completed' ? now : t.completedAt,
          }
        : t
    ),
  };
}

export function formatPlanAsMarkdown(plan: TaskPlan): string {
  const lines: string[] = [`# ${plan.title}`, ``, `**目标**：${plan.goal}`, ``, `## 任务路线图`, ''];
  for (const task of plan.tasks) {
    const statusEmoji = {
      pending: '⬜',
      in_progress: '🔄',
      completed: '✅',
      blocked: '⛔',
      skipped: '⏭️',
    }[task.status];
    lines.push(`${statusEmoji} **${task.title}**`);
    if (task.description) lines.push(`   ${task.description}`);
    if (task.acceptanceCriteria?.length) {
      lines.push(`   验收：${task.acceptanceCriteria.join('；')}`);
    }
    if (task.estimatedMinutes) {
      lines.push(`   预计：${task.estimatedMinutes >= 60 ? `${Math.round(task.estimatedMinutes / 60)} 小时` : `${task.estimatedMinutes} 分钟`}`);
    }
    lines.push('');
  }
  if (plan.milestones.length) {
    lines.push('## 里程碑', '');
    plan.milestones.forEach((m, i) => lines.push(`${i + 1}. ${m}`));
  }
  return lines.join('\n');
}

export function formatSpecAsMarkdown(spec: SpecDefinition): string {
  const lines: string[] = [`# ${spec.title}`, ``, `**目标**：${spec.goal}`, ``];

  const section = (title: string, items: string[]) => {
    if (items.length === 0) return;
    lines.push(`## ${title}`, '');
    items.forEach((item, i) => lines.push(`${i + 1}. ${item}`));
    lines.push('');
  };

  section('需求', spec.requirements);
  section('验收标准', spec.acceptanceCriteria);
  section('交付物', spec.deliverables);
  section('风险', spec.risks);

  lines.push('## 时间线', '', spec.timeline);
  return lines.join('\n');
}

export function getNextPendingTask(plan: TaskPlan): TaskNode | undefined {
  return plan.tasks.find((t) => t.status === 'pending' && t.dependencies.every((depId) => {
    const dep = plan.tasks.find((x) => x.id === depId);
    return dep?.status === 'completed';
  }));
}

export async function generatePlanOrSpec(
  query: string,
  mode: 'plan' | 'spec',
  config: LLMConfig | LlmConfig
): Promise<{ plan?: TaskPlan; spec?: SpecDefinition; raw: string }> {
  const systemPrompt = mode === 'plan'
    ? `你是一名任务规划专家。用户将描述一个复杂目标，请将其拆解为可执行的任务路线图。
输出格式要求：
第一行：计划标题
第二行：目标：xxx
随后每项任务以 "步骤 N：任务标题" 开始，可包含描述、依赖、验收、预计。
示例：
步骤 1：需求分析
描述：梳理用户核心需求
依赖：无
验收：输出需求文档
预计：30 分钟`
    : `你是一名需求规格专家。用户将描述一个任务或项目，请生成详细的需求规格说明书。
输出格式要求：
第一行：规格标题
第二行：目标：xxx
随后分节输出：需求、验收标准、交付物、时间线、风险。`;

  const userPrompt = query
    ? `请为以下目标生成${mode === 'plan' ? '任务执行计划' : '需求规格说明'}：\n${query}`
    : `请生成一个${mode === 'plan' ? '任务执行计划' : '需求规格说明'}。`;

  const raw = await completeRawChat(config, [
    { role: 'system', content: systemPrompt },
    { role: 'user', content: userPrompt },
  ]);

  if (mode === 'plan') {
    return { plan: generatePlanFromText(raw), raw };
  }
  return { spec: generateSpecFromText(raw), raw };
}
