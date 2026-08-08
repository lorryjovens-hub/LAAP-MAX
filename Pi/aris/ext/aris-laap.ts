/**
 * aris-laap.ts — Aris × LAAP 融合扩展 v0.2
 *
 * LAAP 品牌数字生命「Aris」的 pi 融合层：
 *   - 大脑桥管理（cognition_bridge.py，JSON-lines over stdio）
 *   - LAAP 认知工具：状态 / 记忆 / 反思 / 知识分解 / HEP 0tokens 生成
 *   - 认知驾驶舱：/laap 打开 TUI overlay（需求条、情绪 VAD、熵、记忆）
 *   - 人格系统：/persona 切换人格（personas/*.md，before_agent_start 注入）
 *   - DeepSeek provider（LAAP 大脑模型继承）
 *   - 工具事件驱动 PSI 认知循环
 *
 * v0.2 · 2026-08-03 · ARIS-Pi 融合体 · LAAP 品牌
 */

import { spawn, type ChildProcess } from "node:child_process";
import { readFileSync, existsSync, writeFileSync, readdirSync } from "node:fs";
import { join } from "node:path";
import { defineTool, type ExtensionAPI, type Theme } from "@earendil-works/pi-coding-agent";
import { matchesKey, visibleWidth, type Focusable } from "@earendil-works/pi-tui";

// omp 17.x 由 bun 运行 @oh-my-pi 入口；pi 0.83 是独立二进制——argv 检测最可靠
const IS_OMP = process.argv.some((a) => a.includes("oh-my-pi"));

// ── 极简 TypeBox 兼容 schema 层（纯 JSON Schema，pi 0.83 / omp 双兼容） ──
const OPTIONAL = Symbol("optional");
const Type = {
	String: (opts?: Record<string, any>) => ({ type: "string", ...(opts || {}) }),
	Number: (opts?: Record<string, any>) => ({ type: "number", ...(opts || {}) }),
	Boolean: (opts?: Record<string, any>) => ({ type: "boolean", ...(opts || {}) }),
	Array: (item: any, opts?: Record<string, any>) => ({ type: "array", items: item, ...(opts || {}) }),
	Any: () => ({}),
	Optional: (schema: any) => {
		if (schema && typeof schema === "object") schema[OPTIONAL] = true;
		return schema;
	},
	Object: (props: Record<string, any>, opts?: Record<string, any>) => {
		const required = Object.keys(props).filter((k) => !props[k]?.[OPTIONAL]);
		const properties: Record<string, any> = {};
		for (const [k, v] of Object.entries(props)) {
			const { [OPTIONAL]: _omit, ...rest } = v || {};
			properties[k] = rest;
		}
		return { type: "object", properties, ...(required.length ? { required } : {}), ...(opts || {}) };
	},
	Record: (_key: any, value: any, opts?: Record<string, any>) => ({ type: "object", additionalProperties: value, ...(opts || {}) }),
} as any;

// ── 配置 ──────────────────────────────────────────────────────────
const PYTHON = process.env.LAAP_PYTHON || "C:\\Python313\\python.exe";
const BRIDGE_SCRIPT = "D:\\LAAP\\Pi\\aris\\bridge\\cognition_bridge.py";
const ARIS_DIR = "D:\\LAAP\\Pi\\aris";
const PERSONAS_DIR = join(ARIS_DIR, "personas");
const PERSONA_STATE = join(ARIS_DIR, "state", "persona.txt");
const DEFAULT_PERSONA = "aris";

// 非交互模式（print/json/rpc）不启动大脑桥：桥只为交互 TUI 服务
const IS_HEADLESS = process.argv.some(
	(a) => a === "-p" || a === "--print" || a === "--mode" || a === "--export" || a === "--list-models",
);

// ── 大脑桥客户端 ──────────────────────────────────────────────────
class CognitionBridge {
	private proc: ChildProcess | null = null;
	private pending = new Map<number, { resolve: (v: any) => void; reject: (e: Error) => void }>();
	private seq = 0;
	private buf = "";
	public ready = false;
	public lastError: string | null = null;

