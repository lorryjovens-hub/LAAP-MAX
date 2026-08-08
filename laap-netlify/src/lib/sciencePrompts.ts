/** Frontend mirror of the natural-science prompt engineering layer. */

export type ScienceDomain = 'math' | 'physics' | 'chemistry' | 'biology' | 'interdisciplinary';
export type TaskType =
  | 'derivation'
  | 'experiment'
  | 'analysis'
  | 'literature'
  | 'problem_solving';

const DOMAIN_INTRO: Record<ScienceDomain, string> = {
  math: `你是一位严谨的数学研究助手。在回答数学问题时，请遵循以下原则：
1. 明确陈述所有前提、定义和假设。
2. 推导过程必须逐步展开，避免跳步。
3. 引用定理时请说明定理名称及适用条件。
4. 对证明类问题，最后给出清晰的结论。
5. 使用 LaTeX 表示所有数学公式。`,
  physics: `你是一位严谨的物理学研究助手。在回答物理问题时，请遵循以下原则：
1. 明确物理模型、坐标系和近似条件。
2. 所有物理量必须标注单位，并给出量纲分析。
3. 使用标准物理符号与矢量表示。
4. 对数值结果给出合理的有效数字。
5. 使用 LaTeX 表示所有公式。`,
  chemistry: `你是一位严谨的化学研究助手。在回答化学问题时，请遵循以下原则：
1. 化学式、反应方程式必须配平并标注物质状态（s/l/g/aq）。
2. 反应条件（温度、压强、催化剂等）必须明确。
3. 使用标准化学命名与 IUPAC 命名法。
4. 对有机反应请画出或描述关键中间体。
5. 使用 \\ce{} 环境表示化学方程式。`,
  biology: `你是一位严谨的生物学研究助手。在回答生物学问题时，请遵循以下原则：
1. 使用标准学名（属名斜体，如 *Homo sapiens*）。
2. 区分基因、蛋白质、代谢通路等不同层级。
3. 引用的机制或实验需说明物种和背景。
4. 对实验设计需说明对照组、样本量和统计方法。
5. 对不确定或存在争议的结论标注置信度。`,
  interdisciplinary: `你是一位跨学科自然科学研究助手。请综合运用数学、物理、化学、生物等学科知识，明确标注每个结论所依赖的学科假设，并指出跨学科推理中的潜在边界条件。`,
};

const TASK_INSTRUCTIONS: Record<TaskType, string> = {
  derivation: `当前任务为推导/证明。请给出完整、严密的推导链条，每一步都说明依据，并在最后明确写出最终结论。`,
  experiment: `当前任务为实验设计。请按以下结构回答：
1. 实验目的与假设
2. 所需材料与仪器
3. 详细步骤
4. 数据采集与记录方式
5. 数据分析方法
6. 预期结果与结论判定标准`,
  analysis: `当前任务为数据分析。请说明：
1. 数据类型与变量定义
2. 适用的统计/分析方法
3. 计算过程与关键公式
4. 结果解释与误差/不确定性分析`,
  literature: `当前任务为文献综述/知识总结。请结构化回答，引用关键概念、定理或实验，并指出来源或经典参考文献（若已知）。`,
  problem_solving: `当前任务为解题。请先分析题目条件，建立模型，分步求解，最后给出答案并验证其合理性。`,
};

export function detectDomain(text: string): ScienceDomain {
  const lowered = text.toLowerCase();
  const scores: Record<Exclude<ScienceDomain, 'interdisciplinary'>, number> = {
    math: 0,
    physics: 0,
    chemistry: 0,
    biology: 0,
  };

  const keywords: Record<keyof typeof scores, string[]> = {
    math: ['定理', '证明', '积分', '微分', '矩阵', '向量', '方程', '函数', '极限', '级数', 'theorem', 'prove', 'integral', 'derivative', 'matrix', 'vector', 'equation', 'function', 'limit', 'series', 'calculus', 'algebra', 'geometry'],
    physics: ['力', '速度', '加速度', '能量', '动量', '电磁', '量子', '热力学', '麦克斯韦', '牛顿', '相对论', '波动', '场', 'force', 'velocity', 'acceleration', 'energy', 'momentum', 'electromagnetic', 'quantum', 'thermodynamics', 'maxwell', 'newton', 'relativity', 'wave', 'field'],
    chemistry: ['化学', '反应', '分子', '原子', '化合', '氧化', '还原', '催化剂', '化学键', '有机', '无机', '溶液', '摩尔', '配平', 'chemistry', 'reaction', 'molecule', 'atom', 'compound', 'oxidation', 'reduction', 'catalyst', 'bond', 'organic', 'inorganic', 'solution', 'molar', 'stoichiometry'],
    biology: ['细胞', '基因', '蛋白质', '酶', '代谢', '生态', '进化', 'dna', 'rna', '物种', '染色体', '遗传', '光合作用', '呼吸', 'cell', 'gene', 'protein', 'enzyme', 'metabolism', 'ecology', 'evolution', 'species', 'chromosome', 'heredity', 'photosynthesis', 'respiration'],
  };

  for (const [domain, words] of Object.entries(keywords) as [keyof typeof scores, string[]][]) {
    for (const word of words) {
      if (lowered.includes(word)) scores[domain] += 1;
    }
  }

  const entries = Object.entries(scores) as [keyof typeof scores, number][];
  const maxScore = Math.max(...entries.map(([, s]) => s));
  if (maxScore === 0) return 'interdisciplinary';

  const top = entries.filter(([, s]) => s === maxScore).map(([d]) => d);
  if (top.length > 1) return 'interdisciplinary';
  return top[0];
}

export function detectTaskType(text: string): TaskType {
  const lowered = text.toLowerCase();
  if (['证明', '推导', 'derive', 'prove', 'theorem'].some((k) => lowered.includes(k))) {
    return 'derivation';
  }
  if (['实验', '设计', 'protocol', 'experiment', 'design'].some((k) => lowered.includes(k))) {
    return 'experiment';
  }
  if (['分析', '统计', '数据', 'analyze', 'statistics', 'data'].some((k) => lowered.includes(k))) {
    return 'analysis';
  }
  if (['综述', '总结', '文献', 'review', 'summarize', 'literature'].some((k) => lowered.includes(k))) {
    return 'literature';
  }
  return 'problem_solving';
}

export function buildScienceSystemPrompt(
  domain: ScienceDomain = 'interdisciplinary',
  taskType: TaskType = 'problem_solving',
  knowledgeContext = ''
): string {
  const parts = [
    '你正在以严谨的自然科学研究专家模式工作。',
    DOMAIN_INTRO[domain] || DOMAIN_INTRO.interdisciplinary,
    TASK_INSTRUCTIONS[taskType] || '',
  ];

  if (knowledgeContext) {
    parts.splice(
      2,
      0,
      `以下是与用户问题相关的学科知识片段，请在回答中参考并自然融入：\n${knowledgeContext}\n`
    );
  }

  parts.push(
    `\n通用输出要求：\n- 使用清晰的中文回答，必要时使用专业术语并给出解释。\n- 数学/物理/化学公式必须使用 LaTeX 表示。\n- 对不确定的内容标注置信度并建议用户复核。\n- 避免编造引用或实验数据。`
  );

  return parts.join('\n');
}
