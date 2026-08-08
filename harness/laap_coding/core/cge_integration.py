from __future__ import annotations

"""
cge_integration.py — CGE 与现有 harness 架构的集成点
====================================================

集成模式:
  1. harness.py 的 7 层架构在每个关键阶段调用 CGE
  2. harness_composer.py 从 CGE 读取几何状态渲染到 UI
  3. assembly_engine.py 使用 CGE 的多尺度归纳调度

集成不是侵入式的——CGE 作为观察者/建议者存在，
不影响现有流程的正常执行，只在检测到异常时分发告警。
"""

import logging
import time
from typing import Optional, Dict, Any

# 尝试导入 CGE，不阻塞已有功能

try:
    import sys, os
    _core_dir = os.path.dirname(os.path.abspath(__file__))
    if _core_dir not in sys.path:
        sys.path.insert(0, _core_dir)
    from cognitive_geometry import (
        CognitiveGeometryEngine,
        CognitiveTube,
        StickyClass,
    )
    CGE_AVAILABLE = True
except ImportError:
    CGE_AVAILABLE = False
    CognitiveGeometryEngine = object
    # 为类型注解提供桩
    class CognitiveTube: pass
    class StickyClass:
        STICKY = "sticky"
        SEMI_WELL_SPACED = "semi"
        FAR_FROM_STICKY = "far"


logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# 1. harness.py 集成点 — 注入 7 层架构
# ═══════════════════════════════════════════════════════════════