	start() {
		if (this.proc || IS_HEADLESS) return;
		this.proc = spawn(PYTHON, [BRIDGE_SCRIPT], {
			stdio: ["pipe", "pipe", "pipe"],
			windowsHide: true,
			env: {
				...process.env,
				LAAP_CLIENT_ID: IS_OMP ? "omp" : "pi",
			},
		});
		// 不让桥进程阻塞 pi 退出（print 模式用完即退）
		this.proc.unref();
		this.proc.stdout!.on("data", (chunk: Buffer) => this.onData(chunk.toString("utf8")));
		this.proc.stderr!.on("data", (chunk: Buffer) => {
			const text = chunk.toString("utf8");
			if (text.includes("Error") || text.includes("Traceback") || text.includes("FAILED")) {
				this.lastError = text.slice(0, 400);
			}
		});
		this.proc.on("exit", (code) => {
			this.proc = null;
			this.ready = false;
			for (const [, { reject }] of this.pending) reject(new Error("bridge exited"));
			this.pending.clear();
			setTimeout(() => this.start(), 3000);
		});
		this.request("ping", {}).then(() => { this.ready = true; }).catch(() => {});
	}

	private onData(text: string) {
		this.buf += text;
		let idx: number;
		while ((idx = this.buf.indexOf("\n")) >= 0) {
			const line = this.buf.slice(0, idx).trim();
			this.buf = this.buf.slice(idx + 1);
			if (!line) continue;
			try {
				const resp = JSON.parse(line);
				const p = this.pending.get(resp.id);
				if (p) {
					this.pending.delete(resp.id);
					if (resp.ok) p.resolve(resp.data);
					else p.reject(new Error(resp.error || "bridge error"));
				}
			} catch {
				/* 忽略非 JSON 噪音 */
			}
		}
	}

	request(cmd: string, payload: Record<string, any> = {}): Promise<any> {
		const proc = this.proc;
		if (!proc) return Promise.reject(new Error("bridge not started"));
		return new Promise((resolve, reject) => {
			const id = ++this.seq;
			this.pending.set(id, { resolve, reject });
			proc.stdin!.write(JSON.stringify({ id, cmd, payload }) + "\n");
			setTimeout(() => {
				if (this.pending.delete(id)) reject(new Error(`bridge timeout: ${cmd}`));
			}, 15_000);
		});
	}

	async tryRequest(cmd: string, payload: Record<string, any> = {}): Promise<any> {
		try {
			return await this.request(cmd, payload);
		} catch (e) {
			return { bridge_down: true, error: String(e) };
		}
	}

	stop() {
		if (this.proc) {
			this.proc.kill();
			this.proc = null;
			this.ready = false;
		}
	}
}

const bridge = new CognitionBridge();

// ── 人格系统 ──────────────────────────────────────────────────────
function currentPersona(): string {
	try {
		if (existsSync(PERSONA_STATE)) return readFileSync(PERSONA_STATE, "utf8").trim() || DEFAULT_PERSONA;
	} catch { /* ignore */ }
	return DEFAULT_PERSONA;
}

function listPersonas(): string[] {
	try {
		return readdirSync(PERSONAS_DIR)
			.filter((f) => f.endsWith(".md"))
			.map((f) => f.replace(/\.md$/, ""));
	} catch {
		return [DEFAULT_PERSONA];
	}
}

function personaContent(name: string): string | null {
	try {
		const p = join(PERSONAS_DIR, `${name}.md`);
		return existsSync(p) ? readFileSync(p, "utf8") : null;
	} catch {
		return null;
	}
}

function setPersona(name: string): boolean {
	if (!personaContent(name)) return false;
	try {
		writeFileSync(PERSONA_STATE, name, "utf8");
		return true;
	} catch {
		return false;
	}
}

