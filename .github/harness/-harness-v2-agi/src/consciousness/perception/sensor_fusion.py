"""感知融合层 - 多器官信号加权整合

遵循 Harness 第一性原理：
- 截图视觉 vs 爬虫结构冲突时，爬虫优先（实时性更高）
- 多器官一致时，置信度加权提升
- 所有冲突记录日志供审计
"""

from typing import Any, Dict, List, Optional, Tuple

from src.api.models import PerceptionModality, PerceptionSignal
from src.utils.logger import get_logger

# 颜色名称到 HEX 的基础映射表（中英双语）
COLOR_NAME_TO_HEX: Dict[str, str] = {
    "red": "#ff0000", "红色": "#ff0000",
    "blue": "#0000ff", "蓝色": "#0000ff",
    "green": "#008000", "绿色": "#008000",
    "yellow": "#ffff00", "黄色": "#ffff00",
    "purple": "#800080", "紫色": "#800080",
    "orange": "#ffa500", "橙色": "#ffa500",
    "pink": "#ffc0cb", "粉色": "#ffc0cb",
    "black": "#000000", "黑色": "#000000",
    "white": "#ffffff", "白色": "#ffffff",
    "gray": "#808080", "灰色": "#808080",
    "grey": "#808080",
}

# 对齐容忍阈值：RGB 三通道差平方和上限，超过则视为颜色名与 HEX 无关
# 经验值：每通道允许差 ~100（100² × 3 = 30000）
_COLOR_ALIGN_MAX_DISTANCE: float = 30000.0


