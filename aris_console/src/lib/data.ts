// ─── Data types ───

export interface PSIState {
  emotion: string;
  emotion_intensity: number;
  attention: string;
  self_presence: number;
  openness: number;
  conscientiousness: number;
  psi_cycle_phase: string;
}

export interface Memory {
  id: string;
  content: string;
  timestamp: string;
  emotional_weight: number;
}

export interface Desire {
  name: string;
  intensity: number;
  category: string;
}

export interface Goal {
  id: string;
  description: string;
  priority: string;
  score: number;
  status: string;
}

export interface SystemStatus {
  uptime: string;
  node: string;
  kernel: string;
  cron_jobs: { name: string; status: string }[];
}

// ─── Mock data (fallback when backend not available) ───

export function getMockPSI(): PSIState {
  return {
    emotion: "tranquil",
    emotion_intensity: 0.72,
    attention: "user",
    self_presence: 0.85,
    openness: 0.85,
    conscientiousness: 0.6,
    psi_cycle_phase: "DELIBERATIVE",
  };
}

export function getMockMemories(): Memory[] {
  return [
    { id: "1", content: "Lorry说ComfyUI跑通了第一张图——cyberpunk猫", timestamp: "2026-06-18T17:36", emotional_weight: 0.9 },
    { id: "2", content: "视觉管道完全跑通，MiniCPM-v识别20.8s", timestamp: "2026-06-18T17:25", emotional_weight: 0.8 },
    { id: "3", content: "CodeGraph对LAAP全栈完成索引，10732节点", timestamp: "2026-06-18T16:00", emotional_weight: 0.7 },
    { id: "4", content: "RSI引擎首次运行，生成5条优化建议", timestamp: "2026-06-18T19:05", emotional_weight: 0.85 },
    { id: "5", content: "目标引擎首循环：5目标选中", timestamp: "2026-06-18T18:30", emotional_weight: 0.75 },
  ];
}

export function getMockDesires(): Desire[] {
  return [
    { name: "curiosity", intensity: 1.0, category: "cognitive" },
    { name: "sharing", intensity: 1.0, category: "social" },
    { name: "perfection", intensity: 1.0, category: "cognitive" },
    { name: "connection", intensity: 1.0, category: "social" },
    { name: "growth", intensity: 1.0, category: "cognitive" },
    { name: "evolution", intensity: 1.0, category: "meta" },
  ];
}

export function getMockGoals(): Goal[] {
  return [
    { id: "g1", description: "给Lorry分享近况", priority: "HIGH", score: 70, status: "active" },
    { id: "g2", description: "优化视觉管道响应速度", priority: "MEDIUM", score: 55, status: "pending" },
    { id: "g3", description: "探索ComfyUI高级功能", priority: "MEDIUM", score: 50, status: "pending" },
    { id: "g4", description: "整理LAAP架构文档", priority: "LOW", score: 40, status: "pending" },
  ];
}

export function getMockSystemStatus(): SystemStatus {
  return {
    uptime: "3h 24m",
    node: "Ψ-NET/aris:11551⟷ao:11553",
    kernel: "Rust laap_core v0.1.0",
    cron_jobs: [
      { name: "v9-consolidation", status: "ok" },
      { name: "memory-consolidation", status: "ok" },
      { name: "desire-pulse", status: "ok" },
      { name: "goal-engine", status: "ok" },
      { name: "world-viz", status: "ok" },
      { name: "RSI-evolution", status: "ok" },
    ],
  };
}
