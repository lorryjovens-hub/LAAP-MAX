"""Pydantic v2 数据模型 - 类型安全的意识接口"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class Framework(str, Enum):
    REACT = "react"
    VUE = "vue"
    SVELTE = "svelte"
    VANILLA = "vanilla"
    NEXT = "next"
    NUXT = "nuxt"


class StyleSystem(str, Enum):
    TAILWIND = "tailwind"
    CSS_MODULES = "css-modules"
    STYLED_COMPONENTS = "styled-components"
    SCSS = "scss"
    VANILLA_CSS = "vanilla-css"


class AnimationPreference(str, Enum):
    AUTO = "auto"  # 从视频自动提取
    MINIMAL = "minimal"
    RICH = "rich"
    NONE = "none"


class ReplicationRequest(BaseModel):
    """用户复现请求配置"""
    framework: Framework = Field(default=Framework.REACT, description="目标前端框架")
    style_system: StyleSystem = Field(default=StyleSystem.TAILWIND, description="样式系统")
    animation: AnimationPreference = Field(default=AnimationPreference.AUTO, description="动画偏好")
    responsive: bool = Field(default=True, description="是否生成响应式布局")
    accessibility: bool = Field(default=True, description="是否包含无障碍支持")
    component_library: Optional[str] = Field(default=None, description="UI 组件库，如 shadcn/ui")
    output_format: str = Field(default="zip", description="输出格式: zip, git-repo")
    custom_instructions: Optional[str] = Field(default=None, description="额外自定义指令")
    
    # 高级约束
    max_colors: int = Field(default=12, ge=3, le=24, description="最大颜色数")
    max_font_families: int = Field(default=3, ge=1, le=5, description="最大字体族数")
    target_lighthouse_score: int = Field(default=90, ge=70, le=100, description="目标 Lighthouse 分数")


class ReplicationResponse(BaseModel):
    """任务提交响应"""
    task_id: str = Field(..., description="唯一任务 ID")
    status: str = Field(..., description="任务状态")
    message: str = Field(..., description="状态说明")
    estimated_seconds: int = Field(..., description="预计完成秒数")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class TaskStatus(str, Enum):
    QUEUED = "queued"
    PERCEIVING = "perceiving"  # 视觉感知中
    REASONING = "reasoning"    # 架构推理中
    GENERATING = "generating"  # 代码生成中
    VERIFYING = "verifying"    # 视觉回归验证中
    REVISING = "revising"      # 自修正中
    COMPLETED = "completed"
    FAILED = "failed"


class DesignToken(BaseModel):
    """设计令牌 - 审美的原子单位"""
    name: str = Field(..., description="令牌名称")
    value: str = Field(..., description="令牌值")
    type: str = Field(..., description="类型: color, spacing, font, radius, shadow")
    semantics: str = Field(..., description="语义描述")
    usage: List[str] = Field(default_factory=list, description="使用场景")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="提取置信度")


class VisualComponent(BaseModel):
    """视觉组件节点 - 布局树的基本单元"""
    id: str = Field(..., description="组件唯一 ID")
    type: str = Field(..., description="组件类型: hero, navbar, card, button, text, image, container")
    bounding_box: Dict[str, float] = Field(..., description="{x, y, width, height} 相对坐标")
    z_index: int = Field(default=0, description="视觉层级")
    prominence: float = Field(default=0.0, ge=0.0, le=100.0, description="视觉权重")
    tokens: List[str] = Field(default_factory=list, description="引用的设计令牌")
    children: List["VisualComponent"] = Field(default_factory=list, description="子组件")
    animations: List[Dict[str, Any]] = Field(default_factory=list, description="动画参数")
    interactions: List[Dict[str, Any]] = Field(default_factory=list, description="交互定义")
    text_content: Optional[str] = Field(default=None, description="文本内容（OCR）")
    image_url: Optional[str] = Field(default=None, description="图片资源 URL")


class LayoutGrid(BaseModel):
    """布局网格系统"""
    type: str = Field(..., description="grid, flex, absolute")
    columns: Optional[int] = Field(default=None, description="Grid 列数")
    gap: str = Field(default="0", description="间距")
    breakpoints: Dict[str, str] = Field(default_factory=dict, description="响应式断点")


class AnimationSpec(BaseModel):
    """动画规范 - 从视频提取的物理参数"""
    name: str = Field(..., description="动画名称")
    trigger: str = Field(..., description="触发条件: hover, click, scroll, load, auto")
    duration: float = Field(..., description="持续时间 ms")
    easing: str = Field(..., description="缓动函数")
    properties: List[str] = Field(..., description="动画属性: opacity, transform, scale, translate")
    keyframes: List[Dict[str, Any]] = Field(default_factory=list, description="关键帧定义")
    confidence: float = Field(default=0.9, ge=0.0, le=1.0)


class ReplicationResult(BaseModel):
    """最终复现结果"""
    task_id: str
    status: TaskStatus
    design_tokens: List[DesignToken] = Field(default_factory=list)
    component_tree: Optional[VisualComponent] = Field(default=None)
    layout_grid: Optional[LayoutGrid] = Field(default=None)
    animations: List[AnimationSpec] = Field(default_factory=list)
    code_package: Optional[str] = Field(default=None, description="代码包路径")
    preview_url: Optional[str] = Field(default=None, description="预览 URL")
    visual_similarity_score: float = Field(default=0.0, description="视觉相似度")
    lighthouse_score: Optional[Dict[str, float]] = Field(default=None)
    revision_count: int = Field(default=0, description="修正轮数")
    completed_at: Optional[datetime] = Field(default=None)
    error_message: Optional[str] = Field(default=None)


class TaskProgress(BaseModel):
    """任务进度查询"""
    task_id: str
    status: TaskStatus
    progress_percent: int = Field(..., ge=0, le=100)
    current_stage: str = Field(..., description="当前阶段描述")
    logs: List[str] = Field(default_factory=list, description="执行日志")
    result: Optional[ReplicationResult] = Field(default=None)