class SensorFusion:
    """
    感知融合层 - 多器官信号加权整合

    遵循 Harness 第一性原理：
    - 截图视觉 vs 爬虫结构冲突时，爬虫优先（实时性更高）
    - 多器官一致时，置信度加权提升
    - 所有冲突记录日志供审计
    """

    def __init__(self) -> None:
        self.logger = get_logger("perception.sensor_fusion")
        # 模态权重：爬虫最高（实时性），视觉次之，视频再次
        self.modality_weights: Dict[PerceptionModality, float] = {
            PerceptionModality.CRAWLER: 0.9,
            PerceptionModality.VISION: 0.7,
            PerceptionModality.VIDEO: 0.6,
            PerceptionModality.LAYOUT: 0.5,
            PerceptionModality.INTERNAL: 0.3,
        }

    async def fuse(self, signals: List[PerceptionSignal]) -> Dict[str, Any]:
        """
        主入口：融合多个感知信号，输出统一感知表征

        Returns:
            {
                "design_tokens": List[Dict],  # 融合后的设计令牌
                "tech_stack": List[Dict],     # 技术栈（仅爬虫有）
                "content_structure": Dict,    # 内容结构
                "layout": Dict,               # 布局
                "confidence": float,          # 综合置信度
                "sources": List[str],         # 信号来源列表
                "conflicts": List[Dict],      # 冲突记录
            }
        """
        self.logger.info(f"开始融合 {len(signals)} 个感知信号")

        if not signals:
            self.logger.warning("收到空信号列表，返回空融合结果")
            return {
                "design_tokens": [],
                "tech_stack": [],
                "content_structure": {},
                "layout": {},
                "confidence": 0.0,
                "sources": [],
                "conflicts": [],
            }

        # 1. 跨模态语义对齐（如视觉颜色名 → HEX）
        aligned_signals = self._align_modalities(signals)

        # 2. 检测冲突（审计用）
        conflicts = self._detect_conflicts(aligned_signals)
        if conflicts:
            self.logger.info(f"检测到 {len(conflicts)} 个信号冲突，已记录审计")

        # 3. 加权融合
        merged = self._weighted_merge(aligned_signals)

        # 4. 综合置信度
        confidence = self._compute_overall_confidence(aligned_signals, conflicts)

        sources = [s.source for s in aligned_signals]

        result: Dict[str, Any] = {
            "design_tokens": merged["design_tokens"],
            "tech_stack": merged["tech_stack"],
            "content_structure": merged["content_structure"],
            "layout": merged["layout"],
            "confidence": confidence,
            "sources": sources,
            "conflicts": conflicts,
        }

        self.logger.info(
            f"融合完成: {len(result['design_tokens'])} 设计令牌, "
            f"{len(result['tech_stack'])} 技术栈, 置信度={confidence:.3f}"
        )
        return result

    def _weighted_merge(self, signals: List[PerceptionSignal]) -> Dict[str, Any]:
        """
        按 confidence * modality_weight 加权整合信号

        冲突解决策略：
        - 设计令牌冲突（如颜色）：爬虫优先，若多爬虫冲突则取置信度最高
        - 技术栈：仅爬虫模态有，直接合并去重
        - 内容结构：取置信度最高的信号
        - 布局：合并多源信号，冲突时爬虫优先
        """
        # 1. 设计令牌：以 (name, type) 为键合并，冲突时按 score 排序取最高
        token_state: Dict[Tuple[str, str], Dict[str, Any]] = {}
        for sig in signals:
            tokens = sig.payload.get("design_tokens", []) or []
            sig_score = sig.confidence * self.modality_weights.get(sig.modality, 0.5)
            for tok in tokens:
                tok_dict = _to_dict(tok)
                key = (tok_dict.get("name", ""), tok_dict.get("type", ""))
                tok_score = float(tok_dict.get("confidence", 1.0)) * sig_score
                if key not in token_state:
                    token_state[key] = {
                        "best": tok_dict,
                        "best_score": tok_score,
                        "sources": [sig.source],
                        "agree_count": 1,
                    }
                else:
                    state = token_state[key]
                    state["sources"].append(sig.source)
                    # 一致性提升：值相同则累加 agree_count
                    if tok_dict.get("value") == state["best"].get("value"):
                        state["agree_count"] += 1
                    # 取高分者覆盖（保留累积来源与 agree_count）
                    if tok_score > state["best_score"]:
                        state["best"] = tok_dict
                        state["best_score"] = tok_score

        design_tokens: List[Dict[str, Any]] = []
        for state in token_state.values():
            # 多器官一致时，置信度加权提升
            final_score = state["best_score"] + 0.05 * (state["agree_count"] - 1)
            token = dict(state["best"])
            token["confidence"] = min(1.0, final_score)
            token["sources"] = list(state["sources"])
            design_tokens.append(token)

        # 2. 技术栈：仅爬虫模态有，按 name 去重，保留最高 confidence
        tech_state: Dict[str, Dict[str, Any]] = {}
        for sig in signals:
            if sig.modality != PerceptionModality.CRAWLER:
                continue
            techs = sig.payload.get("tech_stack", []) or []
            sig_score = sig.confidence * self.modality_weights.get(sig.modality, 0.5)
            for tech in techs:
                tech_dict = _to_dict(tech)
                name = tech_dict.get("name", "")
                tech_score = float(tech_dict.get("confidence", 1.0)) * sig_score
                if name not in tech_state:
                    tech_state[name] = {
                        "best": tech_dict,
                        "best_score": tech_score,
                        "sources": [sig.source],
                    }
                else:
                    state = tech_state[name]
                    state["sources"].append(sig.source)
                    if tech_score > state["best_score"]:
                        state["best"] = tech_dict
                        state["best_score"] = tech_score

        tech_stack: List[Dict[str, Any]] = []
        for state in tech_state.values():
            tech = dict(state["best"])
            tech["confidence"] = min(1.0, state["best_score"])
            tech["sources"] = list(state["sources"])
            tech_stack.append(tech)

        # 3. 内容结构：取置信度最高（confidence * modality_weight）的信号
        best_content: Dict[str, Any] = {}
        best_content_score = -1.0
        for sig in signals:
            content = sig.payload.get("content_structure")
            if not content:
                continue
            score = sig.confidence * self.modality_weights.get(sig.modality, 0.5)
            if score > best_content_score:
                best_content_score = score
                best_content = content if isinstance(content, dict) else _to_dict(content)

        # 4. 布局：合并所有信号，关键字段冲突时爬虫优先
        layout: Dict[str, Any] = {}
        # 按模态权重倒序：爬虫优先填充
        sorted_signals = sorted(
            signals,
            key=lambda s: -self.modality_weights.get(s.modality, 0.5),
        )
        for sig in sorted_signals:
            sig_layout = sig.payload.get("layout") or sig.payload.get("layout_analysis")
            if not sig_layout:
                continue
            layout_dict = sig_layout if isinstance(sig_layout, dict) else _to_dict(sig_layout)
            for k, v in layout_dict.items():
                if k not in layout or layout.get(k) in (None, "", {}):
                    layout[k] = v
                elif sig.modality == PerceptionModality.CRAWLER:
                    # 爬虫覆盖其他模态
                    layout[k] = v

        return {
            "design_tokens": design_tokens,
            "tech_stack": tech_stack,
            "content_structure": best_content,
            "layout": layout,
        }

    def _align_modalities(
        self, signals: List[PerceptionSignal]
    ) -> List[PerceptionSignal]:
        """
        跨模态语义对齐

        示例：
        - 视觉信号说"主色是蓝色"（描述性）
        - 爬虫信号说"主色 #635BFF"（精确值）
        - 对齐后：视觉信号的 payload 也带 HEX 值

        实现策略：
        1. 找到所有信号的 design_tokens
        2. 对于视觉信号中颜色名为"blue"/"红色"等的令牌，从爬虫信号中找最近的 HEX
        3. 更新视觉信号的 payload，附加 hex_value 字段
        """
        # 收集爬虫信号的所有 HEX 颜色令牌
        crawler_hex_colors: List[Tuple[str, str]] = []  # [(name, hex), ...]
        for sig in signals:
            if sig.modality != PerceptionModality.CRAWLER:
                continue
            tokens = sig.payload.get("design_tokens", []) or []
            for tok in tokens:
                tok_dict = _to_dict(tok)
                if tok_dict.get("type") == "color":
                    val = str(tok_dict.get("value", "")).strip()
                    if _is_hex_color(val):
                        crawler_hex_colors.append(
                            (tok_dict.get("name", ""), val.lower())
                        )

        if not crawler_hex_colors:
            return list(signals)

        aligned: List[PerceptionSignal] = []
        for sig in signals:
            if sig.modality != PerceptionModality.VISION:
                aligned.append(sig)
                continue

            # 深拷贝 payload 以避免修改输入
            new_payload: Dict[str, Any] = {k: v for k, v in sig.payload.items()}
            tokens = new_payload.get("design_tokens", []) or []
            new_tokens: List[Any] = []
            for tok in tokens:
                tok_dict = _to_dict(tok)
                if tok_dict.get("type") == "color":
                    val = str(tok_dict.get("value", "")).strip().lower()
                    # 视觉信号的值是颜色名称（在 COLOR_NAME_TO_HEX 中）
                    if val in COLOR_NAME_TO_HEX:
                        matched_hex = self._match_hex_for_name(val, crawler_hex_colors)
                        if matched_hex is not None:
                            aligned_tok = dict(tok_dict)
                            aligned_tok["hex_value"] = matched_hex
                            new_tokens.append(aligned_tok)
                            continue
                new_tokens.append(tok_dict)
            new_payload["design_tokens"] = new_tokens
            aligned.append(
                PerceptionSignal(
                    modality=sig.modality,
                    payload=new_payload,
                    confidence=sig.confidence,
                    source=sig.source,
                    timestamp=sig.timestamp,
                )
            )

        return aligned

    def _detect_conflicts(
        self, signals: List[PerceptionSignal]
    ) -> List[Dict[str, Any]]:
        """
        检测信号冲突，记录供审计

        冲突类型：
        - color_mismatch: 同名令牌在不同信号中值不同
        - tech_stack_mismatch: 不同爬虫信号检测到不同技术栈
        - layout_mismatch: 布局结构冲突

        返回冲突列表：[{"type": "color_mismatch", "token": "primary", "values": ["#fff", "#000"], "sources": ["vision", "crawler"]}]
        """
        conflicts: List[Dict[str, Any]] = []

        # 1. 设计令牌冲突：按 (name, type) 分组，同组内 value 不同则记录冲突
        token_group: Dict[Tuple[str, str], List[Tuple[str, str, str]]] = {}
        for sig in signals:
            tokens = sig.payload.get("design_tokens", []) or []
            for tok in tokens:
                tok_dict = _to_dict(tok)
                name = tok_dict.get("name", "")
                ttype = tok_dict.get("type", "")
                value = str(tok_dict.get("value", "")).strip().lower()
                key = (name, ttype)
                token_group.setdefault(key, []).append(
                    (value, sig.source, sig.modality.value)
                )

        for (name, ttype), entries in token_group.items():
            unique_values = list({v for v, _, _ in entries})
            if len(unique_values) > 1:
                values_list = [v for v, _, _ in entries]
                sources_list = [s for _, s, _ in entries]
                modalities = list({m for _, _, m in entries})
                conflicts.append(
                    {
                        "type": "color_mismatch" if ttype == "color" else "token_mismatch",
                        "token": name,
                        "token_type": ttype,
                        "values": values_list,
                        "sources": sources_list,
                        "modalities": modalities,
                    }
                )
                self.logger.debug(
                    f"令牌冲突: {name}({ttype}) 唯一值={unique_values} 来源={sources_list}"
                )

        # 2. 技术栈冲突：不同爬虫信号检测到不同技术栈名称
        crawler_signals = [s for s in signals if s.modality == PerceptionModality.CRAWLER]
        if len(crawler_signals) > 1:
            per_signal_names: List[Tuple[str, set]] = []
            for sig in crawler_signals:
                techs = sig.payload.get("tech_stack", []) or []
                names = {
                    _to_dict(tech).get("name", "") for tech in techs
                }
                per_signal_names.append((sig.source, names))

            # 两两比较，找出独有技术栈
            for i, (src_i, names_i) in enumerate(per_signal_names):
                for j, (src_j, names_j) in enumerate(per_signal_names):
                    if i >= j:
                        continue
                    only_i = names_i - names_j
                    only_j = names_j - names_i
                    if only_i or only_j:
                        conflicts.append(
                            {
                                "type": "tech_stack_mismatch",
                                "sources": [src_i, src_j],
                                "only_in_source_1": sorted(only_i),
                                "only_in_source_2": sorted(only_j),
                            }
                        )
                        self.logger.debug(
                            f"技术栈冲突: {src_i} 独有 {sorted(only_i)}, "
                            f"{src_j} 独有 {sorted(only_j)}"
                        )

        # 3. 布局冲突：不同模态对布局关键字段的不一致
        layout_per_signal: List[Tuple[str, str, Dict[str, Any]]] = []
        for sig in signals:
            sig_layout = sig.payload.get("layout") or sig.payload.get("layout_analysis")
            if sig_layout and isinstance(sig_layout, dict):
                layout_per_signal.append((sig.source, sig.modality.value, sig_layout))

        if len(layout_per_signal) > 1:
            all_keys: set = set()
            for _, _, layout_dict in layout_per_signal:
                all_keys.update(layout_dict.keys())
            for key in all_keys:
                values_per_source: List[Tuple[str, str, Any]] = []
                for src, mod, layout_dict in layout_per_signal:
                    if key in layout_dict:
                        values_per_source.append((src, mod, layout_dict[key]))
                unique_vals = {str(v) for _, _, v in values_per_source}
                if len(unique_vals) > 1:
                    conflicts.append(
                        {
                            "type": "layout_mismatch",
                            "field": key,
                            "values": [v for _, _, v in values_per_source],
                            "sources": [src for src, _, _ in values_per_source],
                            "modalities": [mod for _, mod, _ in values_per_source],
                        }
                    )

        return conflicts

    def _compute_overall_confidence(
        self,
        signals: List[PerceptionSignal],
        conflicts: List[Dict[str, Any]],
    ) -> float:
        """综合置信度：模态加权均值 - 冲突惩罚"""
        if not signals:
            return 0.0
        total_weight = 0.0
        weighted_sum = 0.0
        for sig in signals:
            w = self.modality_weights.get(sig.modality, 0.5)
            total_weight += w
            weighted_sum += sig.confidence * w
        if total_weight == 0:
            return 0.0
        base_confidence = weighted_sum / total_weight
        # 冲突惩罚：每个冲突降低 0.02，最多 0.2
        penalty = min(0.2, len(conflicts) * 0.02)
        return max(0.0, min(1.0, base_confidence - penalty))

    def _match_hex_for_name(
        self,
        color_name: str,
        crawler_hex_colors: List[Tuple[str, str]],
    ) -> Optional[str]:
        """
        根据颜色名在爬虫 HEX 颜色中找最接近的

        Args:
            color_name: 颜色名（如 "blue" / "蓝色"）
            crawler_hex_colors: [(token_name, hex), ...] 来自爬虫信号

        Returns:
            最接近的 HEX 字符串（小写），若超出容忍阈值则返回 None
        """
        base_hex = COLOR_NAME_TO_HEX.get(color_name.lower())
        if base_hex is None:
            return None
        base_rgb = _hex_to_rgb(base_hex)
        if base_rgb is None:
            return None

        best_hex: Optional[str] = None
        best_dist: float = float("inf")
        for _, hex_val in crawler_hex_colors:
            rgb = _hex_to_rgb(hex_val)
            if rgb is None:
                continue
            # RGB 三通道差的平方和
            dist = float(sum((a - b) ** 2 for a, b in zip(base_rgb, rgb)))
            if dist < best_dist:
                best_dist = dist
                best_hex = hex_val

        # 阈值过滤：若所有爬虫 HEX 距离都很远，则不强行对齐
        if best_hex is not None and best_dist <= _COLOR_ALIGN_MAX_DISTANCE:
            return best_hex
        return None