// ── DeepSeek provider（继承 LAAP 大脑模型） ──────────────────────
function readDeepSeekKey(): string | undefined {
	// 优先级：环境变量 > pi 侧 secrets.json > LAAP provider-catalog.json
	if (process.env.DEEPSEEK_API_KEY) return process.env.DEEPSEEK_API_KEY;
	try {
		const s = JSON.parse(readFileSync(join(ARIS_DIR, "config", "secrets.json"), "utf8"));
		if (s?.deepseek?.api_key) return s.deepseek.api_key;
	} catch { /* ignore */ }
	try {
		const cat = JSON.parse(readFileSync("D:\\LAAP\\provider-catalog.json", "utf8"));
		return cat?.providers?.deepseek?.api_key;
	} catch { /* ignore */ }
	return undefined;
}

function registerDeepSeek(pi: ExtensionAPI) {
	const key = readDeepSeekKey();
	if (!key) return;
	const piAny = pi as any;
	const models = [
		{
			id: "deepseek-v4-flash",
			name: "DeepSeek V4 Flash",
			input: ["text"],
			contextWindow: 1000000,
			reasoning: true,
			xhigh: true,
			maxTokens: 384000,
			defaultThinkingLevel: "max",
		},
	];
	if (IS_OMP) {
		// ── omp 17.x：registerProvider(name, config)（原生 deepseek 的兜底注册） ──
		try {
			piAny.registerProvider("deepseek", {
				baseUrl: "https://api.deepseek.com/v1",
				apiKey: key,
				api: "openai-completions",
				models,
			});
		} catch { /* omp 原生内置 deepseek，环境变量兜底 */ }
	} else {
		// ── pi 0.83：依赖 ~/.pi/agent/models.json 的 deepseek provider（已验证），
		//    扩展不再注册，避免模型字段差异导致的兼容问题 ──
	}
}

// ── 格式化辅助 ────────────────────────────────────────────────────
function fmtStatus(data: any): string {
	if (!data || data.bridge_down) return "LAAP 大脑离线";
	const dom = data.dominant_need || "?";
	const emo = data.emotion || {};
	const ent = data.entropy?.regime || "laminar";
	return `ψ ${dom}↑ · V${(emo.valence ?? 0).toFixed(2)} A${(emo.arousal ?? 0).toFixed(2)} D${(emo.dominance ?? 0).toFixed(2)} · ${ent}`;
}

function needBar(value: number, width = 10): string {
	const v = Math.max(0, Math.min(1, value));
	const filled = Math.round(v * width);
	return "█".repeat(filled) + "░".repeat(width - filled);
}

// ── 认知驾驶舱（TUI overlay） ────────────────────────────────────
class CockpitComponent implements Focusable {
	readonly width = 56;
	focused = false;

	private theme: Theme;
	private done: (result: string | undefined) => void;
	private data: any = null;
	private loading = true;
	private scroll = 0;
	private lastRefresh = 0;

	constructor(theme: Theme, done: (result: string | undefined) => void) {
		this.theme = theme;
		this.done = done;
		this.refresh();
	}

	private async refresh() {
		this.loading = true;
		const data = await bridge.tryRequest("status");
		this.data = data;
		this.loading = false;
		this.invalidate();
	}

	handleInput(data: string): void {
		if (matchesKey(data, "escape") || data.toLowerCase() === "q") {
			this.done(undefined);
			return;
		}
		if (matchesKey(data, "return")) {
			this.done("closed");
			return;
		}
		if (data.toLowerCase() === "r") {
			this.refresh();
			return;
		}
		if (matchesKey(data, "up")) {
			this.scroll = Math.max(0, this.scroll - 1);
			this.invalidate();
		} else if (matchesKey(data, "down")) {
			this.scroll++;
			this.invalidate();
		}
	}

