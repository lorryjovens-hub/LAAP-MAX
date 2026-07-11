"""规划引擎 - 任务分解与依赖图管理"""

import json
from typing import Dict, List, Optional, Set

from src.api.models import AnimationSpec, LayoutGrid, ReplicationRequest, VisualComponent
from src.config import get_settings
from src.llm.client import get_llm_client
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ReplicationPlanner:
    """
    Harness 的推理层 - 任务规划与架构设计
    
    职责：
    1. 将视觉感知结果分解为可执行的代码生成任务
    2. 建立任务依赖图（哪些组件必须先完成）
    3. 资源分配（图片、字体、图标）
    4. 生成技术架构决策（状态管理、路由、API 设计）
    5. 估算复杂度与风险点
    """
    
    def __init__(self):
        self.settings = get_settings()
    
    async def plan(
        self,
        component_tree: VisualComponent,
        layout_grid: LayoutGrid,
        animations: List[AnimationSpec],
        config: ReplicationRequest,
    ) -> Dict[str, any]:
        """
        生成完整的复现执行计划
        
        Returns:
            {
                "tasks": List[Task],          # 原子任务列表
                "dependency_graph": Dict,     # 依赖关系图
                "architecture_decisions": List, # 架构决策记录
                "risk_assessment": Dict,       # 风险评估
                "resource_plan": Dict,         # 资源计划
            }
        """
        logger.info("[Planner] 开始生成复现计划")
        
        # 1. 深度优先遍历组件树，生成任务列表
        tasks = self._decompose_components(component_tree, config)
        
        # 2. 建立依赖图
        dependency_graph = self._build_dependency_graph(tasks, layout_grid)
        
        # 3. 技术架构决策
        architecture_decisions = await self._make_architecture_decisions(
            component_tree, animations, config
        )
        
        # 4. 资源计划
        resource_plan = self._plan_resources(component_tree, animations)
        
        # 5. 风险评估
        risk_assessment = self._assess_risks(tasks, animations, config)
        
        plan = {
            "tasks": tasks,
            "dependency_graph": dependency_graph,
            "architecture_decisions": architecture_decisions,
            "risk_assessment": risk_assessment,
            "resource_plan": resource_plan,
            "estimated_steps": len(tasks),
        }
        
        logger.info(f"[Planner] 计划生成完成: {len(tasks)} 个任务")
        return plan
    
    def _decompose_components(
        self, component: VisualComponent, config: ReplicationRequest
    ) -> List[Dict]:
        """将组件树分解为原子任务"""
        tasks = []
        
        # 遍历组件树，为每个组件生成任务
        def traverse(node: VisualComponent, depth: int = 0):
            task = {
                "id": node.id,
                "type": "component",
                "component_type": node.type,
                "priority": 100 - depth * 10 - int(node.prominence),
                "estimated_tokens": self._estimate_tokens(node),
                "dependencies": [],
                "metadata": {
                    "bounding_box": node.bounding_box,
                    "z_index": node.z_index,
                    "has_children": len(node.children) > 0,
                    "has_animations": len(node.animations) > 0,
                },
            }
            tasks.append(task)
            
            for child in node.children:
                traverse(child, depth + 1)
                # 子组件依赖父组件
                child_task = next((t for t in tasks if t["id"] == child.id), None)
                if child_task:
                    child_task["dependencies"].append(node.id)
        
        traverse(component)
        
        # 添加全局任务
        tasks.append({
            "id": "global-styles",
            "type": "global",
            "component_type": "styles",
            "priority": 200,  # 最高优先级
            "estimated_tokens": 500,
            "dependencies": [],
            "metadata": {"description": "全局样式和设计令牌"},
        })
        
        tasks.append({
            "id": "layout-system",
            "type": "global",
            "component_type": "layout",
            "priority": 190,
            "estimated_tokens": 300,
            "dependencies": ["global-styles"],
            "metadata": {"description": "布局网格系统"},
        })
        
        # 按优先级排序
        tasks.sort(key=lambda x: x["priority"], reverse=True)
        
        return tasks
    
    def _build_dependency_graph(
        self, tasks: List[Dict], layout_grid: LayoutGrid
    ) -> Dict[str, List[str]]:
        """构建任务依赖图"""
        graph = {}
        
        for task in tasks:
            graph[task["id"]] = task["dependencies"].copy()
        
        # 添加布局系统依赖：所有组件依赖布局系统
        for task in tasks:
            if task["type"] == "component" and task["id"] != "layout-system":
                if "layout-system" not in graph[task["id"]]:
                    graph[task["id"]].append("layout-system")
        
        return graph
    
    async def _make_architecture_decisions(
        self,
        component_tree: VisualComponent,
        animations: List[AnimationSpec],
        config: ReplicationRequest,
    ) -> List[Dict]:
        """做出技术架构决策"""
        decisions = []
        
        # 1. 状态管理决策
        has_interactive = any(
            len(node.animations) > 0 or len(node.interactions) > 0
            for node in self._flatten_tree(component_tree)
        )
        
        if has_interactive and config.framework in ["react", "next", "vue", "nuxt"]:
            decisions.append({
                "category": "state_management",
                "decision": "use_hooks" if config.framework in ["react", "next"] else "use_composables",
                "reason": "组件存在交互动画，需要本地状态管理",
                "alternatives": ["redux", "zustand", "pinia"],
            })
        
        # 2. 动画库决策
        if animations:
            has_complex = any(
                len(a.properties) > 2 or a.duration > 1000
                for a in animations
            )
            if has_complex:
                decisions.append({
                    "category": "animation",
                    "decision": "framer-motion",
                    "reason": "存在复杂动画序列，需要声明式动画库",
                    "alternatives": ["gsap", "react-spring"],
                })
            else:
                decisions.append({
                    "category": "animation",
                    "decision": "css-transitions",
                    "reason": "动画较简单，CSS 过渡足够",
                    "alternatives": ["framer-motion"],
                })
        
        # 3. 样式系统决策
        if config.style_system == "tailwind":
            decisions.append({
                "category": "styling",
                "decision": "tailwind-css",
                "reason": "原子化样式，与设计令牌系统天然契合",
                "alternatives": ["css-modules", "styled-components"],
            })
        
        # 4. 图标系统决策
        decisions.append({
            "category": "icons",
            "decision": "lucide-react" if config.framework in ["react", "next"] else "heroicons",
            "reason": "现代、轻量、与设计系统风格一致",
            "alternatives": ["font-awesome", "material-icons"],
        })
        
        # 5. 字体决策
        decisions.append({
            "category": "typography",
            "decision": "next-fonts" if config.framework == "next" else "google-fonts",
            "reason": "优化加载性能，支持字体子集化",
            "alternatives": ["system-fonts"],
        })
        
        return decisions
    
    def _plan_resources(
        self, component_tree: VisualComponent, animations: List[AnimationSpec]
    ) -> Dict:
        """规划资源需求"""
        resources = {
            "images": [],
            "fonts": set(),
            "icons": set(),
            "animations": len(animations),
        }
        
        for node in self._flatten_tree(component_tree):
            if node.image_url:
                resources["images"].append({
                    "id": node.id,
                    "url": node.image_url,
                    "description": f"Component {node.type} image",
                })
            if node.text_content:
                # 检测是否需要特殊字体（简化）
                pass
        
        resources["fonts"] = list(resources["fonts"])
        resources["icons"] = list(resources["icons"])
        
        return resources
    
    def _assess_risks(
        self,
        tasks: List[Dict],
        animations: List[AnimationSpec],
        config: ReplicationRequest,
    ) -> Dict:
        """评估复现风险"""
        risks = []
        
        # 复杂度风险
        total_tokens = sum(t["estimated_tokens"] for t in tasks)
        if total_tokens > 10000:
            risks.append({
                "type": "complexity",
                "level": "high",
                "description": f"总 token 估算 {total_tokens}，超出单次生成能力",
                "mitigation": "采用分阶段生成策略",
            })
        
        # 动画风险
        complex_animations = [a for a in animations if len(a.properties) > 2]
        if len(complex_animations) > 3:
            risks.append({
                "type": "animation",
                "level": "medium",
                "description": f"存在 {len(complex_animations)} 个复杂动画，可能难以精确还原",
                "mitigation": "使用 Framer Motion 或 GSAP 简化实现",
            })
        
        # 框架风险
        if config.framework == "vanilla" and len(tasks) > 20:
            risks.append({
                "type": "framework",
                "level": "medium",
                "description": "Vanilla JS 组件过多，维护困难",
                "mitigation": "建议改用 React 或 Vue",
            })
        
        return {
            "risks": risks,
            "overall_level": "high" if any(r["level"] == "high" for r in risks) else "medium" if risks else "low",
        }
    
    def _estimate_tokens(self, component: VisualComponent) -> int:
        """估算生成该组件所需的 token 数"""
        base = 200
        
        # 根据复杂度调整
        if component.children:
            base += len(component.children) * 100
        if component.animations:
            base += len(component.animations) * 150
        if component.text_content:
            base += len(component.text_content) * 2
        
        return min(base, 2000)  # 上限
    
    def _flatten_tree(self, root: VisualComponent) -> List[VisualComponent]:
        """展平组件树"""
        nodes = [root]
        for child in root.children:
            nodes.extend(self._flatten_tree(child))
        return nodes


import asyncio
