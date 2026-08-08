import { getLocalConfig, setLocalConfig } from '@/lib/db';

export const SKILLS_KEY = 'laap_skills';

export interface SkillManifest {
  id: string;
  name: string;
  description: string;
  version: string;
  author?: string;
  tags?: string[];
  enabled: boolean;
  config: Record<string, unknown>;
  tools?: {
    name: string;
    description: string;
    parameters: Record<string, unknown>;
  }[];
  prompt?: string;
  installedAt: string;
}

export interface SkillRegistryItem {
  id: string;
  name: string;
  description: string;
  version: string;
  source: 'builtin' | 'custom';
}

export const BUILTIN_SKILLS: SkillRegistryItem[] = [
  {
    id: 'web_search',
    name: '网络搜索',
    description: '让 LAAP 能够实时搜索互联网信息',
    version: '1.0.0',
    source: 'builtin',
  },
  {
    id: 'long_term_memory',
    name: '长期记忆',
    description: '自动保存和检索用户相关事实',
    version: '1.0.0',
    source: 'builtin',
  },
  {
    id: 'causal_reasoning',
    name: '因果推理',
    description: '增强 LAAP 的因果链分析能力',
    version: '1.0.0',
    source: 'builtin',
  },
];

export async function listInstalledSkills(): Promise<SkillManifest[]> {
  const skills = await getLocalConfig<SkillManifest[]>(SKILLS_KEY);
  return skills ?? [];
}

export async function saveInstalledSkills(skills: SkillManifest[]): Promise<void> {
  await setLocalConfig(SKILLS_KEY, skills);
}

export async function installSkill(skill: Omit<SkillManifest, 'installedAt'>): Promise<SkillManifest> {
  const skills = await listInstalledSkills();
  const exists = skills.find((s) => s.id === skill.id);
  if (exists) {
    throw new Error('该技能已安装');
  }
  const created: SkillManifest = { ...skill, installedAt: new Date().toISOString() };
  await saveInstalledSkills([...skills, created]);
  return created;
}

export async function uninstallSkill(id: string): Promise<void> {
  const skills = await listInstalledSkills();
  await saveInstalledSkills(skills.filter((s) => s.id !== id));
}

export async function setSkillEnabled(id: string, enabled: boolean): Promise<void> {
  const skills = await listInstalledSkills();
  await saveInstalledSkills(skills.map((s) => (s.id === id ? { ...s, enabled } : s)));
}

export async function updateSkillConfig(id: string, config: Record<string, unknown>): Promise<void> {
  const skills = await listInstalledSkills();
  await saveInstalledSkills(skills.map((s) => (s.id === id ? { ...s, config } : s)));
}

export async function installBuiltinSkill(id: string): Promise<SkillManifest> {
  const registry = BUILTIN_SKILLS.find((s) => s.id === id);
  if (!registry) {
    throw new Error('未找到内置技能');
  }
  return installSkill({
    id: registry.id,
    name: registry.name,
    description: registry.description,
    version: registry.version,
    enabled: true,
    config: {},
  });
}

export function parseSkillManifest(text: string): SkillManifest {
  let data: Partial<SkillManifest>;
  try {
    data = JSON.parse(text) as Partial<SkillManifest>;
  } catch {
    throw new Error('技能文件不是有效的 JSON');
  }

  if (!data.id || !data.name || !data.description) {
    throw new Error('技能文件缺少必需字段：id, name, description');
  }

  return {
    id: data.id,
    name: data.name,
    description: data.description,
    version: data.version || '1.0.0',
    author: data.author,
    tags: data.tags,
    enabled: data.enabled ?? true,
    config: data.config || {},
    tools: data.tools,
    prompt: data.prompt,
    installedAt: new Date().toISOString(),
  };
}