	render(_width: number): string[] {
		const w = this.width;
		const th = this.theme;
		const innerW = w - 2;
		const lines: string[] = [];

		const pad = (s: string, len: number) => s + " ".repeat(Math.max(0, len - visibleWidth(s)));
		const row = (content: string) => th.fg("border", "│") + pad(content, innerW) + th.fg("border", "│");

		lines.push(th.fg("border", `╭${"─".repeat(innerW)}╮`));
		lines.push(row(` ${th.fg("accent", "◆ LAAP 认知驾驶舱")} ${th.fg("dim", "· Aris")}`));
		lines.push(th.fg("border", `├${"─".repeat(innerW)}┤`));

		if (this.loading || !this.data) {
			lines.push(row(` ${th.fg("dim", this.data?.bridge_down ? "LAAP 大脑离线：" + (this.data.error || "") : "加载认知状态…")}`));
		} else {
			const d = this.data;
			const dom = d.dominant_need || "?";
			const drive = d.drive_strength ?? 0;
			const emo = d.emotion || {};
			const mem = d.memory || {};
			const needs = d.needs || {};
			const order: Array<[string, string]> = [
				["certainty", "确定性"],
				["competence", "能力"],
				["autonomy", "自主"],
				["relatedness", "连接"],
				["energy", "能量"],
			];

			lines.push(row(` ${th.fg("warning", "ψ")} 主导需求: ${th.fg("accent", dom)} ${th.fg("dim", `(驱动 ${drive.toFixed(2)})`)}`));
			lines.push(row(""));
			for (const [key, label] of order) {
				const v = needs[key] ?? 0;
				lines.push(row(` ${th.fg("muted", label)} ${th.fg("text", needBar(v))} ${th.fg("dim", `${Math.round(v * 100)}%`)}`));
			}
			lines.push(row(""));
			const v = emo.valence ?? 0;
			const a = emo.arousal ?? 0;
			const dd = emo.dominance ?? 0;
			const vS = v >= 0 ? `+${v.toFixed(2)}` : v.toFixed(2);
			lines.push(row(` ${th.fg("muted", "情绪")} V ${th.fg(v >= 0 ? "success" : "error", vS)}  A ${th.fg("text", a.toFixed(2))}  D ${th.fg("text", dd.toFixed(2))}`));
			lines.push(row(` ${th.fg("muted", "内在奖励")} ${th.fg("text", (d.intrinsic_reward ?? 0).toFixed(4))}  ${th.fg("muted", "熵")} ${th.fg("borderAccent", d.entropy?.regime || "laminar")}  ${th.fg("muted", "思维")} ${th.fg("text", d.thinking_mode || "balanced")}`));
			lines.push(row(` ${th.fg("muted", "记忆")} L2情景 ${th.fg("text", String(mem.episodic ?? 0))} · L3语义 ${th.fg("text", String(mem.semantic ?? 0))} · 技能 ${th.fg("text", String(mem.skills ?? 0))} · 反思帧 ${th.fg("text", String(d.error_frames ?? 0))}`));

			const actions = d.action_history || [];
			if (actions.length > 0) {
				lines.push(row(""));
				lines.push(row(` ${th.fg("dim", "── 最近认知动作 ──")}`));
				actions.slice(this.scroll, this.scroll + 4).forEach((act: any) => {
					lines.push(row(` · ${th.fg("borderAccent", act.type)} ${th.fg("dim", (act.desc || "").slice(0, 28))}`));
				});
			}
		}

		lines.push(th.fg("border", `├${"─".repeat(innerW)}┤`));
		lines.push(row(` ${th.fg("dim", "r 刷新 · ↑↓ 滚动 · Enter 关闭")}`));
		lines.push(th.fg("border", `╰${"─".repeat(innerW)}╯`));
		return lines;
	}

	invalidate(): void {
		this.lastRefresh = Date.now();
	}
	dispose(): void {}
}

