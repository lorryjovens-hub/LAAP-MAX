/**
 * Tool Policy — 工具调用权限策略
 *
 * Adapted from BaiLongma's src/tooling/tool-policy.js
 *
 * Controls which tools may be invoked, by whom, under what conditions, and
 * with what argument constraints. Policies are evaluated before a tool call
 * is executed; violations produce a policy decision with a reason.
 */

export type PolicyAction = 'allow' | 'deny' | 'confirm'

export interface PolicyRule {
  id: string
  name: string
  /** Tool name patterns (supports * wildcard) */
  toolPatterns: string[]
  /** Optional user/message pattern that triggers this rule */
  scope?: 'all' | 'user' | 'system' | 'agent'
  /** Maximum risk score this rule allows (0-1) */
  maxRisk?: number
  /** Require confirmation for destructive operations */
  requireConfirmation?: boolean
  /** Argument keys that are never allowed (e.g. 'force', 'recursive') */
  forbiddenArgs?: string[]
  /** Default action for this rule */
  action: PolicyAction
  /** Human-readable rationale */
  reason?: string
  enabled: boolean
  priority: number
}

export interface ToolCallIntent {
  toolName: string
  args: Record<string, unknown>
  caller: 'user' | 'agent' | 'system'
  riskScore: number
}

export interface PolicyDecision {
  action: PolicyAction
  reason: string
  ruleId?: string
}

export type PolicyListener = (event: { type: 'evaluated'; intent: ToolCallIntent; decision: PolicyDecision }) => void

export const DEFAULT_POLICIES: PolicyRule[] = [
  {
    id: 'policy-readonly',
    name: '只读工具默认允许',
    toolPatterns: ['web_search', 'file_read', 'memory_search', 'read_*'],
    scope: 'all',
    maxRisk: 0.3,
    action: 'allow',
    reason: '只读查询工具风险低，默认允许。',
    enabled: true,
    priority: 100,
  },
  {
    id: 'policy-destructive-confirm',
    name: '破坏性操作需确认',
    toolPatterns: ['code_exec', 'shell_exec', 'file_write', 'delete_*', 'rm*'],
    scope: 'all',
    requireConfirmation: true,
    forbiddenArgs: ['force', 'recursive', 'yes', 'y'],
    action: 'confirm',
    reason: '该工具可能修改系统状态或数据，需要用户确认。',
    enabled: true,
    priority: 200,
  },
  {
    id: 'policy-high-risk-deny',
    name: '高风险调用拒绝',
    toolPatterns: ['*'],
    scope: 'all',
    maxRisk: 0.85,
    action: 'deny',
    reason: '风险评分过高，已拒绝执行以保护系统安全。',
    enabled: true,
    priority: 999,
  },
]

function matchPattern(pattern: string, value: string): boolean {
  const regex = new RegExp(`^${pattern.replace(/\*/g, '.*')}$`, 'i')
  return regex.test(value)
}

function matchesRule(rule: PolicyRule, intent: ToolCallIntent): boolean {
  if (!rule.enabled) return false
  if (rule.scope && rule.scope !== 'all' && rule.scope !== intent.caller) return false
  return rule.toolPatterns.some((pattern) => matchPattern(pattern, intent.toolName))
}

function hasForbiddenArg(args: Record<string, unknown>, forbidden: string[]): boolean {
  const keys = Object.keys(args).map((k) => k.toLowerCase())
  return forbidden.some((f) => keys.includes(f.toLowerCase()))
}

export class ToolPolicy {
  private rules: PolicyRule[] = [...DEFAULT_POLICIES]
  private listeners = new Set<PolicyListener>()

  /**
   * Evaluate a tool call intent against all active policy rules.
   * Returns the most restrictive matching decision.
   */
  evaluate(intent: ToolCallIntent): PolicyDecision {
    const matches = this.rules
      .filter((rule) => matchesRule(rule, intent))
      .sort((a, b) => b.priority - a.priority)

    for (const rule of matches) {
      if (rule.maxRisk !== undefined && intent.riskScore > rule.maxRisk) {
        const decision: PolicyDecision = {
          action: rule.action === 'allow' ? 'deny' : rule.action,
          reason: `${rule.reason} (risk ${intent.riskScore.toFixed(2)} > max ${rule.maxRisk})`,
          ruleId: rule.id,
        }
        this.emit({ type: 'evaluated', intent, decision })
        return decision
      }

      if (rule.requireConfirmation) {
        const decision: PolicyDecision = { action: 'confirm', reason: rule.reason || '该工具调用需要您的确认。', ruleId: rule.id }
        this.emit({ type: 'evaluated', intent, decision })
        return decision
      }

      if (rule.forbiddenArgs && hasForbiddenArg(intent.args, rule.forbiddenArgs)) {
        const decision: PolicyDecision = {
          action: 'deny',
          reason: `${rule.reason} (forbidden argument detected)`,
          ruleId: rule.id,
        }
        this.emit({ type: 'evaluated', intent, decision })
        return decision
      }

      if (rule.action !== 'allow') {
        const decision: PolicyDecision = { action: rule.action, reason: rule.reason || '策略规则已触发。', ruleId: rule.id }
        this.emit({ type: 'evaluated', intent, decision })
        return decision
      }
    }

    const decision: PolicyDecision = {
      action: 'allow',
      reason: matches.length > 0
        ? `Matched ${matches.length} allow-rule(s).`
        : 'No policy rule matched; default allow.',
    }
    this.emit({ type: 'evaluated', intent, decision })
    return decision
  }

  addRule(rule: Omit<PolicyRule, 'id'> & { id?: string }): PolicyRule {
    const full: PolicyRule = {
      ...rule,
      id: rule.id ?? `policy-${Date.now()}`,
    }
    this.rules.push(full)
    this.rules.sort((a, b) => b.priority - a.priority)
    return full
  }

  removeRule(id: string): boolean {
    const idx = this.rules.findIndex((r) => r.id === id)
    if (idx === -1) return false
    this.rules.splice(idx, 1)
    return true
  }

  listRules(): PolicyRule[] {
    return [...this.rules]
  }

  toggleRule(id: string, enabled: boolean): boolean {
    const rule = this.rules.find((r) => r.id === id)
    if (!rule) return false
    rule.enabled = enabled
    return true
  }

  onEvaluate(listener: PolicyListener): () => void {
    this.listeners.add(listener)
    return () => this.listeners.delete(listener)
  }

  private emit(event: { type: 'evaluated'; intent: ToolCallIntent; decision: PolicyDecision }): void {
    for (const listener of this.listeners) {
      listener(event)
    }
  }
}

export const toolPolicy = new ToolPolicy()

/**
 * Estimate a simple risk score for a tool call based on name and arguments.
 */
export function estimateToolRisk(toolName: string, args: Record<string, unknown>): number {
  let risk = 0.1
  const name = toolName.toLowerCase()
  if (/exec|shell|run|script|eval/.test(name)) risk += 0.4
  if (/write|delete|remove|rm|update|patch/.test(name)) risk += 0.3
  if (/search|read|get|list|find/.test(name)) risk += 0.05

  const argStr = JSON.stringify(args).toLowerCase()
  if (/force|recursive|rm -rf|delete_all|drop/.test(argStr)) risk += 0.4
  if (typeof args.path === 'string' && /(^|[\\/])\.\./.test(args.path)) risk += 0.2

  return Math.min(1, risk)
}