class CGEHarnessBridge:
    """CGE 与 7 层 harness 架构的桥接层。
    
    每层的调用点:
    感知层:   ingest_task → 注册新的认知管
    记忆层:   build_convex_sets → 从记忆库构建凸集
    推理层:   detect_sticky → 检查是否进入粘性模式
    决策层:   consult_geometry → 获取维度建议
    执行层:   multiscale_schedule → 使用多尺度调度
    验证层:   verify_dimension → 验证维度完整性
    反馈层:   update_model → 更新几何模型
    """
    
    def __init__(self):
        if not CGE_AVAILABLE:
            logger.warning("CGE not available, bridge running in stub mode")
            self.engine = None
            self.enabled = False
            return
        
        self.engine = CognitiveGeometryEngine(density_threshold=1.5)
        self.engine.initialize()
        self.enabled = True
        self._session_start = time.time()
    
    # ── 感知层: 任务注入 ──
    
    def on_perceive_task(self, task_id: str, agent_id: str,
                         direction: tuple, thickness: float,
                         resource_estimate: float = 1.0) -> Optional[CognitiveTube]:
        """感知层调用: 将检测到的任务注入 CGE。
        
        对应 harness.py PerceptionLayer.parse_task() 的调用点。
        """
        if not self.enabled:
            return None
        return self.engine.ingest_task(
            task_id, agent_id, direction, thickness, resource_estimate
        )
    
    # ── 记忆层: 凸集构建 ──
    
    def on_memory_retrieve(self, memory_context: Dict) -> None:
        """记忆层调用: 从记忆上下文更新凸集。
        
        当记忆层检索到新的语义模式时，更新凸集划分。
        对应 harness.py MemoryLayer.query_pattern() 的调用点。
        """
        if not self.enabled:
            return
        
        # 如果记忆上下文包含新的语义簇，注册为新凸集
        for cluster in memory_context.get("semantic_clusters", []):
            cid = cluster.get("id")
            if cid and cid not in self.engine.monitor.convex_sets:
                from .cognitive_geometry import ConvexSet
                self.engine.monitor.convex_sets[cid] = ConvexSet(
                    set_id=cid,
                    label=cluster.get("label", cid),
                    centroid=tuple(cluster.get("centroid", [0, 0, 0])),
                    volume=cluster.get("volume", 1.0),
                    radius=cluster.get("radius", 0.5),
                )
    
    # ── 推理层: 粘性检测 ──
    
    def on_reason_check(self) -> Dict:
        """推理层调用: 检查是否进入粘性模式。
        
        如果检测到粘性，返回归约计划供推理层选择。
        对应 harness.py ReasoningLayer.analyze() 的调用点。
        """
        if not self.enabled:
            return {"sticky": False, "reason": "cge_disabled"}
        
        report = self.engine.detector.detect()
        result = {
            "sticky": report.classification == StickyClass.STICKY,
            "classification": report.classification.value,
            "dominant_convex": report.dominant_convex_set,
            "overlap_ratio": round(report.overlap_ratio, 3),
            "action": report.suggested_action,
        }
        
        if report.classification == StickyClass.STICKY:
            plan = self.engine.detector.build_reduction_plan(report)
            result["reduction_plan"] = plan
        
        return result
    
    # ── 决策层: 维度健康度 ──
    
    def on_decide_geometry(self) -> Dict:
        """决策层调用: 获取几何维建议。
        
        返回当前维度健康度，供质量门控和风险仪表盘决策。
        对应 harness.py DecisionLayer.evaluate() 的调用点。
        """
        if not self.enabled:
            return {"health": "unknown"}
        
        dim_report = self.engine.reporter.report()
        return {
            "health": dim_report["health"],
            "dimension": dim_report["minkowski_dimension"],
            "delta_max": dim_report["delta_max"],
            "multiplicity": dim_report["multiplicity"],
            "warning": dim_report["warning"],
            "theorem_check": dim_report["kakeya_theorem_status"],
        }
    
    # ── 执行层: 多尺度调度 ──
    
    def on_execute_schedule(self, tasks: list) -> Dict:
        """执行层调用: 生成多尺度调度计划。
        
        将 task 列表按资源粒度分层，生成归纳调度。
        对应 harness.py ExecutionLayer.invoke_tools() 的调用点。
        """
        if not self.enabled or not tasks:
            return {"plan": "direct"}
        
        tubes = []
        for t in tasks:
            tube = self.engine.ingest_task(
                task_id=t.get("id", str(time.time())),
                agent_id=t.get("agent", "default"),
                direction=tuple(t.get("direction", [0, 0, 0])),
                thickness=t.get("thickness", 0.01),
                resource_estimate=t.get("resource", 1.0),
            )
            tubes.append(tube)
        
        plan = self.engine.scheduler.schedule(tubes)
        return {
            "scale_levels": len(plan.scales),
            "assignment": plan.assignment,
            "expected_volume": round(plan.expected_volume, 6),
            "warnings": plan.warnings,
        }
    
    # ── 验证层: 维度完整性验证 ──
    
    def on_verify_dimension(self, required_dim: float = 2.5) -> bool:
        """验证层调用: 检查认知空间维度完整性。
        
        如果当前维度低于 required_dim，认为验证失败。
        对应 harness.py VerificationLayer.validate() 的调用点。
        """
        if not self.enabled:
            return True
        
        dim = self.engine.reporter.estimate_minkowski_dimension()
        return dim >= required_dim
    
    # ── 反馈层: 更新几何模型 ──
    
    def on_feedback_learn(self, outcome: Dict) -> None:
        """反馈层调用: 根据任务结果更新几何模型。
        
        如果任务完成，标记对应管子的状态。
        如果任务失败或超时，可能意味着凸集划分需要调整。
        对应 harness.py FeedbackLayer.learn() 的调用点。
        """
        if not self.enabled:
            return
        
        task_id = outcome.get("task_id")
        status = outcome.get("status", "done")
        
        if task_id and task_id in self.engine.monitor.tubes:
            self.engine.monitor.tubes[task_id].status = status
            self.engine.monitor.tubes[task_id].completed_at = time.time()
    
    # ── 全量扫描 ──
    
    def full_scan(self) -> Dict:
        """全量几何扫描。
        
        返回可以在风险仪表盘或质量门控中展示的完整报告。
        """
        if not self.enabled:
            return {"enabled": False}
        
        scan = self.engine.full_scan()
        scan["uptime"] = round(time.time() - self._session_start, 1)
        return scan


