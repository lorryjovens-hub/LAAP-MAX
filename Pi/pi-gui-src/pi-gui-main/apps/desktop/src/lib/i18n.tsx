import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";

export type Language = "zh" | "en";

const STORAGE_KEY = "laap:language:v1";

/** 中英文界面词典。key 为语义化标识，zh/en 分别对应中文与英文文案。 */
const MESSAGES: Record<Language, Record<string, string>> = {
  zh: {
    // ── 通用 ──
    "common.cancel": "取消",
    "common.confirm": "确认",
    "common.save": "保存",
    "common.close": "关闭",
    "common.loading": "加载中…",
    "common.offline": "离线",
    "common.online": "在线",
    "common.current": "当前",
    "common.new": "新建",
    "common.open": "打开",
    "common.back": "返回",

    // ── LAAP 认知舱 ──
    "laap.cockpit": "LAAP 认知舱",
    "laap.collapseCockpit": "收起认知舱",
    "laap.cognition": "认知层",
    "laap.dominantNeed": "主导需求",
    "laap.need.certainty": "确定性",
    "laap.need.competence": "能力",
    "laap.need.autonomy": "自主",
    "laap.need.relatedness": "连接",
    "laap.need.energy": "能量",
    "laap.emotion": "情绪 VAD",
    "laap.entropy": "熵",
    "laap.regime": "流态",
    "laap.intrinsicReward": "内在奖励",
    "laap.thinkingMode": "思维模式",
    "laap.memory": "记忆",
    "laap.memory.episodic": "情景记忆",
    "laap.memory.semantic": "语义记忆",
    "laap.memory.skills": "技能",
    "laap.memory.reflections": "反思",
    "laap.memory.wm": "工作记忆",
    "laap.errorFrames": "错误反思帧",
    "laap.modules": "系统模块",
    "laap.actionHistory": "最近行动",
    "laap.brainOffline": "LAAP 大脑离线",
    "laap.setupLLM": "一键配置 LLM",
    "laap.setupDesc": "默认 OmniRoute 免费网关 + DeepSeek 模型",
    "laap.setupRunning": "配置中…",
    "laap.setupDone": "已配置：{provider}（默认 {model}）",
    "laap.personas": "人格 / LAAPer",
    "laap.createLaaper": "新建 LAAPer",
    "laap.createName": "实例名字（如：书生）",
    "laap.createDesc": "人格描述",
    "laap.createBtn": "创建 LAAPer",
    "laap.personaCurrent": "当前",

    // ── RSI 自我进化 ──
    "rsi.title": "RSI 自我进化",
    "rsi.generation": "进化代数",
    "rsi.evolveCount": "进化次数",
    "rsi.compiled": "热编译产物",
    "rsi.speciesCount": "物种库组件",
    "rsi.cacheEntries": "编译缓存",
    "rsi.evolve": "触发进化",
    "rsi.evolving": "进化中…",
    "rsi.evolved": "已进化：{component} → v{revision}",
    "rsi.history": "进化历史",
    "rsi.noHistory": "尚无进化记录，点击「触发进化」开始。",
    "rsi.lastEvolved": "最近进化",

    // ── 原子组件热编译 ──
    "comp.title": "原子组件库",
    "comp.subtitle": "RSI 热编译 · 0 token 复用",
    "comp.kind.cognitive": "认知",
    "comp.kind.code": "代码",
    "comp.insert": "插入",
    "comp.compile": "热编译",
    "comp.compiling": "编译中…",
    "comp.compiled": "已编译",
    "comp.raw": "原始",
    "comp.rev": "v{rev}",
    "comp.inserted": "已将 {name} 插入输入框",
    "comp.insertHint": "点击「插入」把组件模板加入聊天输入框。",
    "comp.empty": "组件库为空",
    "comp.error": "组件库加载失败",

    // ── 界面导航与主界面 ──
    "nav.threads": "对话",
    "nav.settings": "设置",
    "nav.skills": "技能",
    "nav.extensions": "扩展",
    "nav.cockpit": "认知舱",
    "sidebar.newThread": "新对话",
    "sidebar.openFolder": "打开文件夹",
    "sidebar.empty": "暂无可用文件夹",
    "composer.placeholder": "询问 LAAP 检查仓库、修复问题或继续当前对话…",
    "composer.send": "发送消息",
    "composer.attach": "附加文件",
    "composer.stop": "停止运行",
    "empty.workspaceTitle": "打开文件夹开始",
    "empty.openFolderDesc": "添加项目文件夹后再创建新对话。",
    "empty.threadTitle": "为当前文件夹创建对话",
    "empty.threadDesc": "为这个文件夹创建对话，然后从侧边栏切换会话。",
    "settings.general": "通用",
    "settings.appearance": "外观",
    "settings.models": "模型",
    "settings.providers": "服务商",
    "settings.notifications": "通知",
    "settings.customEndpoints": "自定义端点",
    "lang.switch": "切换语言",
  },
  en: {
    // ── Common ──
    "common.cancel": "Cancel",
    "common.confirm": "Confirm",
    "common.save": "Save",
    "common.close": "Close",
    "common.loading": "Loading…",
    "common.offline": "Offline",
    "common.online": "Online",
    "common.current": "Current",
    "common.new": "New",
    "common.open": "Open",
    "common.back": "Back",

    // ── LAAP Cockpit ──
    "laap.cockpit": "LAAP Cockpit",
    "laap.collapseCockpit": "Collapse cockpit",
    "laap.cognition": "Cognition",
    "laap.dominantNeed": "Dominant need",
    "laap.need.certainty": "Certainty",
    "laap.need.competence": "Competence",
    "laap.need.autonomy": "Autonomy",
    "laap.need.relatedness": "Relatedness",
    "laap.need.energy": "Energy",
    "laap.emotion": "Emotion VAD",
    "laap.entropy": "Entropy",
    "laap.regime": "Regime",
    "laap.intrinsicReward": "Intrinsic reward",
    "laap.thinkingMode": "Thinking mode",
    "laap.memory": "Memory",
    "laap.memory.episodic": "Episodic",
    "laap.memory.semantic": "Semantic",
    "laap.memory.skills": "Skills",
    "laap.memory.reflections": "Reflections",
    "laap.memory.wm": "Working memory",
    "laap.errorFrames": "Error frames",
    "laap.actionHistory": "Recent actions",
    "laap.brainOffline": "LAAP brain offline",
    "laap.setupLLM": "One-click LLM setup",
    "laap.setupDesc": "Default OmniRoute free gateway + DeepSeek model",
    "laap.setupRunning": "Configuring…",
    "laap.setupDone": "Configured: {provider} (default {model})",
    "laap.personas": "Personas / LAAPers",
    "laap.createLaaper": "New LAAPer",
    "laap.createName": "Instance name (e.g. scholar)",
    "laap.createDesc": "Persona description",
    "laap.createBtn": "Create LAAPer",
    "laap.personaCurrent": "Current",

    // ── RSI self-evolution ──
    "rsi.title": "RSI Self-Evolution",
    "rsi.generation": "Generation",
    "rsi.evolveCount": "Evolutions",
    "rsi.compiled": "Hot-compiled",
    "rsi.speciesCount": "Species components",
    "rsi.cacheEntries": "Compile cache",
    "rsi.evolve": "Evolve",
    "rsi.evolving": "Evolving…",
    "rsi.evolved": "Evolved: {component} → v{revision}",
    "rsi.history": "Evolution history",
    "rsi.noHistory": "No evolution yet. Click “Evolve” to start.",
    "rsi.lastEvolved": "Last evolved",

    // ── Atomic components ──
    "comp.title": "Atomic Components",
    "comp.subtitle": "RSI hot-compiled · 0-token reuse",
    "comp.kind.cognitive": "Cognitive",
    "comp.kind.code": "Code",
    "comp.insert": "Insert",
    "comp.compile": "Compile",
    "comp.compiling": "Compiling…",
    "comp.compiled": "Compiled",
    "comp.raw": "Raw",
    "comp.rev": "v{rev}",
    "comp.inserted": "Inserted {name} into the composer",
    "comp.insertHint": "Click “Insert” to add a component template to the chat input.",
    "comp.empty": "Component library is empty",
    "comp.error": "Failed to load component library",

    // ── Navigation & main UI ──
    "nav.threads": "Threads",
    "nav.settings": "Settings",
    "nav.skills": "Skills",
    "nav.extensions": "Extensions",
    "nav.cockpit": "Cockpit",
    "sidebar.newThread": "New thread",
    "sidebar.openFolder": "Open folder",
    "sidebar.empty": "No folders available",
    "composer.placeholder": "Ask LAAP to inspect the repo, run a fix, or continue the current thread…",
    "composer.send": "Send message",
    "composer.attach": "Attach files",
    "composer.stop": "Stop run",
    "empty.workspaceTitle": "Open a folder to start",
    "empty.openFolderDesc": "Add a project folder before creating a new thread.",
    "empty.threadTitle": "Create a thread for this folder",
    "empty.threadDesc": "Create a thread for this folder, then jump between sessions from the sidebar.",
    "settings.general": "General",
    "settings.appearance": "Appearance",
    "settings.models": "Models",
    "settings.providers": "Providers",
    "settings.notifications": "Notifications",
    "settings.customEndpoints": "Custom endpoints",
    "lang.switch": "Switch language",
  },
};

