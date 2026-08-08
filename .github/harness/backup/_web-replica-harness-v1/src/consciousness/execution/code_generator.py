"""代码生成器 - 模板驱动 + LLM 填充的混合架构"""

import json
from pathlib import Path
from typing import Dict, List, Optional

from jinja2 import Environment, PackageLoader, select_autoescape

from src.api.models import (
    AnimationSpec,
    DesignToken,
    LayoutGrid,
    ReplicationRequest,
    VisualComponent,
)
from src.config import get_settings
from src.consciousness.memory.design_system import DesignSystemMemory
from src.llm.client import get_llm_client
from src.utils.logger import get_logger

logger = get_logger(__name__)


class CodeGenerator:
    """
    Harness 的执行层 —— 代码生成

    设计原则：
    1. 模板引擎负责 80% 的确定性结构（import、组件骨架、类型定义）
    2. LLM 只填充 20% 的不确定性内容（业务逻辑、文案、复杂样式）
    3. 强制设计令牌映射：LLM 不允许自由书写样式值
    """

    def __init__(self):
        self.settings = get_settings()
        self.jinja = Environment(
            loader=PackageLoader("src", "templates"),
            autoescape=select_autoescape(["html", "xml"]),
        )
        self.design_memory = DesignSystemMemory()

    async def generate(
        self,
        task_plan: Dict,
        component_tree: VisualComponent,
        design_tokens: List[DesignToken],
        layout_grid: LayoutGrid,
        animations: List[AnimationSpec],
        config: ReplicationRequest,
    ) -> Dict[str, str]:
        """生成完整代码包"""
        logger.info("[CodeGenerator] 开始代码生成")

        # 1. 生成全局样式/设计令牌
        global_styles = self._generate_global_styles(design_tokens, config)

        # 2. 生成布局系统
        layout_code = self._generate_layout_system(layout_grid, config)

        # 3. 按依赖顺序生成组件
        components_code = {}
        for task in task_plan["tasks"]:
            if task["type"] == "component":
                code = await self._generate_component(
                    task, component_tree, design_tokens, animations, config
                )
                components_code[task["id"]] = code

        # 4. 生成入口文件
        entry_code = self._generate_entry(component_tree, components_code, config)

        # 5. 组装完整包
        package = {
            "package.json": self._generate_package_json(task_plan, config),
            "globals.css": global_styles,
            "layout.tsx" if config.framework == "next" else "App.jsx": layout_code,
            "components/index.ts": self._generate_component_index(components_code),
            **{f"components/{k}.tsx": v for k, v in components_code.items()},
            "entry": entry_code,
        }

        logger.info(f"[CodeGenerator] 代码生成完成: {len(package)} 个文件")
        return package

    def _generate_global_styles(
        self, tokens: List[DesignToken], config: ReplicationRequest
    ) -> str:
        """生成全局样式文件（CSS Variables / Tailwind Config）"""
        if config.style_system == "tailwind":
            return self._generate_tailwind_config(tokens)
        else:
            return self._generate_css_variables(tokens)

    def _generate_tailwind_config(self, tokens: List[DesignToken]) -> str:
        """生成 Tailwind 配置文件，扩展主题"""
        colors = {}
        font_sizes = {}
        spacing = {}

        for t in tokens:
            if t.type == "color":
                colors[t.name] = t.value
            elif t.type == "font":
                font_sizes[t.name] = t.value
            elif t.type == "spacing":
                spacing[t.name] = t.value

        return f"""import type {{ Config }} from 'tailwindcss';

const config: Config = {{
  content: ['./src/**/*.{html,js,jsx,ts,tsx}'],
  theme: {{
    extend: {{
      colors: {json.dumps(colors, indent=6)},
      fontSize: {json.dumps(font_sizes, indent=6)},
      spacing: {json.dumps(spacing, indent=6)},
    }},
  }},
  plugins: [],
}};

export default config;
"""

    def _generate_css_variables(self, tokens: List[DesignToken]) -> str:
        """生成 CSS 变量文件"""
        lines = [":root {"]
        for t in tokens:
            var_name = f"--{t.name.replace('-', '_')}"
            lines.append(f"  {var_name}: {t.value}; /* {t.semantics} */")
        lines.append("}")
        return "\n".join(lines)

    def _generate_layout_system(self, grid: LayoutGrid, config: ReplicationRequest) -> str:
        """生成布局系统代码"""
        if grid.type == "grid":
            return f"""
export const LayoutGrid = ({{children}}) => (
  <div className="grid grid-cols-1 md:grid-cols-{grid.columns} gap-{grid.gap.replace('px', '')}">
    {{children}}
  </div>
);
"""
        else:
            return """
export const FlexContainer = ({children, direction = 'row'}) => (
  <div className={`flex ${direction === 'column' ? 'flex-col' : 'flex-row'} gap-4`}>
    {children}
  </div>
);
"""

    async def _generate_component(
        self,
        task: Dict,
        tree: VisualComponent,
        tokens: List[DesignToken],
        animations: List[AnimationSpec],
        config: ReplicationRequest,
    ) -> str:
        """生成单个组件代码"""
        node = self._find_node(tree, task["id"])
        if not node:
            return ""

        # 1. 尝试从记忆库获取模板
        template = await self.design_memory.get_component_template(
            node.type, config.framework
        )

        # 2. 构建 LLM 上下文（约束极强的 prompt）
        context = self._build_component_context(node, tokens, animations, config)

        # 3. 调用 LLM 填充（仅填充业务逻辑和结构，样式由 Harness 强制）
        llm = await get_llm_client()
        prompt = f"""
        你是一个严格遵守设计系统的 React 组件生成器。

        【设计令牌约束】（必须严格遵守，禁止自由书写样式值）：
        {json.dumps([t.model_dump() for t in tokens], ensure_ascii=False, indent=2)}

        【组件规范】：
        - 类型: {node.type}
        - 文本内容: {node.text_content or "无"}
        - 视觉权重: {node.prominence}
        - 层级: {node.z_index}

        【动画规范】：
        {json.dumps([a.model_dump() for a in animations if a.trigger in ["hover", "load"]], ensure_ascii=False)}

        【强制规则】：
        1. 必须使用 Tailwind CSS 类名，禁止内联 style
        2. 颜色必须使用设计令牌对应的类名（如 bg-primary, text-surface）
        3. 间距必须是 4 的倍数（4, 8, 12, 16, 24, 32, 48, 64）
        4. 圆角必须使用 rounded-sm, rounded, rounded-lg, rounded-xl 之一
        5. 阴影必须使用 shadow-sm, shadow, shadow-lg 之一
        6. 字体大小必须使用 text-xs, text-sm, text-base, text-lg, text-xl, text-2xl 之一

        请生成完整的 React 组件代码，包含 TypeScript 类型定义。
        """

        try:
            code = await llm.chat_completion(
                messages=[
                    {"role": "system", "content": "你生成的是生产级代码，必须类型安全、可维护。"},
                    {"role": "user", "content": prompt},
                ],
                stage="execution",
                temperature=0.1,
            )

            # 后处理：强制替换自由样式值为设计令牌
            code = self._enforce_design_tokens(code, tokens)
            return code

        except Exception as e:
            logger.error(f"组件生成失败 {task['id']}: {e}")
            return template or self._generate_fallback_component(node, config)

    def _enforce_design_tokens(self, code: str, tokens: List[DesignToken]) -> str:
        """强制将代码中的自由样式值替换为设计令牌"""
        import re

        for t in tokens:
            if t.type == "color":
                code = code.replace(f'"{t.value}"', f'"var(--{t.name})"')

        return code

    def _generate_fallback_component(
        self, node: VisualComponent, config: ReplicationRequest
    ) -> str:
        """生成降级组件"""
        return f"""
export const {node.type.capitalize()} = () => (
  <div className="p-4">
    {{/* Fallback for {node.type} */}}
  </div>
);
"""

    def _generate_entry(
        self, tree: VisualComponent, components: Dict[str, str], config: ReplicationRequest
    ) -> str:
        """生成应用入口"""
        imports = "\n".join([
            f'import {{ {k.capitalize()} }} from "./components/{k}";'
            for k in components.keys()
        ])

        return f"""
{imports}

export default function App() {{
  return (
    <main className="min-h-screen bg-background">
      {{/* 根组件渲染 */}}
    </main>
  );
}}
"""

    def _generate_package_json(self, plan: Dict, config: ReplicationRequest) -> str:
        """生成 package.json"""
        deps = {
            "react": "^18.3.0",
            "react-dom": "^18.3.0",
            "tailwindcss": "^3.4.0",
        }

        for decision in plan.get("architecture_decisions", []):
            if decision["category"] == "animation" and decision["decision"] == "framer-motion":
                deps["framer-motion"] = "^11.0.0"
            if decision["category"] == "icons":
                deps["lucide-react"] = "^0.400.0"

        return json.dumps({
            "name": "web-replica",
            "version": "1.0.0",
            "dependencies": deps,
            "devDependencies": {
                "typescript": "^5.5.0",
                "@types/react": "^18.3.0",
            }
        }, indent=2)

    def _generate_component_index(self, components: Dict[str, str]) -> str:
        """生成组件索引文件"""
        exports = []
        for name in components.keys():
            exports.append(f'export {{ default as {name.capitalize()} }} from "./{name}";')
        return "\n".join(exports)

    def _find_node(self, tree: VisualComponent, node_id: str) -> Optional[VisualComponent]:
        """在组件树中查找节点"""
        if tree.id == node_id:
            return tree
        for child in tree.children:
            found = self._find_node(child, node_id)
            if found:
                return found
        return None

    def _build_component_context(
        self,
        node: VisualComponent,
        tokens: List[DesignToken],
        animations: List[AnimationSpec],
        config: ReplicationRequest,
    ) -> str:
        """构建组件生成的上下文信息"""
        return json.dumps({
            "node": node.model_dump(),
            "tokens": [t.model_dump() for t in tokens],
            "animations": [a.model_dump() for a in animations],
            "framework": config.framework,
        }, ensure_ascii=False)
