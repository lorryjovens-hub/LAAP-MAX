import { searchMemories, getStructuredMemories } from '@/lib/memoryManager';

export interface FactClaim {
  text: string;
  category: 'factual' | 'speculative' | 'subjective' | 'unverifiable';
  confidence: 'high' | 'medium' | 'low';
  sources?: string[];
}

export interface HallucinationReport {
  claims: FactClaim[];
  uncertainPhrases: string[];
  recommendation: string;
}

const UNCERTAINTY_MARKERS = [
  '可能', '也许', '大概', '似乎', '应该', '估计', '我猜', '我觉得', '不排除',
  'perhaps', 'maybe', 'probably', 'likely', 'seems', 'might', 'could', 'possibly',
  '据说', '传闻', '有人认为', '一种观点认为',
];

const FACTUAL_PATTERNS = [
  /\d{4}年/, // years
  /\b(v\d+\.\d+|\d+\.\d+\.\d+)\b/, // version numbers
  /\d{1,3}(,\d{3})+(\.\d+)?/, // numbers with commas
  /\b(成立|发布|推出|发明|发现|获得|死于|生于)\b/, // factual verbs
];

export function extractClaims(text: string): FactClaim[] {
  const sentences = text.split(/[。！？\n]/).filter((s) => s.trim().length > 5);
  const claims: FactClaim[] = [];

  for (const sentence of sentences) {
    const lower = sentence.toLowerCase();
    const hasUncertainty = UNCERTAINTY_MARKERS.some((m) => lower.includes(m.toLowerCase()));
    const hasFactualPattern = FACTUAL_PATTERNS.some((p) => p.test(sentence));

    let category: FactClaim['category'] = 'factual';
    let confidence: FactClaim['confidence'] = 'high';

    if (hasUncertainty) {
      category = 'speculative';
      confidence = 'low';
    } else if (/\b(我认为|我觉得|我相信|我喜欢|我讨厌)\b/.test(sentence)) {
      category = 'subjective';
      confidence = 'medium';
    } else if (!hasFactualPattern) {
      category = 'unverifiable';
      confidence = 'medium';
    }

    claims.push({ text: sentence.trim(), category, confidence });
  }

  return claims;
}

export function findUncertaintyMarkers(text: string): string[] {
  const found = new Set<string>();
  for (const marker of UNCERTAINTY_MARKERS) {
    if (text.toLowerCase().includes(marker.toLowerCase())) {
      found.add(marker);
    }
  }
  return Array.from(found);
}

export async function crossCheckWithMemories(
  userId: string,
  text: string
): Promise<{ contradictions: string[]; supports: string[] }> {
  const claims = extractClaims(text).filter((c) => c.category === 'factual');
  const memories = await getStructuredMemories(userId, 100);
  const contradictions: string[] = [];
  const supports: string[] = [];

  for (const claim of claims) {
    const results = searchMemories(memories, claim.text, 3);
    for (const r of results) {
      if (r.score > 0.5) {
        supports.push(r.memory.content);
      } else if (r.score > 0.2 && r.score <= 0.4) {
        contradictions.push(`记忆「${r.memory.content}」与陈述「${claim.text}」可能存在冲突。`);
      }
    }
  }

  return { contradictions: [...new Set(contradictions)], supports: [...new Set(supports)] };
}

export function applyUncertaintyMarkers(text: string): string {
  let result = text;
  for (const marker of UNCERTAINTY_MARKERS) {
    const regex = new RegExp(`(${marker.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})([^，。！？\\s]{2,40})`, 'gi');
    result = result.replace(regex, '$1〔推测〕$2');
  }
  return result;
}

export function buildHallucinationReport(text: string): HallucinationReport {
  const claims = extractClaims(text);
  const uncertainPhrases = findUncertaintyMarkers(text);
  const factualClaims = claims.filter((c) => c.category === 'factual');
  const speculativeClaims = claims.filter((c) => c.category === 'speculative');

  let recommendation = '该回复以事实性内容为主，可信度较高。';
  if (speculativeClaims.length > 0 && factualClaims.length > 0) {
    recommendation = '回复中包含推测性内容，请以批判性思维核实关键事实。';
  } else if (speculativeClaims.length > factualClaims.length) {
    recommendation = '回复中推测性内容较多，建议通过外部检索或追问进一步验证。';
  }

  return { claims, uncertainPhrases, recommendation };
}

export function stripUncertaintyMarkers(text: string): string {
  return text.replace(/〔推测〕/g, '');
}