export function loadLanguage(): Language {
  try {
    const raw = globalThis.localStorage?.getItem(STORAGE_KEY);
    if (raw === "zh" || raw === "en") {
      return raw;
    }
  } catch {
    /* ignore */
  }
  return "zh";
}

export function saveLanguage(lang: Language): void {
  try {
    globalThis.localStorage?.setItem(STORAGE_KEY, lang);
  } catch {
    /* ignore */
  }
}

interface I18nContextValue {
  readonly lang: Language;
  readonly setLang: (lang: Language) => void;
  readonly toggleLang: () => void;
  readonly t: (key: string, params?: Record<string, string | number>) => string;
}

const I18nContext = createContext<I18nContextValue | null>(null);

export function I18nProvider({ children }: { children: ReactNode }) {
  const [lang, setLangState] = useState<Language>(() => loadLanguage());

  useEffect(() => {
    document.documentElement.lang = lang === "zh" ? "zh-CN" : "en";
  }, [lang]);

  const setLang = useCallback((next: Language) => {
    setLangState(next);
    saveLanguage(next);
  }, []);

  const toggleLang = useCallback(() => {
    setLangState((current) => {
      const next = current === "zh" ? "en" : "zh";
      saveLanguage(next);
      return next;
    });
  }, []);

  const t = useCallback(
    (key: string, params?: Record<string, string | number>) => {
      let text = MESSAGES[lang][key] ?? MESSAGES[lang === "zh" ? "en" : "zh"][key] ?? key;
      if (params) {
        for (const [k, v] of Object.entries(params)) {
          text = text.replaceAll(`{${k}}`, String(v));
        }
      }
      return text;
    },
    [lang],
  );

  const value = useMemo<I18nContextValue>(
    () => ({ lang, setLang, toggleLang, t }),
    [lang, setLang, toggleLang, t],
  );

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

export function useI18n(): I18nContextValue {
  const ctx = useContext(I18nContext);
  if (!ctx) {
    return { lang: "zh", setLang: () => {}, toggleLang: () => {}, t: (k) => k };
  }
  return ctx;
}