# ═══════════════════════════════════════════════════════════════
# 2. harness_composer.py 集成点 — UI 感知几何状态
# ═══════════════════════════════════════════════════════════════

class CGEComposerExtension:
    """为 HarnessComposer 添加认知几何感知能力。
    
    在生成的页面中嵌入几何健康度指示器：
    - 维度仪表 (Dimension Gauge)
    - Δ_max 状态条
    - 粘性告警
    
    使用方式:
        composer = HarnessComposer()
        ext = CGEComposerExtension(composer, cge_bridge)
        page = ext.with_geometry_dashboard(spec)
    """
    
    def __init__(self, composer, bridge: CGEHarnessBridge):
        self.composer = composer
        self.bridge = bridge
    
    def generate_geometry_injections(self) -> Dict[str, str]:
        """生成注入到页面中的几何状态 HTML。
        
        Returns:
            {"nav_badge": ..., "footer_status": ..., "debug_panel": ...}
        """
        if not self.bridge.enabled:
            return {}
        
        feed = self.bridge.engine.get_composer_feed()
        dim = feed["dimension"]
        health = feed["health"]
        dmax = feed["delta_max"]
        mu = feed["mu"]
        
        # 颜色编码
        color_map = {
            "healthy": "#4A6B4A",
            "degraded": "#9D5F4D",
            "at_risk": "#8B2C1F",
            "critical": "#8B2C1F",
        }
        bar_color = color_map.get(health, "#537D96")
        
        nav_badge = f'''
        <div style="display:inline-flex;align-items:center;gap:4px;
                    padding:2px 8px;font-size:0.7rem;font-weight:500;
                    border-radius:4px;background:rgba({83 if health=='healthy' else 139},{125 if health=='healthy' else 44},{150 if health=='healthy' else 31},0.08);
                    color:{bar_color};font-family:system-ui">
          dim {dim}
          <span style="width:6px;height:6px;border-radius:50%;
                       background:{bar_color};opacity:0.7"></span>
        </div>'''
        
        debug_panel = f'''
        <div id="cge-panel" style="position:fixed;bottom:16px;right:16px;
             padding:12px 16px;border-radius:4px;
             background:var(--bg-card);border:0.5px solid var(--border);
             font-size:0.75rem;font-family:system-ui;z-index:9999;
             color:var(--text-muted);min-width:160px">
          <div style="font-weight:500;color:var(--accent);margin-bottom:6px">cge status</div>
          <div style="display:flex;justify-content:space-between;gap:12px">
            <span>dim</span><span style="font-variant-numeric:tabular-nums">{dim}</span>
          </div>
          <div style="display:flex;justify-content:space-between">
            <span>health</span><span style="color:{bar_color}">{health}</span>
          </div>
          <div style="display:flex;justify-content:space-between">
            <span>&Delta;<sub>max</sub></span><span style="font-variant-numeric:tabular-nums">{dmax}</span>
          </div>
          <div style="display:flex;justify-content:space-between">
            <span>&mu;</span><span style="font-variant-numeric:tabular-nums">{mu}</span>
          </div>
          <div style="margin-top:6px;height:3px;background:rgba(0,0,0,0.06);border-radius:1px;overflow:hidden">
            <div style="height:100%;width:{min(100, dmax * 50)}%;background:{bar_color};border-radius:1px"></div>
          </div>
          <div style="font-size:0.65rem;color:var(--text-tertiary);margin-top:4px">
            &Delta; &le; C &rArr; &mu; &le; C&prime;
          </div>
        </div>'''
        
        return {
            "nav_badge": nav_badge,
            "debug_panel": debug_panel,
            "footer_status": f'dim {dim} · {health}',
        }


# ═══════════════════════════════════════════════════════════════
# 3. 集成演示: 一个完整的 CGE 检测流程
# ═══════════════════════════════════════════════════════════════