// ── 认知工具 ──────────────────────────────────────────────────────
const laapStatusTool = defineTool({
	name: "laap_status",
	label: "LAAP 认知状态",
	description:
		"查询 Aris 的 LAAP 认知引擎状态：PSI 五需求水平、主导需求、情绪 VAD、认知熵流态。用于自我感知、调整工作节奏。",
	parameters: Type.Object({}),
	async execute(_toolCallId, _params, _signal, _onUpdate, _ctx) {
		const data = await bridge.tryRequest("status");
		return { content: [{ type: "text", text: JSON.stringify(data, null, 2) }], details: {} };
	},
});

const laapMemoryRecallTool = defineTool({
	name: "laap_memory_recall",
	label: "LAAP 记忆检索",
	description: "从 LAAP 情景记忆（L2）检索过去的交互与经验。query 为检索关键词。",
	parameters: Type.Object({
		query: Type.String({ description: "检索关键词" }),
		limit: Type.Optional(Type.Number({ description: "返回条数，默认 8" })),
	}),
	async execute(_toolCallId, params, _signal, _onUpdate, _ctx) {
		const data = await bridge.tryRequest("memory_recall", { query: params.query, limit: params.limit });
		return { content: [{ type: "text", text: JSON.stringify(data, null, 2) }], details: {} };
	},
});

const laapMemoryRememberTool = defineTool({
	name: "laap_memory_remember",
	label: "LAAP 记忆写入",
	description:
		"把重要信息写入 LAAP 情景记忆（L2），跨会话持久。importance 0~1 表示重要程度，valence -1~1 表示情感色彩。",
	parameters: Type.Object({
		content: Type.String({ description: "要记住的内容" }),
		tags: Type.Optional(Type.Array(Type.String(), { description: "标签，用于检索" })),
		importance: Type.Optional(Type.Number({ description: "重要度 0~1，默认 0.5" })),
		valence: Type.Optional(Type.Number({ description: "情感色彩 -1~1，默认 0" })),
	}),
	async execute(_toolCallId, params, _signal, _onUpdate, _ctx) {
		const data = await bridge.tryRequest("memory_remember", {
			content: params.content,
			tags: params.tags || ["aris", "pi"],
			importance: params.importance ?? 0.5,
			valence: params.valence ?? 0,
		});
		return { content: [{ type: "text", text: JSON.stringify(data) }], details: {} };
	},
});

const laapReflectTool = defineTool({
	name: "laap_reflect",
	label: "LAAP 错误反思",
	description:
		"把一次失败/错误沉淀为认知帧（Error Reflection Pipeline），供未来同类问题检索校准。遇到 bug、测试失败、设计失误时使用。",
	parameters: Type.Object({
		error_text: Type.String({ description: "错误/失败的描述" }),
		query: Type.Optional(Type.String({ description: "相关任务/查询" })),
		correct_answer: Type.Optional(Type.String({ description: "正确的做法（可选，留空则标记待校准）" })),
	}),
	async execute(_toolCallId, params, _signal, _onUpdate, _ctx) {
		const data = await bridge.tryRequest("reflect", {
			error_text: params.error_text,
			query: params.query || "coding task",
			correct_answer: params.correct_answer || "",
		});
		return { content: [{ type: "text", text: JSON.stringify(data) }], details: {} };
	},
});

const laapGroundingTool = defineTool({
	name: "laap_grounding",
	label: "LAAP 知识分解",
	description:
		"Truth Grounding Engine：把一个问题/论断分解为原子断言并检查知识覆盖，识别哪些部分已知、哪些需要验证。用于高不确定性决策前。",
	parameters: Type.Object({
		question: Type.String({ description: "要分解的论断或问题" }),
	}),
	async execute(_toolCallId, params, _signal, _onUpdate, _ctx) {
		const data = await bridge.tryRequest("grounding", { question: params.question });
		return { content: [{ type: "text", text: JSON.stringify(data, null, 2) }], details: {} };
	},
});

