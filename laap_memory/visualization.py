"""
laap_memory/visualization.py — 记忆图谱可视化

生成 SVG 格式的记忆图谱，用于快速了解记忆状态。
支持：
- 记忆图谱：节点 = 记忆，边 = 关联
- 分布直方图：按类型、重要性分布
- 热点图：高频访问记忆
- 生命线：时间轴上的记忆分布
- 导出为 HTML/SVG
"""

from __future__ import annotations

import json
import math
import time
from typing import Optional

from .models import MemoryEntry, MemoryType
from .vault import MemoryVault


class MemoryVisualizer:
    """记忆可视化引擎"""

    def __init__(self, vault: MemoryVault):
        self.vault = vault

    def render_graph_svg(self, entity_id: str = "",
                         max_nodes: int = 30,
                         width: int = 700,
                         height: int = 500) -> str:
        """渲染记忆关联图谱为 SVG

        节点颜色 = 记忆类型
        边颜色 = 关联类型
        节点大小 = 重要性
        """
        entries = self.vault.retrieve(entity_id=entity_id, limit=max_nodes)

        if not entries:
            return self._empty_graph(width, height)

        # 类型颜色
        type_colors = {
            "conversation": "#537D96",
            "semantic": "#1B365D",
            "episode": "#9D5F4D",
            "self": "#4A6B4A",
            "reflection": "#8B2C1F",
            "relationship": "#8F867B",
            "procedural": "#6B6158",
        }

        # 布局：简单圆形布局
        center_x = width // 2
        center_y = height // 2
        radius = min(width, height) * 0.35
        n = len(entries)

        nodes = []
        for i, entry in enumerate(entries):
            angle = 2 * math.pi * i / n - math.pi / 2
            x = center_x + radius * math.cos(angle)
            y = center_y + radius * math.sin(angle)
            node_size = 4 + entry.importance * 10
            color = type_colors.get(entry.type.value, "#537D96")
            nodes.append({
                "id": entry.id[:8],
                "x": x, "y": y,
                "r": node_size,
                "color": color,
                "label": entry.content[:30],
                "type": entry.type.value,
                "importance": entry.importance,
            })

        # 边
        edges = []
        seen_pairs = set()
        for node in nodes:
            assocs = self.vault.get_associations(node["id"])
            for a in assocs:
                target_id = a.target_id[:8] if a.source_id == node["id"] else a.source_id[:8]
                pair = tuple(sorted([node["id"], target_id]))
                if pair not in seen_pairs:
                    seen_pairs.add(pair)
                    edge_color = {
                        "similar": "#537D96", "follows": "#4A6B4A",
                        "causes": "#8B2C1F", "responds": "#9D5F4D",
                    }.get(a.relation_type, "#D8CFBE")
                    opacity = 0.3 + a.weight * 0.7
                    # 找到目标节点位置
                    target_node = next((n2 for n2 in nodes if n2["id"] == target_id), None)
                    if target_node:
                        edges.append({
                            "x1": node["x"], "y1": node["y"],
                            "x2": target_node["x"], "y2": target_node["y"],
                            "color": edge_color, "opacity": opacity,
                        })

        # 渲染 SVG
        svg_parts = [
            f'<svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" role="img">',
            f'<title>Memory graph for {entity_id or "all"}</title>',
            f'<desc>{len(entries)} memories, {len(edges)} associations</desc>',
            '<style>text{font-family:system-ui,sans-serif;font-size:10px;fill:#4A433C}</style>',
        ]

        # 边
        for e in edges:
            svg_parts.append(
                f'<line x1="{e["x1"]:.0f}" y1="{e["y1"]:.0f}" '
                f'x2="{e["x2"]:.0f}" y2="{e["y2"]:.0f}" '
                f'stroke="{e["color"]}" stroke-width="0.8" opacity="{e["opacity"]:.2f}"/>'
            )

        # 节点
        for node in nodes:
            svg_parts.append(
                f'<circle cx="{node["x"]:.0f}" cy="{node["y"]:.0f}" '
                f'r="{node["r"]:.1f}" fill="{node["color"]}" opacity="0.8"/>'
            )
            # 标签
            svg_parts.append(
                f'<text x="{node["x"]:.0f}" y="{node["y"] + node["r"] + 12:.0f}" '
                f'text-anchor="middle">{node["label"]}</text>'
            )

        # 图例
        legend_y = height - 20
        x_offset = 20
        for t, c in [("conv", "#537D96"), ("sem", "#1B365D"), ("ep", "#9D5F4D"),
                      ("rel", "#4A6B4A"), ("ref", "#8B2C1F"), ("relshp", "#8F867B")]:
            svg_parts.append(
                f'<circle cx="{x_offset}" cy="{legend_y}" r="3" fill="{c}"/>'
                f'<text x="{x_offset + 8}" y="{legend_y + 3}" font-size="9">{t}</text>'
            )
            x_offset += 50

        svg_parts.append('</svg>')
        return "\n".join(svg_parts)

    def render_histogram_svg(self, entity_id: str = "",
                             width: int = 600, height: int = 300) -> str:
        """渲染记忆类型分布直方图"""
        entries = self.vault.retrieve(entity_id=entity_id, limit=500)
        if not entries:
            return self._empty_graph(width, height)

        # 按类型统计
        type_counts: dict[str, int] = {}
        for e in entries:
            type_counts[e.type.value] = type_counts.get(e.type.value, 0) + 1

        type_colors = {
            "conversation": "#537D96", "semantic": "#1B365D",
            "episode": "#9D5F4D", "self": "#4A6B4A",
            "reflection": "#8B2C1F", "relationship": "#8F867B",
            "procedural": "#6B6158",
        }

        types = sorted(type_counts.keys())
        max_count = max(type_counts.values())
        bar_width = min(60, (width - 60) / max(len(types), 1))
        gap = 10

        svg_parts = [
            f'<svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" role="img">',
            '<style>text{font-family:system-ui,sans-serif;font-size:11px;fill:#4A433C}</style>',
        ]

        for i, t in enumerate(types):
            count = type_counts[t]
            bar_h = (count / max_count) * (height - 60) if max_count > 0 else 0
            x = 40 + i * (bar_width + gap)
            y = height - 30 - bar_h
            color = type_colors.get(t, "#537D96")

            svg_parts.append(
                f'<rect x="{x:.0f}" y="{y:.0f}" width="{bar_width:.0f}" '
                f'height="{bar_h:.0f}" fill="{color}" rx="2" opacity="0.8"/>'
            )
            svg_parts.append(
                f'<text x="{x + bar_width / 2:.0f}" y="{height - 12}" '
                f'text-anchor="middle" font-size="9">{t[:5]}</text>'
            )
            svg_parts.append(
                f'<text x="{x + bar_width / 2:.0f}" y="{y - 5}" '
                f'text-anchor="middle" font-size="9">{count}</text>'
            )

        svg_parts.append('</svg>')
        return "\n".join(svg_parts)

    def render_timeline_svg(self, entity_id: str = "",
                            width: int = 700, height: int = 200) -> str:
        """渲染记忆时间线"""
        entries = self.vault.retrieve(entity_id=entity_id, limit=100)
        if not entries:
            return self._empty_graph(width, height)

        entries = sorted(entries, key=lambda e: e.created_at)
        if len(entries) < 2:
            return self._empty_graph(width, height)

        t_min = entries[0].created_at
        t_max = entries[-1].created_at
        t_range = max(t_max - t_min, 1)

        svg_parts = [
            f'<svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" role="img">',
            '<style>text{font-family:system-ui,sans-serif;font-size:10px;fill:#4A433C}</style>',
            f'<line x1="20" y1="{height/2}" x2="{width-20}" y2="{height/2}" '
            f'stroke="#D8CFBE" stroke-width="1"/>',
        ]

        for e in entries:
            x = 20 + (e.created_at - t_min) / t_range * (width - 40)
            y = height / 2
            r = 2 + e.importance * 5
            color = {
                "conversation": "#537D96", "semantic": "#1B365D",
                "episode": "#9D5F4D", "self": "#4A6B4A",
                "reflection": "#8B2C1F", "relationship": "#8F867B",
            }.get(e.type.value, "#537D96")

            y_offset = -15 if e.importance > 0.5 else 15
            svg_parts.append(
                f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r:.1f}" '
                f'fill="{color}" opacity="0.7"/>'
            )
            if e.importance > 0.7:
                ts = time.strftime("%m-%d", time.localtime(e.created_at))
                svg_parts.append(
                    f'<text x="{x:.0f}" y="{y + y_offset:.0f}" '
                    f'text-anchor="middle" font-size="8">{ts}</text>'
                )

        svg_parts.append('</svg>')
        return "\n".join(svg_parts)

    def render_importance_svg(self, entity_id: str = "",
                              width: int = 600, height: int = 200) -> str:
        """渲染重要性分布气泡图"""
        entries = self.vault.retrieve(entity_id=entity_id, limit=50)
        if not entries:
            return self._empty_graph(width, height)

        # 按重要性排序
        entries = sorted(entries, key=lambda e: -e.importance)

        svg_parts = [
            f'<svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" role="img">',
            '<style>text{font-family:system-ui,sans-serif;font-size:9px;fill:#4A433C}</style>',
        ]

        # 绘制气泡
        x, y = 30, 30
        max_row_h = 0
        for entry in entries[:30]:
            r = max(8, entry.importance * 25 + 5)
            if x + r * 2 > width - 20:
                x = 30
                y += max_row_h + 10
                max_row_h = 0
            if y + r > height - 10:
                break

            color = {
                "conversation": "#537D96", "semantic": "#1B365D",
                "episode": "#9D5F4D", "self": "#4A6B4A",
                "reflection": "#8B2C1F", "relationship": "#8F867B",
            }.get(entry.type.value, "#537D96")

            opacity = 0.3 + entry.importance * 0.5
            svg_parts.append(
                f'<circle cx="{x + r:.0f}" cy="{y + r:.0f}" r="{r:.0f}" '
                f'fill="{color}" opacity="{opacity:.2f}"/>'
            )
            # 短标签
            label = entry.content[:6]
            svg_parts.append(
                f'<text x="{x + r:.0f}" y="{y + r + 3:.0f}" '
                f'text-anchor="middle" font-size="8">{label}</text>'
            )

            x += r * 2 + 8
            max_row_h = max(max_row_h, r * 2)

        svg_parts.append('</svg>')
        return "\n".join(svg_parts)

    def render_full_dashboard(self, entity_id: str = "") -> str:
        """渲染完整仪表盘（多图组合）"""
        graph = self.render_graph_svg(entity_id, max_nodes=20, width=600, height=400)
        hist = self.render_histogram_svg(entity_id, width=600, height=250)
        timeline = self.render_timeline_svg(entity_id, width=600, height=150)
        importance = self.render_importance_svg(entity_id, width=600, height=200)

        stats = self.vault.stats()
        total = stats.get("total_memories", 0)
        assocs = stats.get("associations", 0)

        html = f"""<div style="font-family:system-ui,sans-serif;color:#2A2622;max-width:650px">
<h2 style="font-size:1.1rem;font-weight:500;border-left:2px solid #537D96;padding-left:8px;margin:0 0 0.5rem">Memory Dashboard</h2>
<div style="display:flex;gap:12px;margin-bottom:1rem;font-size:0.85rem">
  <span>{total} memories</span>
  <span>{assocs} associations</span>
  <span>{stats.get('archived',0)} archived</span>
</div>
{graph}
<div style="display:flex;gap:12px;margin-top:0.5rem;flex-wrap:wrap">
<div style="flex:1;min-width:280px">{hist}</div>
<div style="flex:1;min-width:280px">{importance}</div>
</div>
<div style="margin-top:0.5rem">{timeline}</div>
</div>"""
        return html

    def _empty_graph(self, width: int, height: int) -> str:
        return f'<svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" role="img"><text x="{width/2}" y="{height/2}" text-anchor="middle" font-family="system-ui" font-size="14" fill="#999">No memories yet</text></svg>'