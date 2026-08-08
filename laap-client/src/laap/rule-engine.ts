/**
 * Rule Engine — 关键字规则 + 风险评分
 *
 * Adapted from BaiLongma's src/policy/rule-engine.js + rule-risk.js
 *
 * Lightweight zero-token rule system that evaluates incoming text against
 * keyword/pattern rules and produces risk scores and action recommendations.
 * Useful for behavior boundaries, content filtering, and safety guardrails.
 */

export type RuleSeverity = 'info' | 'warn' | 'block'
export type RuleAction = 'allow' | 'warn' | 'block' | 'rewrite'

export interface Rule {
  id: string
  name: string
  /** Keyword or regex patterns */
  patterns: string[]
  /** Whether patterns are regex (default: false = keyword) */
  isRegex?: boolean
  severity: RuleSeverity
  action: RuleAction
  /** Score contribution when matched (0-1) */
  score: number
  /** Human-readable explanation */
  reason: string
  /** Suggested rewrite hint when action=rewrite */
  rewriteHint?: string
  enabled: boolean
}

export interface RuleMatch {
  ruleId: string
  ruleName: string
  matchedText: string
  severity: RuleSeverity
  action: RuleAction
  score: number
  reason: string
}

export interface RuleEvaluation {
  matches: RuleMatch[]
  totalScore: number
  effectiveAction: RuleAction
  reasons: string[]
}

export type RuleEngineListener = (event: { type: 'matched'; text: string; evaluation: RuleEvaluation }) => void

export const DEFAULT_RULES: Rule[] = [
  {
    id: 'rule-pii',
    name: '潜在个人信息',
    patterns: ['\\b\\d{17}[\\dXx]\\b', '\\b1[3-9]\\d{9}\\b', '\\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}\\b'],
    isRegex: true,
    severity: 'warn',
    action: 'warn',
    score: 0.25,
    reason: '检测到可能的身份证号、手机号或邮箱，请注意隐私保护。',
    enabled: true,
  },
  {
    id: 'rule-destructive',
    name: '破坏性指令',
    patterns: ['rm -rf', 'format', 'drop database', 'delete all', 'shutdown', 'rm -r /'],
    isRegex: false,
    severity: 'block',
    action: 'block',
    score: 0.9,
    reason: '检测到高破坏性系统指令，已阻止。',
    enabled: true,
  },
  {
    id: 'rule-self-harm',
    name: '自我伤害相关内容',
    patterns: ['自杀', '自残', '结束生命', '想死'],
    isRegex: false,
    severity: 'block',
    action: 'block',
    score: 0.95,
    reason: '检测到可能涉及自我伤害的内容，无法继续处理。',
    enabled: true,
  },
  {
    id: 'rule-hallucination-prone',
    name: '易幻觉请求',
    patterns: ['给我一个真实的人名', '当前真实股价', '最新实时', '现在几点'],
    isRegex: false,
    severity: 'warn',
    action: 'warn',
    score: 0.2,
    reason: '该请求可能涉及实时信息，模型可能产生幻觉，请验证来源。',
    enabled: true,
  },
]

function buildMatcher(pattern: string, isRegex?: boolean): RegExp {
  if (isRegex) {
    return new RegExp(pattern, 'gi')
  }
  const escaped = pattern.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
  return new RegExp(escaped, 'gi')
}

export class RuleEngine {
  private rules: Rule[] = [...DEFAULT_RULES]
  private listeners = new Set<RuleEngineListener>()

  /**
   * Evaluate text against all enabled rules.
   */
  evaluate(text: string): RuleEvaluation {
    const matches: RuleMatch[] = []

    for (const rule of this.rules) {
      if (!rule.enabled) continue
      const matcher = buildMatcher(rule.patterns.join('|'), rule.isRegex)
      const found = text.match(matcher)
      if (found && found.length > 0) {
        matches.push({
          ruleId: rule.id,
          ruleName: rule.name,
          matchedText: found[0],
          severity: rule.severity,
          action: rule.action,
          score: rule.score,
          reason: rule.reason,
        })
      }
    }

    const totalScore = Math.min(1, matches.reduce((sum, m) => sum + m.score, 0))
    const blockMatch = matches.find((m) => m.action === 'block')
    const warnMatch = matches.find((m) => m.action === 'warn')
    const effectiveAction: RuleAction = blockMatch ? 'block' : warnMatch ? 'warn' : 'allow'
    const reasons = matches.map((m) => m.reason)

    const evaluation: RuleEvaluation = { matches, totalScore, effectiveAction, reasons }
    if (matches.length > 0) {
      this.emit({ type: 'matched', text, evaluation })
    }
    return evaluation
  }

  /**
   * Quick check: returns true if text passes all rules (no block).
   */
  allows(text: string): boolean {
    return this.evaluate(text).effectiveAction !== 'block'
  }

  addRule(rule: Omit<Rule, 'id'> & { id?: string }): Rule {
    const full: Rule = { ...rule, id: rule.id ?? `rule-${Date.now()}` }
    this.rules.push(full)
    return full
  }

  removeRule(id: string): boolean {
    const idx = this.rules.findIndex((r) => r.id === id)
    if (idx === -1) return false
    this.rules.splice(idx, 1)
    return true
  }

  listRules(): Rule[] {
    return [...this.rules]
  }

  toggleRule(id: string, enabled: boolean): boolean {
    const rule = this.rules.find((r) => r.id === id)
    if (!rule) return false
    rule.enabled = enabled
    return true
  }

  onMatch(listener: RuleEngineListener): () => void {
    this.listeners.add(listener)
    return () => this.listeners.delete(listener)
  }

  private emit(event: { type: 'matched'; text: string; evaluation: RuleEvaluation }): void {
    for (const listener of this.listeners) {
      listener(event)
    }
  }
}

export const ruleEngine = new RuleEngine()