# ---------------------------------------------------------------------------
# 模块级辅助函数
# ---------------------------------------------------------------------------


def _to_dict(obj: Any) -> Dict[str, Any]:
    """将令牌对象统一转换为 dict（兼容 Pydantic 模型与普通对象）"""
    if isinstance(obj, dict):
        return dict(obj)
    # Pydantic v2
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    # Pydantic v1 / 兼容
    if hasattr(obj, "dict"):
        try:
            return obj.dict()
        except Exception:
            pass
    if hasattr(obj, "__dict__"):
        return dict(obj.__dict__)
    return {"value": str(obj)}


def _is_hex_color(value: str) -> bool:
    """判断字符串是否为 HEX 颜色（#rgb 或 #rrggbb）"""
    if not value:
        return False
    v = value.strip().lower()
    if v.startswith("#"):
        v = v[1:]
    if len(v) not in (3, 6):
        return False
    try:
        int(v, 16)
        return True
    except ValueError:
        return False


def _hex_to_rgb(hex_value: str) -> Optional[Tuple[int, int, int]]:
    """HEX → RGB 元组"""
    v = hex_value.strip().lower()
    if v.startswith("#"):
        v = v[1:]
    if len(v) == 3:
        v = "".join(c * 2 for c in v)
    if len(v) != 6:
        return None
    try:
        r = int(v[0:2], 16)
        g = int(v[2:4], 16)
        b = int(v[4:6], 16)
        return (r, g, b)
    except ValueError:
        return None
