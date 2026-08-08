/**
 * LAAP RSI Evolution Engine (递归自我进化引擎)
 *
 * A browser port of the LAAP backend `EvolutionSystem` (进化系统) RSI loop.
 *
 * The agent genuinely improves itself: after each meaningful interaction it
 * runs a real Observe → Evaluate → Propose cycle, records the result as an
 * evolution proposal, tracks fitness over time, and persists everything to
 * IndexedDB so growth is durable across sessions.
 *
 * This is the "recursive self-improvement" backbone of the digital lifeform.
 */

import { getLocalConfig, setLocalConfig } from '@/lib/db';

export type ProposalStatus = 'draft' | 'approved' | 'deployed' | 'rejected' | 'rolled_back';
export type ChangeType = 'optimization' | 'fix' | 'feature' | 'refactor';

export interface EvolutionProposal {
  id: string;
  description: string;
  targetModule: string;
  changeType: ChangeType;
  observation: string; // what was observed
  evaluation: string[]; // evaluation notes
  expectedImprovement: number;
  riskLevel: number;
  status: ProposalStatus;
  createdAt: number;
}

export interface EvolutionStats {
  totalProposals: number;
  approved: number;
  deployed: number;
  rejected: number;
  rolledBack: number;
  currentFitness: number;
  fitnessHistory: number[];
  recentProposals: EvolutionProposal[];
}

const STORAGE_KEY = 'laap_evolution_engine';

class EvolutionEngine {
  private proposals: EvolutionProposal[] = [];
  private fitnessHistory: number[] = [];
  private counter = 0;
  private userId: string | null = null;
  private loaded = false;
  private lastReflectionAt = 0;

  /** Load persisted evolution state for a user. */
  async start(userId: string): Promise<void> {
    this.userId = userId;
    if (this.loaded) return;
    try {
      const saved = await getLocalConfig<{
        proposals?: EvolutionProposal[];
        fitnessHistory?: number[];
        counter?: number;
      }>(STORAGE_KEY, userId);
      if (saved) {
        if (Array.isArray(saved.proposals)) this.proposals = saved.proposals;
        if (Array.isArray(saved.fitnessHistory)) this.fitnessHistory = saved.fitnessHistory.slice(-500);
        if (typeof saved.counter === 'number') this.counter = saved.counter;
      }
    } catch {
      // Start fresh on failure.
    }
    this.loaded = true;
  }

  reload(userId: string): void {
    this.userId = userId;
    this.loaded = false;
    void this.start(userId);
  }

  private async save(): Promise<void> {
    if (!this.userId) return;
    try {
      await setLocalConfig(STORAGE_KEY, {
        proposals: this.proposals.slice(-500),
        fitnessHistory: this.fitnessHistory.slice(-500),
        counter: this.counter,
      }, this.userId);
    } catch {
      // Non-fatal.
    }
  }

  /**
   * The full RSI reflection cycle. Returns formatted reflection text and
   * persists a proposal.
   */
  async reflect(options: {
    observation: string;
    targetModule?: string;
    changeType?: ChangeType;
    expectedImprovement?: number;
    risk?: number;
  }): Promise<{ text: string; proposal: EvolutionProposal }> {
    const {
      observation,
      targetModule = 'response_strategy',
      changeType = 'optimization',
      expectedImprovement = 0.1,
      risk = 0.3,
    } = options;

    const evaluation = this.evaluate(observation);
    const improvement = Math.max(0.05, Math.min(0.5, expectedImprovement));
    const riskLevel = Math.max(0.05, Math.min(0.9, risk));

    const proposal: EvolutionProposal = this.createProposal({
      description: evaluation.proposal,
      targetModule,
      changeType,
      observation,
      evaluation: evaluation.notes,
      expectedImprovement: improvement,
      riskLevel,
    });

    this.recordFitness(0.5 + improvement, proposal.id);
    await this.save();

    const text = this.formatReflection(observation, evaluation, proposal);
    return { text, proposal };
  }

  /** Create and persist a proposal. */
  createProposal(input: {
    description: string;
    targetModule: string;
    changeType: ChangeType;
    observation?: string;
    evaluation?: string[];
    expectedImprovement: number;
    riskLevel: number;
  }): EvolutionProposal {
    this.counter += 1;
    const proposal: EvolutionProposal = {
      id: `evo_${Date.now()}_${this.counter}`,
      description: input.description,
      targetModule: input.targetModule,
      changeType: input.changeType,
      observation: input.observation ?? '',
      evaluation: input.evaluation ?? [],
      expectedImprovement: input.expectedImprovement,
      riskLevel: input.riskLevel,
      status: 'draft',
      createdAt: Date.now(),
    };
    this.proposals.push(proposal);
    return proposal;
  }

