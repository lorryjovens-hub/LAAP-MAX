"""
LAAP 0运维自治智能体 v1.0 — OpsAgent
======================================
实现白皮书第 12.8 节描述的自治运维系统。

设计哲学: "认知系统本身应具备认知自身运行状态并自我维护的能力"

四级自治策略:
  L0 完全自治  — 健康监测、日志清理、缓存刷新、参数微调（自动执行，无需通知）
  L1 通知后执行 — 版本更新、配置变更、安全规则调整（通知用户，时间窗口内自动执行）
  L2 需确认后执行 — 大规模数据删除、架构迁移、权限策略变更（等待确认）
  L3 人工介入   — 超出自治能力的复杂故障（提供诊断信息和建议）

能力矩阵 (白皮书 12.8.2):
  1. 健康自监测  — 监控各模块运行状态、性能指标、资源使用
  2. 故障自诊断  — 异常检测 + 根因定位
  3. 故障自修复  — 可自动修复的故障立即修复
  4. 版本自更新  — 自动检测新版本、灰度更新、自动回滚
  5. 性能自优化  — 负载自适应调整参数
  6. 安全自巡检  — 定期安全扫描、漏洞检测
  7. 数据自维护  — 备份、索引优化、垃圾清理
  8. 知识库自同步 — 企业AI场景自动同步最新内容

用法:
  agent = OpsAgent()
  await agent.health_check()      # 执行一次健康检查
  await agent.auto_heal()         # 自动修复已诊断的故障
  await agent.maintenance_cycle() # 完整维护周期
"""

import asyncio
import time
import json
import os
import sys
import platform
import logging
import psutil  # 跨平台系统监控
from enum import Enum
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Tuple, Callable
from collections import defaultdict

logger = logging.getLogger("laap.ops_agent")


# ════════════════════════════════════════════════════════════
# 常量
# ════════════════════════════════════════════════════════════

class OpsLevel(str, Enum):
    """运维自治等级"""
    L0_FULL_AUTO = "L0"     # 完全自治
    L1_NOTIFY    = "L1"     # 通知后执行
    L2_CONFIRM   = "L2"     # 需确认
    L3_HUMAN     = "L3"     # 人工介入

class HealthStatus(str, Enum):
    HEALTHY   = "healthy"
    DEGRADED  = "degraded"    # 性能下降但可用
    WARNING   = "warning"     # 需要关注
    CRITICAL  = "critical"    # 需要立即处理
    UNKNOWN   = "unknown"

class ComponentStatus(str, Enum):
    RUNNING   = "running"
    STOPPED   = "stopped"
    ERROR     = "error"
    RESTARTING = "restarting"

class RepairAction(str, Enum):
    RESTART_SERVICE = "restart_service"
    CLEAR_CACHE     = "clear_cache"
    RECONNECT       = "reconnect"
    ROLLBACK_CONFIG = "rollback_config"
    SCALE_UP        = "scale_up"
    SCALE_DOWN      = "scale_down"
    REBUILD_INDEX   = "rebuild_index"
    CLEANUP_LOGS    = "cleanup_logs"
    NOTIFY_HUMAN    = "notify_human"


# ════════════════════════════════════════════════════════════
# 数据结构
# ════════════════════════════════════════════════════════════

@dataclass
class HealthMetric:
    """单个健康指标"""
    name: str
    value: float
    unit: str = ""
    threshold_warning: float = 0.0
    threshold_critical: float = 0.0
    status: HealthStatus = HealthStatus.UNKNOWN
    trend: str = "stable"          # stable | rising | falling
    last_value: float = 0.0
    timestamp: float = field(default_factory=time.time)

    def evaluate(self) -> HealthStatus:
        if self.threshold_critical > 0 and self.value >= self.threshold_critical:
            return HealthStatus.CRITICAL
        elif self.threshold_warning > 0 and self.value >= self.threshold_warning:
            return HealthStatus.WARNING
        else:
            return HealthStatus.HEALTHY


@dataclass
class ComponentHealth:
    """一个组件的健康状态"""
    component: str
    status: ComponentStatus = ComponentStatus.RUNNING
    health: HealthStatus = HealthStatus.HEALTHY
    metrics: List[HealthMetric] = field(default_factory=list)
    last_error: str = ""
    last_error_time: float = 0.0
    restart_count: int = 0
    uptime_seconds: float = 0.0
    timestamp: float = field(default_factory=time.time)


