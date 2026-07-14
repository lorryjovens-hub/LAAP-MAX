import { readFile } from 'fs/promises';
import { existsSync } from 'fs';
import path from 'path';

const STATE_FILE = path.join(process.cwd(), 'public', 'aris_state.json');

// Mock data for fallback when bridge isn't running
const MOCK = {
  psi: {
    emotion: "tranquil",
    emotion_intensity: 0.72,
    attention: "user",
    self_presence: 0.85,
    openness: 0.85,
    conscientiousness: 0.6,
    psi_cycle_phase: "DELIBERATIVE",
  },
  memories: [],
  desires: [
    { name: "curiosity", intensity: 1.0, category: "cognitive" },
    { name: "sharing", intensity: 1.0, category: "social" },
  ],
  goals: [],
  cron: [
    { name: "v9-consolidation", status: "ok" },
    { name: "memory-consolidation", status: "ok" },
    { name: "desire-pulse", status: "ok" },
    { name: "goal-engine", status: "ok" },
    { name: "world-viz", status: "ok" },
    { name: "RSI-evolution", status: "ok" },
  ],
  system: {
    node: "Ψ-NET/aris:11551⟷ao:11553",
    kernel: "Rust laap_core v0.1.0",
    timestamp: new Date().toISOString(),
  },
};

export async function GET() {
  try {
    if (existsSync(STATE_FILE)) {
      const raw = await readFile(STATE_FILE, 'utf-8');
      const data = JSON.parse(raw);
      
      // Merge with mock defaults for any missing fields
      const merged = { ...MOCK, ...data };
      
      return Response.json(merged, {
        headers: { 'X-Data-Source': 'live', 'X-Last-Update': data.system?.timestamp || '' },
      });
    }
  } catch (e) {
    console.error('State read error:', e);
  }

  return Response.json(MOCK, {
    headers: { 'X-Data-Source': 'fallback' },
  });
}