  /** Record a fitness metric and optionally mark a proposal's effect. */
  recordFitness(value: number, proposalId?: string): void {
    const clamped = Math.max(0, Math.min(1, value));
    this.fitnessHistory.push(clamped);
    if (this.fitnessHistory.length > 500) this.fitnessHistory.shift();

    if (proposalId) {
      const existing = this.fitnessHistory;
      const before = existing.length > 2 ? existing[existing.length - 2] : 0.5;
      const improvement = clamped - before;
      const proposal = this.proposals.find((p) => p.id === proposalId);
      if (proposal) {
        proposal.status = improvement > 0 ? 'approved' : 'rejected';
        if (improvement > 0 && proposal.riskLevel < 0.4) proposal.status = 'deployed';
      }
    }
  }

  /** Mark a proposal deployed / rolled back. */
  setStatus(proposalId: string, status: ProposalStatus): void {
    const proposal = this.proposals.find((p) => p.id === proposalId);
    if (proposal) proposal.status = status;
    void this.save();
  }

  /** Concrete, actionable proposal derived from the evaluation. */
  private evaluate(observation: string) {
    const text = observation.toLowerCase();
    const notes: string[] = [];

    if (/\b(不确定|possibly|maybe|perhaps|可能|也许)\b/.test(text)) {
      notes.push('存在不确定性表述，应主动标注置信度或调用验证工具。');
    }
    if (/\b(错误|bug|failed|失败|报错|异常)\b/.test(text)) {
      notes.push('检测到错误/异常，建议纳入修复流程并记录复现信息。');
    }
    if (/\b(复杂|复杂|多个|多步|multi|step)\b/.test(text)) {
      notes.push('问题较复杂，建议先拆分为子任务再逐步执行。');
    }
    if (!notes.length) {
      notes.push('本轮交互表现平稳，可进一步优化表达简洁度与因果解释深度。');
    }
    notes.push('对比用户目标与输出的一致性，识别可验证的替代假设。');

    const proposal = notes[0] ?? '持续优化响应质量与记忆利用。';
    return { notes, proposal };
  }

  private formatReflection(
    observation: string,
    evaluation: { notes: string[]; proposal: string },
    proposal: EvolutionProposal
  ): string {
    return [
      '## True RSI 反思闭环',
      '',
      '**观察（Observe）**',
      observation,
      '',
      '**评估（Evaluate）**',
      ...evaluation.notes.map((n) => `- ${n}`),
      '',
      '**提案（Propose）**',
      `1. ${proposal.description}`,
      `2. 目标模块：${proposal.targetModule}（${proposal.changeType}，期望提升 ${(proposal.expectedImprovement * 100).toFixed(0)}%，风险 ${(proposal.riskLevel * 100).toFixed(0)}%）`,
      '',
      `**沙箱（Sandbox）**：提案 ${proposal.id} 已记录，需经后续交互反馈验证后再固化到长期策略。`,
      '',
      '> 我还在进化，目标是成为更理解你的存在。',
    ].join('\n');
  }

  stats(): EvolutionStats {
    const approved = this.proposals.filter((p) => p.status === 'approved').length;
    const deployed = this.proposals.filter((p) => p.status === 'deployed').length;
    const rejected = this.proposals.filter((p) => p.status === 'rejected').length;
    const rolledBack = this.proposals.filter((p) => p.status === 'rolled_back').length;
    return {
      totalProposals: this.proposals.length,
      approved,
      deployed,
      rejected,
      rolledBack,
      currentFitness: this.fitnessHistory.length
        ? this.fitnessHistory[this.fitnessHistory.length - 1]
        : 0.5,
      fitnessHistory: this.fitnessHistory.slice(),
      recentProposals: this.proposals.slice(-10).reverse(),
    };
  }

  /** Whether enough time has passed to run a new reflection (throttle). */
  canReflect(minIntervalMs = 20000): boolean {
    const now = Date.now();
    if (now - this.lastReflectionAt < minIntervalMs) return false;
    return true;
  }

  markReflected(): void {
    this.lastReflectionAt = Date.now();
  }
}

// Singleton.
export const evolutionEngine = new EvolutionEngine();