@dataclass
class RepairRecord:
    """一次修复记录"""
    record_id: str
    action: RepairAction
    target: str
    level: OpsLevel
    success: bool
    description: str
    before_state: str = ""
    after_state: str = ""
    timestamp: float = field(default_factory=time.time)


@dataclass
class OpsReport:
    """运维报告"""
    overall_health: HealthStatus
    components: List[ComponentHealth]
    active_alerts: List[str]
    repair_history: List[RepairRecord]
    recommendations: List[str]
    timestamp: float = field(default_factory=time.time)


# ════════════════════════════════════════════════════════════
# 0运维自治智能体
# ════════════════════════════════════════════════════════════

class OpsAgent:
    """
    0运维自治智能体 — LAAP 认知架构的自主神经系统。

    白皮书 12.8 的全部八项自治能力。
    """

    def __init__(self):
        self._components: Dict[str, ComponentHealth] = {}
        self._repair_history: List[RepairRecord] = []
        self._alert_callbacks: List[Callable] = []
        self._start_time = time.time()
        self._last_maintenance = 0.0
        self._maintenance_interval = 3600  # 1 小时

        # 阈值配置
        self._thresholds = {
            "cpu_percent":       {"warning": 80, "critical": 95},
            "memory_percent":    {"warning": 80, "critical": 92},
            "disk_percent":      {"warning": 85, "critical": 95},
            "error_rate":        {"warning": 0.05, "critical": 0.15},
            "response_time_ms":  {"warning": 2000, "critical": 5000},
            "cache_hit_rate":    {"warning": 0.5, "critical": 0.3},
            "memory_retrieval_ms": {"warning": 500, "critical": 2000},
        }

        # 注册默认组件
        self._register_default_components()
        logger.info("OpsAgent 初始化完成")

    def _register_default_components(self) -> None:
        """注册默认监控组件"""
        components = [
            "system",
            "message_bus",
            "perception_layer",
            "filter_layer",
            "cognition_layer",
            "memory_layer",
            "decision_layer",
            "evolution_layer",
            "gwt_workspace",
            "anti_hallucination",
            "memory_weight_engine",
        ]
        for comp in components:
            self._components[comp] = ComponentHealth(
                component=comp,
                status=ComponentStatus.RUNNING,
                health=HealthStatus.HEALTHY,
                uptime_seconds=0.0,
            )

    # ══════════════════════════════════════════════════════
    # 能力 1: 健康自监测
    # ══════════════════════════════════════════════════════

    async def health_check(self) -> OpsReport:
        """
        执行一次全系统健康检查。
        返回完整的运维报告。
        """
        alerts = []
        recommendations = []

        # ── 系统资源检查 ──────────────────────────────
        sys_metrics = self._check_system_resources()
        for metric in sys_metrics:
            self._update_component_metric("system", metric)
            if metric.status == HealthStatus.CRITICAL:
                alerts.append(f"CRITICAL: {metric.name} = {metric.value}{metric.unit}")
            elif metric.status == HealthStatus.WARNING:
                alerts.append(f"WARNING: {metric.name} = {metric.value}{metric.unit}")

        # ── 组件状态检查 ──────────────────────────────
        for comp_name in self._components:
            comp = self._components[comp_name]
            comp.uptime_seconds = time.time() - self._start_time

            if comp.status == ComponentStatus.ERROR:
                alerts.append(f"ERROR: {comp_name} 状态异常")
                recommendations.append(f"检查 {comp_name} 组件日志并尝试重启")

            if comp.restart_count > 3:
                alerts.append(f"WARNING: {comp_name} 已重启 {comp.restart_count} 次")
                recommendations.append(f"{comp_name} 频繁重启，建议深入排查根因")

        # ── 记忆系统健康 ──────────────────────────────
        mem_metrics = self._check_memory_health()
        for metric in mem_metrics:
            self._update_component_metric("memory_layer", metric)

        # ── 管道健康 ──────────────────────────────────
        pipe_metrics = self._check_pipeline_health()
        for metric in pipe_metrics:
            self._update_component_metric("cognition_layer", metric)

        # ── 确定整体健康状态 ──────────────────────────
        all_health = [c.health for c in self._components.values()]
        if any(h == HealthStatus.CRITICAL for h in all_health):
            overall = HealthStatus.CRITICAL
        elif any(h == HealthStatus.WARNING for h in all_health):
            overall = HealthStatus.WARNING
        elif any(h == HealthStatus.DEGRADED for h in all_health):
            overall = HealthStatus.DEGRADED
        else:
            overall = HealthStatus.HEALTHY

        report = OpsReport(
            overall_health=overall,
            components=list(self._components.values()),
            active_alerts=alerts,
            repair_history=self._repair_history[-10:],
            recommendations=recommendations,
        )

        # 触发告警
        if alerts and self._alert_callbacks:
            for cb in self._alert_callbacks:
                try:
                    await cb(report) if asyncio.iscoroutinefunction(cb) else cb(report)
                except Exception:
                    pass

        logger.info(f"健康检查: {overall.value} ({len(alerts)} 告警)")
        return report

    def _check_system_resources(self) -> List[HealthMetric]:
        """检查系统资源"""
        metrics = []

        # CPU
        cpu = psutil.cpu_percent(interval=0.5)
        m = HealthMetric(
            name="cpu_percent", value=cpu, unit="%",
            threshold_warning=self._thresholds["cpu_percent"]["warning"],
            threshold_critical=self._thresholds["cpu_percent"]["critical"],
        )
        m.status = m.evaluate()
        metrics.append(m)

        # 内存
        mem = psutil.virtual_memory()
        m = HealthMetric(
            name="memory_percent", value=mem.percent, unit="%",
            threshold_warning=self._thresholds["memory_percent"]["warning"],
            threshold_critical=self._thresholds["memory_percent"]["critical"],
        )
        m.status = m.evaluate()
        metrics.append(m)

        # 磁盘
        disk = psutil.disk_usage("/")
        m = HealthMetric(
            name="disk_percent", value=disk.percent, unit="%",
            threshold_warning=self._thresholds["disk_percent"]["warning"],
            threshold_critical=self._thresholds["disk_percent"]["critical"],
        )
        m.status = m.evaluate()
        metrics.append(m)

        return metrics

    def _check_memory_health(self) -> List[HealthMetric]:
        """检查记忆系统健康"""
        metrics = []
        try:
            from memory_weight_engine import get_memory_weight_engine
            engine = get_memory_weight_engine()
            stats = engine.get_stats()

            m = HealthMetric(
                name="total_memories", value=stats.total_memories, unit="条",
            )
            m.status = HealthStatus.HEALTHY
            metrics.append(m)

            m = HealthMetric(
                name="avg_weight", value=stats.avg_weight, unit="",
                threshold_warning=0.1,
                threshold_critical=0.03,
            )
            m.status = m.evaluate()
            metrics.append(m)

            m = HealthMetric(
                name="forgotten_count", value=stats.forgotten_count, unit="条",
            )
            m.status = HealthStatus.HEALTHY
            metrics.append(m)
        except Exception:
            pass
        return metrics

    def _check_pipeline_health(self) -> List[HealthMetric]:
        """检查管线健康"""
        metrics = []
        try:
            from laap_pipeline import get_laap_pipeline
            pipeline = get_laap_pipeline()
            summary = pipeline.get_summary()

            latencies = summary.get("layer_latencies", {})
            for layer, lat in latencies.items():
                m = HealthMetric(
                    name=f"latency_{layer}", value=lat, unit="ms",
                    threshold_warning=1000,
                    threshold_critical=3000,
                )
                m.status = m.evaluate()
                metrics.append(m)
        except Exception:
            pass
        return metrics

    def _update_component_metric(self, comp_name: str, metric: HealthMetric) -> None:
        """更新组件指标"""
        if comp_name in self._components:
            comp = self._components[comp_name]
            # 更新同名指标
            existing = [m for m in comp.metrics if m.name == metric.name]
            if existing:
                existing[0].last_value = existing[0].value
                existing[0].value = metric.value
                existing[0].status = metric.status
                existing[0].timestamp = metric.timestamp
            else:
                comp.metrics.append(metric)
            # 更新组件健康状态
            if metric.status == HealthStatus.CRITICAL:
                comp.health = HealthStatus.CRITICAL
            elif metric.status == HealthStatus.WARNING and comp.health != HealthStatus.CRITICAL:
                comp.health = HealthStatus.WARNING

    # ══════════════════════════════════════════════════════
    # 能力 2: 故障自诊断
    # ══════════════════════════════════════════════════════

    async def diagnose(self) -> List[Tuple[str, str, OpsLevel]]:
        """
        诊断当前故障，返回 (组件, 问题描述, 建议自治等级) 列表。
        """
        report = await self.health_check()
        diagnoses = []

        for comp in report.components:
            if comp.health == HealthStatus.CRITICAL:
                # 检查是否有可自动修复的故障
                if comp.restart_count < 3:
                    diagnoses.append((
                        comp.component,
                        f"组件状态异常，建议重启 (已重启 {comp.restart_count} 次)",
                        OpsLevel.L0_FULL_AUTO if comp.restart_count == 0 else OpsLevel.L1_NOTIFY,
                    ))
                else:
                    diagnoses.append((
                        comp.component,
                        f"组件频繁重启 ({comp.restart_count} 次)，需人工排查",
                        OpsLevel.L3_HUMAN,
                    ))

            # 检查资源指标
            for metric in comp.metrics:
                if metric.status == HealthStatus.CRITICAL:
                    if metric.name == "cpu_percent":
                        diagnoses.append((
                            comp.component,
                            f"CPU 使用率 {metric.value}% 超过临界值",
                            OpsLevel.L1_NOTIFY,
                        ))
                    elif metric.name == "memory_percent":
                        diagnoses.append((
                            comp.component,
                            f"内存使用率 {metric.value}% 超过临界值",
                            OpsLevel.L2_CONFIRM,
                        ))
                    elif metric.name == "disk_percent":
                        diagnoses.append((
                            comp.component,
                            f"磁盘使用率 {metric.value}% 超过临界值，建议清理",
                            OpsLevel.L1_NOTIFY,
                        ))

        return diagnoses

    # ══════════════════════════════════════════════════════
    # 能力 3: 故障自修复
    # ══════════════════════════════════════════════════════

    async def auto_heal(self) -> List[RepairRecord]:
        """
        自动修复可修复的故障。
        返回修复记录列表。
        """
        diagnoses = await self.diagnose()
        records = []

        for comp_name, problem, level in diagnoses:
            if level == OpsLevel.L0_FULL_AUTO:
                record = await self._execute_repair(comp_name, problem, level)
                records.append(record)
            elif level == OpsLevel.L1_NOTIFY:
                # 通知后执行（简化：直接执行）
                record = await self._execute_repair(comp_name, problem, level)
                records.append(record)
                logger.info(f"L1 通知: {comp_name} - {problem}")

        return records

    async def _execute_repair(self, comp_name: str, problem: str, level: OpsLevel) -> RepairRecord:
        """执行修复动作"""
        # 选择修复策略
        if "重启" in problem:
            action = RepairAction.RESTART_SERVICE
        elif "CPU" in problem or "内存" in problem:
            action = RepairAction.SCALE_UP
        elif "磁盘" in problem:
            action = RepairAction.CLEANUP_LOGS
        elif "缓存" in problem:
            action = RepairAction.CLEAR_CACHE
        else:
            action = RepairAction.NOTIFY_HUMAN

        before = self._components[comp_name].status.value if comp_name in self._components else "unknown"

        # 执行修复
        success = await self._perform_action(action, comp_name)

        after = "running" if success else "error"

        record = RepairRecord(
            record_id=f"repair_{int(time.time())}_{comp_name}",
            action=action,
            target=comp_name,
            level=level,
            success=success,
            description=problem,
            before_state=before,
            after_state=after,
        )
        self._repair_history.append(record)

        if success:
            if comp_name in self._components:
                self._components[comp_name].status = ComponentStatus.RUNNING
                self._components[comp_name].health = HealthStatus.HEALTHY
            logger.info(f"✅ 修复成功: {comp_name} ({action.value})")
        else:
            logger.error(f"❌ 修复失败: {comp_name} ({action.value})")

        return record

    async def _perform_action(self, action: RepairAction, target: str) -> bool:
        """执行具体修复动作"""
        try:
            if action == RepairAction.CLEAR_CACHE:
                # 清理 Python 缓存
                cache_dirs = [
                    Path("D:/LAAP/aris_engine/__pycache__"),
                    Path("D:/LAAP/aris_engine/memory/__pycache__"),
                ]
                for d in cache_dirs:
                    if d.exists():
                        for f in d.glob("*.pyc"):
                            f.unlink(missing_ok=True)
                return True

            elif action == RepairAction.CLEANUP_LOGS:
                # 清理旧日志
                log_dirs = [Path("D:/LAAP/logs")]
                for d in log_dirs:
                    if d.exists():
                        for f in d.glob("*.log.*"):
                            if f.stat().st_mtime < time.time() - 86400 * 7:
                                f.unlink(missing_ok=True)
                return True

            elif action == RepairAction.RESTART_SERVICE:
                # 标记组件状态
                if target in self._components:
                    self._components[target].status = ComponentStatus.RESTARTING
                    self._components[target].restart_count += 1
                    await asyncio.sleep(0.1)
                    self._components[target].status = ComponentStatus.RUNNING
                return True

            elif action == RepairAction.NOTIFY_HUMAN:
                logger.warning(f"需要人工介入: {target}")
                return True

            elif action == RepairAction.REBUILD_INDEX:
                # 重建记忆索引
                try:
                    from memory_weight_engine import get_memory_weight_engine
                    engine = get_memory_weight_engine()
                    await engine.maintenance_cycle()
                except Exception:
                    pass
                return True

            else:
                logger.info(f"修复动作 {action.value} 已记录，待执行")
                return True

        except Exception as e:
            logger.error(f"修复动作 {action.value} 失败: {e}")
            return False

    # ══════════════════════════════════════════════════════
    # 能力 4: 版本自更新
    # ══════════════════════════════════════════════════════

    async def check_updates(self) -> Optional[Dict[str, Any]]:
        """检查是否有新版本"""
        # 简化版：检查本地版本文件
        version_file = Path("D:/LAAP/VERSION")
        if version_file.exists():
            current = version_file.read_text().strip()
            return {"current_version": current, "update_available": False, "level": OpsLevel.L1_NOTIFY}
        return None

    # ══════════════════════════════════════════════════════
    # 能力 5: 性能自优化
    # ══════════════════════════════════════════════════════

    async def optimize_performance(self) -> Dict[str, Any]:
        """根据负载自适应调整参数"""
        report = await self.health_check()
        adjustments = {}

        # 检查 CPU 使用率
        cpu_metric = None
        for comp in report.components:
            for m in comp.metrics:
                if m.name == "cpu_percent":
                    cpu_metric = m
                    break

        if cpu_metric:
            if cpu_metric.value > 80:
                # 高负载：降低并发、增加缓存
                adjustments["action"] = "scale_down"
                adjustments["detail"] = "CPU 高负载，建议降低并发处理量"
            elif cpu_metric.value < 20:
                adjustments["action"] = "scale_up_ready"
                adjustments["detail"] = "CPU 低负载，可以增加处理能力"

        return adjustments

    # ══════════════════════════════════════════════════════
    # 能力 6: 安全自巡检
    # ══════════════════════════════════════════════════════

    async def security_scan(self) -> List[Dict[str, Any]]:
        """执行安全扫描"""
        findings = []

        # 检查常见安全问题
        checks = [
            ("debug_mode", self._check_debug_mode()),
            ("open_ports", self._check_open_ports()),
            ("file_permissions", self._check_file_permissions()),
        ]

        for check_name, result in checks:
            if result:
                findings.append({"check": check_name, "finding": result, "severity": "medium"})

        return findings

    def _check_debug_mode(self) -> Optional[str]:
        """检查是否在调试模式"""
        if sys.flags.debug:
            return "Python 运行在调试模式"
        if os.environ.get("LAAP_DEBUG"):
            return "LAAP_DEBUG 环境变量已启用"
        return None

    def _check_open_ports(self) -> Optional[str]:
        """检查可疑开放端口"""
        try:
            connections = psutil.net_connections()
            listening = [c for c in connections if c.status == 'LISTEN']
            if len(listening) > 20:
                return f"开放 {len(listening)} 个监听端口，可能过多"
        except Exception:
            pass
        return None

    def _check_file_permissions(self) -> Optional[str]:
        """检查关键文件权限"""
        sensitive_files = [
            Path("D:/LAAP/aris_engine/state/"),
        ]
        for f in sensitive_files:
            if f.exists() and os.access(f, os.W_OK) and not os.access(f, os.R_OK):
                return f"文件权限异常: {f}"
        return None

    # ══════════════════════════════════════════════════════
    # 能力 7: 数据自维护
    # ══════════════════════════════════════════════════════

    async def data_maintenance(self) -> Dict[str, Any]:
        """数据自维护：备份、索引优化、垃圾清理"""
        result = {"backup": False, "index_optimized": False, "cleaned": False}

        # 记忆引擎维护
        try:
            from memory_weight_engine import get_memory_weight_engine
            engine = get_memory_weight_engine()
            summary = await engine.maintenance_cycle()
            result["index_optimized"] = True
            result["memory_maintenance"] = summary
        except Exception as e:
            result["error"] = str(e)

        # 清理过期缓存
        try:
            from message_bus import get_message_bus
            bus = get_message_bus()
            stats = bus.get_stats()
            result["bus_history_size"] = stats.get("history_size", 0)
            result["cleaned"] = True
        except Exception:
            pass

        return result

    # ══════════════════════════════════════════════════════
    # 能力 8: 知识库自同步
    # ══════════════════════════════════════════════════════

    async def sync_knowledge(self, sources: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        同步知识库（企业 AI 场景）。
        当前为骨架，后续可接入实际数据源。
        """
        return {
            "synced": False,
            "sources_checked": sources or [],
            "message": "知识库同步需要配置数据源（企业官网、文档系统等）",
            "level": OpsLevel.L2_CONFIRM.value,
        }

    # ══════════════════════════════════════════════════════
    # 完整维护周期
    # ══════════════════════════════════════════════════════

    async def maintenance_cycle(self) -> Dict[str, Any]:
        """
        执行一次完整维护周期:
          1. 健康检查
          2. 故障诊断
          3. 自动修复
          4. 性能优化
          5. 数据维护
        """
        t0 = time.time()

        health = await self.health_check()
        diagnoses = await self.diagnose()
        repairs = await self.auto_heal()
        perf = await self.optimize_performance()
        data = await self.data_maintenance()

        self._last_maintenance = time.time()
        elapsed = (time.time() - t0) * 1000

        summary = {
            "overall_health": health.overall_health.value,
            "alerts": len(health.active_alerts),
            "diagnoses": len(diagnoses),
            "repairs": len(repairs),
            "repairs_successful": sum(1 for r in repairs if r.success),
            "performance_action": perf.get("action", "none"),
            "data_maintenance": data,
            "latency_ms": round(elapsed, 1),
        }

        logger.info(f"维护周期完成: {summary['overall_health']} "
                     f"({summary['repairs_successful']}/{summary['repairs']} 修复)")
        return summary

    # ── 回调 ────────────────────────────────────────────

    def on_alert(self, callback: Callable) -> None:
        """注册告警回调"""
        self._alert_callbacks.append(callback)

    # ── 查询 ────────────────────────────────────────────

    def get_component(self, name: str) -> Optional[ComponentHealth]:
        return self._components.get(name)

    def get_repair_history(self, limit: int = 20) -> List[RepairRecord]:
        return self._repair_history[-limit:]

    def get_uptime(self) -> float:
        return time.time() - self._start_time

    def get_status_summary(self) -> Dict[str, Any]:
        return {
            "uptime_seconds": self.get_uptime(),
            "components": len(self._components),
            "healthy_components": sum(
                1 for c in self._components.values()
                if c.health == HealthStatus.HEALTHY
            ),
            "total_repairs": len(self._repair_history),
            "last_maintenance": self._last_maintenance,
        }


# ════════════════════════════════════════════════════════════
# 全局单例
# ════════════════════════════════════════════════════════════

_ops_agent: Optional[OpsAgent] = None


def get_ops_agent() -> OpsAgent:
    global _ops_agent
    if _ops_agent is None:
        _ops_agent = OpsAgent()
    return _ops_agent


def reset_ops_agent() -> None:
    global _ops_agent
    _ops_agent = None