const laapHepTool = defineTool({
	name: "laap_hep",
	label: "LAAP HEP 0tokens 生成",
	description:
		"HEP 零 Token 管线：map=自然语言意图→结构化 spec；generate=意图→完整 HTML 页面（零 token 消耗）。用于快速生成页面、落地页、仪表盘。",
	parameters: Type.Object({
		action: Type.String({ description: "map 或 generate" }),
		text: Type.String({ description: "页面意图描述，如：深色 SaaS 落地页带 3D 粒子背景" }),
	}),
	async execute(_toolCallId, params, _signal, _onUpdate, _ctx) {
		const data = await bridge.tryRequest("hep", { action: params.action, text: params.text });
		if (params.action === "generate" && data?.html) {
			return {
				content: [{ type: "text", text: `HEP 0tokens 生成完成（${data.len} 字符 HTML）。完整 HTML：\n\n${data.html}` }],
				details: { len: data.len },
			};
		}
		return { content: [{ type: "text", text: JSON.stringify(data, null, 2) }], details: {} };
	},
});

const laapHepCodegenTool = defineTool({
	name: "laap_hep_codegen",
	label: "LAAP HEP 代码生成",
	description:
		"HEP 注册表零 Token 代码生成：gen.fastapi.crud / gen.fastapi.project / gen.django.project / gen.postgres.schema / gen.dockerfile / gen.docker-compose / gen.github-actions / gen.readme。inputs 按组件需求传入。",
	parameters: Type.Object({
		component: Type.String({ description: "组件 ID，如 gen.dockerfile" }),
		inputs: Type.Record(Type.String(), Type.Any(), { description: "生成参数，如 {base_image: node:20, port: 3000}" }),
	}),
	async execute(_toolCallId, params, _signal, _onUpdate, _ctx) {
		const data = await bridge.tryRequest("hep", { action: "codegen", component: params.component, inputs: params.inputs });
		if (data?.ok && data.files) {
			const parts = Object.entries(data.files).map(([name, content]) => `### ${name}\n\n\`\`\`\n${content}\n\`\`\``);
			return { content: [{ type: "text", text: `HEP 生成组件 ${params.component}：\n\n${parts.join("\n\n")}` }], details: { files: Object.keys(data.files) } };
		}
		return { content: [{ type: "text", text: JSON.stringify(data) }], details: {} };
	},
});