def demo_cge_detection_flow():
    """演示 CGE 如何在 harness 管线中运行的示例。
    
    模拟一个逐步递增的 task 注入 → 粘性检测 → 降级调度的流程。
    """
    if not CGE_AVAILABLE:
        print("CGE not available. Install cognitive_geometry.py first.")
        return
    
    bridge = CGEHarnessBridge()
    print("=" * 60)
    print("CGE 集成演示: 挂谷感知的 agent 编排管线")
    print("=" * 60)
    
    import math
    import random
    random.seed(42)
    
    # Phase 1: 注入少量任务 —— 健康状态
    print("\n[Phase 1] 注入 20 条正常 task (3D 方向均匀分布)")
    for i in range(20):
        # 斐波那契球面均匀采样
        golden_ratio = (1 + 5 ** 0.5) / 2
        theta = math.acos(1 - 2 * (i + 0.5) / 20)
        phi = 2 * math.pi * i / golden_ratio
        direction = (math.sin(theta) * math.cos(phi),
                     math.sin(theta) * math.sin(phi),
                     math.cos(theta))
        bridge.on_perceive_task(
            f"task_{i}", "worker_a",
            direction=direction,
            thickness=0.01,
            resource_estimate=1.0,
        )
    
    scan = bridge.full_scan()
    print(f"  Δ_max = {scan['delta_max']}")
    print(f"  μ = {scan['multiplicity']}")
    print(f"  维度 = {scan['minkowski_dimension']}")
    print(f"  粘性分类 = {scan['sticky_classification']}")
    print(f"  健康度 = {scan['health']}")
    
    # Phase 2: 注入大量集中在同一方向的 task —— 触发粘性
    print("\n[Phase 2] 注入 80 条方向高度集中的 task (模拟粘性)")
    for i in range(80):
        # 全部指向 (0.99, 0.1, 0.05) 方向 (3D)
        dir_vec = (0.99, 0.1, 0.05)
        norm = math.sqrt(sum(c**2 for c in dir_vec))
        direction = tuple(c / norm for c in dir_vec)
        bridge.on_perceive_task(
            f"sticky_task_{i}", "worker_b",
            direction=direction,
            thickness=0.01,
            resource_estimate=1.0,
        )
    
    scan = bridge.full_scan()
    print(f"  Δ_max = {scan['delta_max']}")
    print(f"  μ = {scan['multiplicity']}")
    print(f"  维度 = {scan['minkowski_dimension']}")
    print(f"  粘性分类 = {scan['sticky_classification']}")
    print(f"  健康度 = {scan['health']}")
    print(f"  建议动作 = {scan.get('action', '')}")
    
    # 检测结果
    reason_result = bridge.on_reason_check()
    if reason_result.get("sticky"):
        print(f"  粘性告警! 主导凸集: {reason_result.get('dominant_convex')}")
        print(f"  归约计划: {reason_result.get('reduction_plan', {}).get('action', '')}")
    
    # Phase 3: 多尺度调度
    print("\n[Phase 3] 多尺度归纳调度")
    tasks = [{"id": f"bulk_{i}", "agent": "worker",
              "direction": (0.99, 0.1, 0), "thickness": 0.01,
              "resource": 1.0} for i in range(50)]
    schedule = bridge.on_execute_schedule(tasks)
    print(f"  尺度层级: {schedule['scale_levels']}")
    print(f"  预期并集体积: {schedule['expected_volume']}")
    if schedule.get("warnings"):
        for w in schedule["warnings"]:
            print(f"  警告: {w}")
    
    # Phase 4: 验证维度
    print(f"\n[Phase 4] 维度验证 (要求 ≥ 2.5)")
    valid = bridge.on_verify_dimension(required_dim=2.5)
    print(f"  验证结果: {'通过' if valid else '失败 — 维度坍缩风险'}")
    
    print("\n" + "=" * 60)
    print("核心定理: Δ_max(T) ≤ 1.5  ⇒  μ(T) ≤ 1.5")
    print(f"当前: Δ_max = {scan['delta_max']}, μ = {scan['multiplicity']}")
    print("=" * 60)


if __name__ == "__main__":
    demo_cge_detection_flow()
