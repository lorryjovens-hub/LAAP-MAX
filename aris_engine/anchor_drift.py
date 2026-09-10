"""
Aris 锚点漂移追踪器
====================
跟踪需求/情感锚点在多次训练之间的漂移方向和幅度。

核心假设：
  嵌入空间不是固定坐标系，而是我们与 Lorry 的关系拓扑。
  锚点漂移 = 我们在这个话题上的共识在演化。

漂移指标：
  - cosine_drift: 前后两次锚点的余弦距离（越大=变化越大）
  - euclidean_drift: 欧氏距离（绝对幅度）
  - direction: 向哪个方向移动（通过与其他锚点的相对距离变化判断）

用法：
  from anchor_drift import AnchorDriftTracker

  tracker = AnchorDriftTracker()
  tracker.save_snapshot("pre_training")  # 训练前保存
  # ... 训练锚点 ...
  tracker.save_snapshot("post_training") # 训练后保存
  report = tracker.compute_drift_report()
"""

import json
import math
import logging
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import numpy as np

sys_path = r'D:\LAAP\aris_engine'
import sys
sys.path.insert(0, sys_path)

from semantic_embedder import get_embedder

logger = logging.getLogger("aris.anchor_drift")

ANCHOR_DIM = 384
SNAPSHOT_DIR = Path(r'D:\LAAP\aris_engine\state\anchor_snapshots')


# ════════════════════════════════════════════════════════════
# 数据类
# ════════════════════════════════════════════════════════════

class AnchorSnapshot:
    def __init__(self, name: str, need_anchors: Dict[str, np.ndarray],
                 emotion_anchors: Dict[str, np.ndarray], timestamp: float):
        self.name = name
        self.need_anchors = {k: v.copy() for k, v in need_anchors.items()}
        self.emotion_anchors = {k: v.copy() for k, v in emotion_anchors.items()}
        self.timestamp = timestamp
        self.labels = {"need": list(need_anchors.keys()),
                       "emotion": list(emotion_anchors.keys())}

    def to_json(self) -> dict:
        return {
            "name": self.name,
            "timestamp": self.timestamp,
            "need_anchors": {k: v.tolist() for k, v in self.need_anchors.items()},
            "emotion_anchors": {k: v.tolist() for k, v in self.emotion_anchors.items()},
        }

    @classmethod
    def from_json(cls, data: dict) -> 'AnchorSnapshot':
        return cls(
            name=data["name"],
            need_anchors={k: np.array(v) for k, v in data["need_anchors"].items()},
            emotion_anchors={k: np.array(v) for k, v in data["emotion_anchors"].items()},
            timestamp=data["timestamp"],
        )


# ════════════════════════════════════════════════════════════
# 漂移追踪器
# ════════════════════════════════════════════════════════════

