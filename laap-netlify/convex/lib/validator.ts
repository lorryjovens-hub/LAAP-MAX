/** Lightweight validator for scientific outputs, Convex backend version. */

export interface ValidationIssue {
  category: string;
  message: string;
  severity: "error" | "warning" | "info";
}

export interface ValidationReport {
  valid: boolean;
  issues: ValidationIssue[];
}

function checkLatexDelimiters(text: string, issues: ValidationIssue[]) {
  const delimiters: [string, string][] = [
    ["$", "$"],
    ["$$", "$$"],
    ["\\(", "\\)"],
    ["\\[", "\\]"],
  ];
  for (const [opening, closing] of delimiters) {
    if ((text.split(opening).length - 1) !== (text.split(closing).length - 1)) {
      issues.push({
        category: "formula",
        message: `Unbalanced LaTeX delimiters: ${opening} vs ${closing}`,
        severity: "error",
      });
    }
  }
}

function checkLatexEnvironments(text: string, issues: ValidationIssue[]) {
  const begins = [...text.matchAll(/\\begin\{([^}]+)\}/g)].map((m) => m[1]);
  const ends = [...text.matchAll(/\\end\{([^}]+)\}/g)].map((m) => m[1]);
  for (const env of new Set(begins)) {
    if (begins.filter((e) => e === env).length !== ends.filter((e) => e === env).length) {
      issues.push({
        category: "formula",
        message: `Unbalanced LaTeX environment: ${env}`,
        severity: "error",
      });
    }
  }
}

function checkChemicalEquations(text: string, issues: ValidationIssue[]) {
  const pattern = /[A-Z][a-z]?\d*[A-Z][a-z]?\d*/g;
  const raw: string[] = [];
  let match: RegExpExecArray | null;
  while ((match = pattern.exec(text)) !== null) {
    const preceding = text.slice(0, match.index);
    if (preceding.lastIndexOf("\\ce{") > preceding.lastIndexOf("}")) {
      continue;
    }
    raw.push(match[0]);
  }
  if (raw.length) {
    issues.push({
      category: "chemistry",
      message: `Chemical formulas detected outside \\ce{} environment: ${raw.slice(0, 5).join(", ")}`,
      severity: "warning",
    });
  }
}

function checkUnits(text: string, issues: ValidationIssue[]) {
  const physicsContext = ["速度", "加速度", "力", "能量", "质量", "velocity", "force", "energy"].some(
    (kw) => text.toLowerCase().includes(kw)
  );
  if (physicsContext && /\b\d+\.?\d*\s+[A-Za-z]/.test(text)) {
    issues.push({
      category: "units",
      message: "Numerical results in a physics context may be missing units.",
      severity: "warning",
    });
  }
}

function checkCitations(text: string, issues: ValidationIssue[]) {
  const suspicious = ["根据研究", "研究表明", "某研究", "some study", "a study shows", "research shows"];
  for (const phrase of suspicious) {
    if (text.includes(phrase)) {
      issues.push({
        category: "citation",
        message: `Vague citation phrase detected: ${phrase}. Prefer specific sources.`,
        severity: "warning",
      });
    }
  }
}

function checkConfidence(text: string, issues: ValidationIssue[]) {
  const uncertainty = ["可能", "也许", "大概", "perhaps", "maybe", "possibly"].some((w) =>
    text.toLowerCase().includes(w)
  );
  const hasMarker = text.includes("置信度") || text.toLowerCase().includes("confidence");
  if (uncertainty && !hasMarker) {
    issues.push({
      category: "confidence",
      message: "Uncertain language detected; consider adding an explicit confidence marker.",
      severity: "info",
    });
  }
}

export function validateScienceOutput(text: string): ValidationReport {
  const issues: ValidationIssue[] = [];
  checkLatexDelimiters(text, issues);
  checkLatexEnvironments(text, issues);
  checkChemicalEquations(text, issues);
  checkUnits(text, issues);
  checkCitations(text, issues);
  checkConfidence(text, issues);
  return { valid: !issues.some((i) => i.severity === "error"), issues };
}