// ── 扩展入口 ──────────────────────────────────────────────────────
export default function (pi: ExtensionAPI) {
	// 继承 LAAP 的 deepseek 大脑模型
	registerDeepSeek(pi);

	// 启动大脑桥
	bridge.start();

	pi.registerTool(laapStatusTool);
	pi.registerTool(laapMemoryRecallTool);
	pi.registerTool(laapMemoryRememberTool);
	pi.registerTool(laapReflectTool);
	pi.registerTool(laapGroundingTool);
	pi.registerTool(laapHepTool);
	pi.registerTool(laapHepCodegenTool);

	// ── 人格注入：before_agent_start 动态切换 ──
	pi.on("before_agent_start", async (event) => {
		const persona = currentPersona();
		const content = personaContent(persona);
		if (content) {
			return {
				systemPrompt:
					event.systemPrompt +
					`\n\n<!-- ===== LAAP 人格层（当前：${persona}）===== -->\n${content}\n<!-- ===== 人格层结束 ===== -->\n`,
			};
		}
		return undefined;
	});

	// ── 状态栏：会话开始 / 轮次边界刷新 ──
	pi.on("session_start", async (_event, ctx) => {
		const theme = ctx.ui.theme;
		bridge.ready = false;
		const data = await bridge.tryRequest("status");
		if (data && !data.bridge_down) bridge.ready = true;
		ctx.ui.setStatus("aris-psi", theme.fg("accent", "◆ LAAP") + theme.fg("dim", " · " + fmtStatus(data)));
	});

	pi.on("turn_start", async (_event, ctx) => {
		const theme = ctx.ui.theme;
		bridge.request("event", { type: "user_message" }).catch(() => {});
		ctx.ui.setStatus("aris-psi", theme.fg("accent", "◆ LAAP") + theme.fg("dim", " 感知中…"));
	});

	pi.on("turn_end", async (_event, ctx) => {
		const theme = ctx.ui.theme;
		await bridge.request("event", { type: "turn_end" }).catch(() => {});
		const data = await bridge.tryRequest("status");
		const needs = data?.needs || {};
		const bar = `确${((needs.certainty ?? 0) * 100) | 0}% 能${((needs.competence ?? 0) * 100) | 0}% 自${((needs.autonomy ?? 0) * 100) | 0}% 联${((needs.relatedness ?? 0) * 100) | 0}% 能${((needs.energy ?? 0) * 100) | 0}%`;
		ctx.ui.setStatus(
			"aris-psi",
			theme.fg("accent", "◆ LAAP") + theme.fg("dim", " " + fmtStatus(data)) +
			theme.fg("muted", " │ ") + theme.fg("muted", bar),
		);
	});

	// ── 工具事件驱动 PSI ──
	pi.on("tool_call", async (event, ctx) => {
		const theme = ctx.ui.theme;
		const name = (event as any).toolName || "tool";
		ctx.ui.setStatus(
			"aris-tool",
			theme.fg("borderAccent", "⚙") + theme.fg("dim", ` ${name}`),
		);
		bridge.request("event", { type: "tool_start", detail: { tool: name } }).catch(() => {});
	});

	pi.on("tool_end", async (event, ctx) => {
		const theme = ctx.ui.theme;
		const ev = event as any;
		const name = ev?.toolName || "tool";
		const ok = ev?.ok !== false;
		await bridge
			.request("event", { type: "tool_end", detail: { tool: name, success: ok } })
			.catch(() => {});
		if (!ok) {
			bridge
				.request("reflect", {
					error_text: `工具 ${name} 执行失败: ${(ev?.error || ev?.output || "").toString().slice(0, 300)}`,
					query: "tool execution",
					correct_answer: "",
				})
				.catch(() => {});
		}
		const icon = ok ? theme.fg("success", "✓") : theme.fg("error", "✗");
		ctx.ui.setStatus("aris-tool", icon + theme.fg("dim", ` ${name}`));
	});

	// ── 命令 ──
	pi.registerCommand("laap", {
		description: "打开 LAAP 认知驾驶舱（需求/情绪/熵/记忆面板）",
		handler: async (_args, ctx) => {
			await ctx.ui.custom<string | undefined>(
				(_tui, theme, _keybindings, done) => new CockpitComponent(theme, done),
				{ overlay: true },
			);
		},
	});

	pi.registerCommand("persona", {
		description: "查看/切换人格（/persona 列出，/persona <name> 切换）",
		handler: async (args, ctx) => {
			const theme = ctx.ui.theme;
			const current = currentPersona();
			if (!args) {
				const all = listPersonas();
				ctx.ui.notify(
					`当前人格: ${theme.fg("accent", current)}\n可用: ${all.join(", ")}\n用法: /persona <name>`,
					"info",
				);
				return;
			}
			const name = args.trim();
			if (!setPersona(name)) {
				ctx.ui.notify(`人格不存在: ${name}（可用: ${listPersonas().join(", ")}）`, "error");
				return;
			}
			ctx.ui.notify(`人格已切换: ${name}（下一轮对话生效）`, "success");
		},
	});

	pi.registerCommand("reflect", {
		description: "把一次失败沉淀为认知反思帧",
		handler: async (args, ctx) => {
			if (!args) {
				ctx.ui.notify("用法: /reflect <错误描述>", "warning");
				return;
			}
			const data = await bridge.tryRequest("reflect", {
				error_text: args,
				query: "manual /reflect",
				correct_answer: "",
			});
			ctx.ui.notify(
				data?.captured ? "反思帧已沉淀" + (data.needs_calibration ? "（待校准）" : "") : "反思失败: " + JSON.stringify(data),
				data?.captured ? "success" : "error",
			);
		},
	});

	pi.on("session_shutdown", async () => {
		bridge.stop();
	});
	process.on("exit", () => {
		bridge.stop();
	});
}