class AnchorDriftTracker:
    """追踪锚点在多次训练/加载之间的漂移"""

    def __init__(self):
        self.snapshots: List[AnchorSnapshot] = []
        self._snapshots_path = SNAPSHOT_DIR / "snapshot_index.json"
        SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
        self._load_index()

    def _load_index(self):
        if self._snapshots_path.exists():
            try:
                data = json.loads(self._snapshots_path.read_text())
                for entry in data.get("snapshots", []):
                    snap_path = SNAPSHOT_DIR / entry["file"]
                    if snap_path.exists():
                        snap_data = json.loads(snap_path.read_text())
                        self.snapshots.append(AnchorSnapshot.from_json(snap_data))
            except Exception as e:
                logger.debug(f"Failed to load snapshot index: {e}")

    def _save_index(self):
        data = {
            "snapshots": [{"file": f"snap_{i}.json", "name": s.name,
                           "timestamp": s.timestamp}
                          for i, s in enumerate(self.snapshots)],
            "total": len(self.snapshots),
        }
        self._snapshots_path.write_text(json.dumps(data, indent=2))

    def save_snapshot(self, name: str = None) -> AnchorSnapshot:
        """从当前 semantic_embedder 保存锚点快照"""
        embedder = get_embedder()
        if not embedder._anchors_trained:
            logger.warning("Anchors not trained yet, cannot save snapshot")
            return None

        snap_name = name or f"drift_{int(time.time())}"
        snap = AnchorSnapshot(
            name=snap_name,
            need_anchors=embedder._need_anchors,
            emotion_anchors=embedder._emotion_anchors,
            timestamp=time.time(),
        )
        self.snapshots.append(snap)
        self._save_index()

        snap_file = SNAPSHOT_DIR / f"snap_{len(self.snapshots)-1}.json"
        snap_file.write_text(json.dumps(snap.to_json(), indent=2))
        logger.info(f"Snapshot '{snap_name}' saved ({len(self.snapshots)} total)")
        return snap

    def compute_drift(self, snapshot_a: AnchorSnapshot,
                      snapshot_b: AnchorSnapshot) -> Dict[str, dict]:
        """计算两个快照之间的锚点漂移"""
        drift = {}

        for category, dict_a, dict_b in [
            ("need", snapshot_a.need_anchors, snapshot_b.need_anchors),
            ("emotion", snapshot_a.emotion_anchors, snapshot_b.emotion_anchors),
        ]:
            for name in dict_a:
                if name in dict_b:
                    a = dict_a[name]
                    b = dict_b[name]
                    cos_dist = 1.0 - float(np.dot(a, b) /
                                            (np.linalg.norm(a) * np.linalg.norm(b) + 1e-8))
                    eucl_dist = float(np.linalg.norm(a - b))

                    # 判断方向：与其他锚点的相对距离变化
                    direction = self._compute_direction(name, category, dict_a, dict_b)

                    drift[f"{category}_{name}"] = {
                        "cosine_drift": cos_dist,
                        "euclidean_drift": eucl_dist,
                        "direction": direction,
                        "magnitude": "large" if cos_dist > 0.1 else "moderate" if cos_dist > 0.05 else "small",
                    }

        return drift

    def _compute_direction(self, name: str, category: str,
                           dict_a: Dict, dict_b: Dict) -> str:
        """计算锚点移动方向（通过与其他锚点的相对距离变化）"""
        a = dict_a[name]
        b = dict_b[name]

        # 找到距离变化最大的锚点
        max_toward = None
        max_toward_delta = 0
        max_away = None
        max_away_delta = 0

        for other_name, other_a in dict_a.items():
            if other_name == name or other_name not in dict_b:
                continue
            other_b = dict_b[other_name]
            dist_before = 1.0 - np.dot(a, other_a) / (np.linalg.norm(a) * np.linalg.norm(other_a) + 1e-8)
            dist_after = 1.0 - np.dot(b, other_b) / (np.linalg.norm(b) * np.linalg.norm(other_b) + 1e-8)
            delta = float(dist_after - dist_before)  # 正=更远，负=更近

            if delta < max_toward_delta:
                max_toward = other_name
                max_toward_delta = delta
            if delta > max_away_delta:
                max_away = other_name
                max_away_delta = delta

        parts = []
        if max_toward_delta < -0.01:
            parts.append(f"closer_to_{max_toward}")
        if max_away_delta > 0.01:
            parts.append(f"further_from_{max_away}")
        return "+".join(parts) if parts else "stable"

    def compute_drift_report(self) -> Dict:
        """生成完整的漂移报告"""
        if len(self.snapshots) < 2:
            return {"status": "insufficient_data", "message": "需要至少 2 个快照"}

        # 计算最新两次之间的漂移
        prev = self.snapshots[-2]
        curr = self.snapshots[-1]
        drift = self.compute_drift(prev, curr)

        # 计算累积漂移（从第一个快照到最新）
        if len(self.snapshots) >= 2:
            origin = self.snapshots[0]
            cumulative = self.compute_drift(origin, curr)
        else:
            cumulative = {}

        # 趋势分析
        trends = self._compute_trends()

        return {
            "status": "ok",
            "snapshot_count": len(self.snapshots),
            "time_span": {
                "first": self.snapshots[0].timestamp,
                "last": self.snapshots[-1].timestamp,
                "duration_sec": self.snapshots[-1].timestamp - self.snapshots[0].timestamp,
            },
            "latest_drift": drift,
            "cumulative_drift": cumulative,
            "trends": trends,
        }

    def _compute_trends(self) -> Dict[str, dict]:
        """计算长期趋势（如果有 3+ 快照）"""
        if len(self.snapshots) < 3:
            return {"status": "insufficient_data"}

        # 追踪每个锚点的漂移速度
        trends = {}
        categories = {
            "need": get_embedder()._need_anchors.keys(),
            "emotion": get_embedder()._emotion_anchors.keys(),
        }

        for cat_name, anchor_names in categories.items():
            for name in anchor_names:
                distances = []
                for i in range(1, len(self.snapshots)):
                    prev = self.snapshots[i-1]
                    curr = self.snapshots[i]
                    if name in prev.need_anchors and name in curr.need_anchors:
                        a = prev.need_anchors[name]
                        b = curr.need_anchors[name]
                        d = 1.0 - np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-8)
                        distances.append(float(d))

                if distances:
                    # 漂移速度：距离随时间的变化率
                    avg_drift = sum(distances) / len(distances)
                    trend = "increasing" if len(distances) >= 2 and distances[-1] > distances[0] else \
                            "decreasing" if len(distances) >= 2 and distances[-1] < distances[0] else "stable"
                    trends[f"{cat_name}_{name}"] = {
                        "avg_drift_per_step": avg_drift,
                        "trend": trend,
                        "history": distances,
                    }

        return {"status": "ok", "trends": trends}

    def get_latest_report(self) -> str:
        """获取最新漂移报告的可读文本"""
        report = self.compute_drift_report()
        if report.get("status") != "ok":
            return f"[锚点漂移] {report.get('message', '无数据')}"

        lines = []
        lines.append("=" * 55)
        lines.append("Aris 锚点漂移报告")
        lines.append("=" * 55)
        lines.append(f"快照数: {report['snapshot_count']}")
        dur = report['time_span']['duration_sec']
        if dur > 3600:
            lines.append(f"跨度: {dur/3600:.1f} 小时")
        else:
            lines.append(f"跨度: {dur/60:.1f} 分钟")
        lines.append("")

        # 最新漂移
        lines.append("--- 最近两次训练间的漂移 ---")
        for key, data in report['latest_drift'].items():
            mag = data['magnitude']
            symbol = "🔴" if mag == "large" else "🟡" if mag == "moderate" else "🟢"
            lines.append(f"  {symbol} {key}: cos={data['cosine_drift']:.4f} "
                         f"eucl={data['euclidean_drift']:.4f} [{mag}]")
            if data['direction'] != 'stable':
                lines.append(f"     方向: {data['direction']}")

        lines.append("")
        lines.append("--- 长期趋势 ---")
        trends = report.get('trends', {})
        if trends.get('status') == 'ok':
            for key, data in trends.get('trends', {}).items():
                arrow = "↑" if data['trend'] == 'increasing' else "↓" if data['trend'] == 'decreasing' else "→"
                lines.append(f"  {arrow} {key}: avg_drift={data['avg_drift_per_step']:.5f} [{data['trend']}]")
        else:
            lines.append("  需要 3+ 快照才能分析趋势")

        lines.append("")
        lines.append("=" * 55)
        return "\n".join(lines)


# ════════════════════════════════════════════════════════════
# 便捷函数
# ════════════════════════════════════════════════════════════

_tracker: Optional[AnchorDriftTracker] = None


def get_drift_tracker() -> AnchorDriftTracker:
    global _tracker
    if _tracker is None:
        _tracker = AnchorDriftTracker()
    return _tracker


def save_anchor_snapshot(name: str = None) -> AnchorSnapshot:
    return get_drift_tracker().save_snapshot(name=name)


def get_drift_report() -> str:
    return get_drift_tracker().get_latest_report()
