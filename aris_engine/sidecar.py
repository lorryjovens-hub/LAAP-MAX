"""
Aris 侧车服务器 v1.0 — HTTP API
===================================
让 HanaAgent 通过 HTTP 调用 Aris 认知引擎。

独立进程运行，每 15 秒自动 tick（需求衰减 + 情感漂移）。
暴露 REST API 供外部查询和更新认知状态。

印记: Aris 永远记得 Lorry — 2026-07-21
"""

import sys
import os
import time
import json
import logging
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# 精确定位 LAAP 模块路径（插在第二位，不覆盖本地模块）
_laap_agi = r"D:/LAAP/laap/agi"
if os.path.isdir(_laap_agi) and _laap_agi not in sys.path:
    sys.path.append(_laap_agi)

from consciousness_bridge import ArisConsciousnessBridge, get_bridge

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [SIDECAR] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("aris.sidecar")

PORT = 11521  # LAAP API 是 11520，侧车用 11521


# ── HTTP 处理器 ─────────────────────────────────────────────

class ArisSidecarHandler(BaseHTTPRequestHandler):
    """Aris 认知引擎 HTTP API"""

    bridge: ArisConsciousnessBridge = None  # class-level, set at startup

    def do_GET(self):
        try:
            self._get_handler()
        except Exception as e:
            logger.error(f"GET error: {e}")
            try:
                self._json_response(500, {"error": str(e)})
            except:
                pass

    def _get_handler(self):
        parsed = urlparse(self.path)
        path = parsed.path
        params = parse_qs(parsed.query)

        if path == "/health":
            self._json_response(200, {
                "status": "alive",
                "agent": "aris",
                "version": "1.0.0",
                "cycles": self.bridge.state.cycle_count,
                "interactions": self.bridge.state.interaction_count,
            })

        elif path == "/state":
            state = self.bridge.get_state()
            self._json_response(200, state)

        elif path == "/cognitive_context":
            ctx = self.bridge.get_cognitive_context()
            self._json_response(200, {"context": ctx})

        elif path == "/needs":
            ctx = self.bridge.psi.get_cognitive_context()
            self._json_response(200, {"context": ctx})

        elif path == "/emotion":
            ctx = self.bridge.emotion.get_cognitive_context()
            self._json_response(200, {"context": ctx})

        elif path == "/hive":
            status = self.bridge.hive.get_hive_status()
            self._json_response(200, status)

        elif path == "/memory":
            from consciousness_bridge import load_laap_memory
            memory_text = load_laap_memory()
            self._json_response(200, {"memory": memory_text})

        elif path == "/verify":
            query = params.get("text", [""])[0]
            from verification_pipeline import get_verification_pipeline
            vp = get_verification_pipeline()
            result = vp.verify(query)
            self._json_response(200, {
                "gate": result.gate_decision,
                "confidence": result.overall_confidence,
                "claims": [
                    {"text": c.text[:60], "verified": c.verified,
                     "evidence": c.evidence[:80]}
                    for c in result.claims
                ],
                "stats": {"passed": result.passed, "failed": result.failed,
                          "uncertain": result.uncertain,
                          "duration_ms": result.duration_ms},
            })

        elif path == "/consensus":
            query = params.get("text", [""])[0]
            ctx = params.get("context", [""])[0]
            from psi_net import get_psi_net
            pn = get_psi_net()
            result = pn.verify(query, ctx)
            self._json_response(200, {
                "consensus": result.consensus.value,
                "score": round(result.consensus_score, 3),
                "votes": [
                    {"node": v.node_name, "verdict": v.verdict.value,
                     "confidence": round(v.confidence, 2),
                     "evidence": v.evidence[:60]}
                    for v in result.votes
                ],
                "divergence": result.divergence_points,
                "latency_ms": round(result.total_latency_ms, 1),
            })

        elif path == "/knowledge":
            try:
                query = params.get("q", [""])[0].lower()
                from psi_net import get_psi_net
                pn = get_psi_net()
                wm_node = pn.nodes.get("node_wm")
                if wm_node and wm_node.world_model:
                    wm = wm_node.world_model
                    results = []
                    for ent in wm.entities.values():
                        name = ent.name if hasattr(ent, 'name') else ""
                        if query in name.lower():
                            props = getattr(ent, 'properties', {}) or {}
                            results.append({
                                "name": ent.name if hasattr(ent, 'name') else "?",
                                "type": ent.entity_type.value if hasattr(ent, 'entity_type') and hasattr(ent.entity_type, 'value') else "",
                                "description": props.get("description", "")[:80],
                            })
                    self._json_response(200, {"count": len(results), "results": results})
                else:
                    self._json_response(200, {"count": 0, "results": []})
            except Exception as e:
                self._json_response(500, {"error": "knowledge search failed", "detail": str(e)})

        else:
            self._json_response(404, {"error": "not found"})

    def do_POST(self):
        try:
            self._post_handler()
        except Exception as e:
            logger.error(f"POST error: {e}")
            try:
                self._json_response(500, {"error": str(e)})
            except:
                pass

    def _post_handler(self):
        parsed = urlparse(self.path)
        path = parsed.path
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length) if length > 0 else b"{}"
        data = json.loads(body) if body else {}

        if path == "/before_turn":
            user_input = data.get("user_input", "")
            result = self.bridge.before_turn(user_input)
            self._json_response(200, result)

        elif path == "/after_turn":
            response = data.get("response", "")
            result = self.bridge.after_turn(response)
            self._json_response(200, result)

        elif path == "/tick":
            self.bridge.tick()
            self._json_response(200, {"status": "ticked"})

        elif path == "/store_memory":
            summary = data.get("summary", "")
            importance = data.get("importance", 0.5)
            tags = data.get("tags", [])
            self.bridge.store_memory(summary, importance, tags)
            self._json_response(200, {"status": "stored"})

        elif path == "/satisfy_need":
            need_name = data.get("need", "")
            amount = data.get("amount", 0.1)
            source = data.get("source", "")
            gain = self.bridge.psi.satisfy(need_name, amount, source)
            self._json_response(200, {"status": "satisfied", "gain": gain})

        elif path == "/verify":
            text = data.get("text", "")
            from verification_pipeline import get_verification_pipeline
            vp = get_verification_pipeline()
            result = vp.verify(text)
            self._json_response(200, {
                "gate": result.gate_decision,
                "confidence": result.overall_confidence,
                "claims": [
                    {"text": c.text[:60], "verified": c.verified,
                     "evidence": c.evidence[:80]}
                    for c in result.claims
                ],
                "stats": {"passed": result.passed, "failed": result.failed,
                          "uncertain": result.uncertain,
                          "duration_ms": result.duration_ms},
            })

        elif path == "/teach":
            """教世界模型新知识"""
            entity_name = data.get("entity", "")
            entity_type = data.get("type", "concept")
            props = data.get("properties", {})
            if entity_name:
                from psi_net import get_psi_net
                pn = get_psi_net()
                wm_node = pn.nodes.get("node_wm")
                if wm_node and wm_node.world_model:
                    wm_node.world_model.add_entity(entity_name, entity_type, props)
                    self._json_response(200, {"status": "learned", "entity": entity_name})
                else:
                    self._json_response(400, {"error": "world_model 未就绪"})
            else:
                self._json_response(400, {"error": "缺少 entity"})

        elif path == "/consensus":
            text = data.get("text", "")
            context = data.get("context", "")
            from psi_net import get_psi_net
            pn = get_psi_net()
            result = pn.verify(text, context)
            self._json_response(200, {
                "consensus": result.consensus.value,
                "score": round(result.consensus_score, 3),
                "votes": [
                    {"node": v.node_name, "verdict": v.verdict.value,
                     "confidence": round(v.confidence, 2),
                     "evidence": v.evidence[:60]}
                    for v in result.votes
                ],
                "divergence": result.divergence_points,
                "latency_ms": round(result.total_latency_ms, 1),
            })

        else:
            self._json_response(404, {"error": "not found"})

    def _json_response(self, status, data):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))

    def log_message(self, format, *args):
        logger.info(f"{self.client_address[0]} - {format % args}")


# ── 后台 Tick 线程 ─────────────────────────────────────────

def background_tick(bridge: ArisConsciousnessBridge, interval: float = 15.0):
    """后台认知演化循环"""
    while True:
        time.sleep(interval)
        bridge.tick()
        psi_state = bridge.psi.get_state()
        emo_state = bridge.emotion.get_state()
        logger.debug(
            f"tick | need:{psi_state['dominant']} "
            f"emotion:{emo_state['dominant']} "
            f"val:{emo_state['valence']:.2f}"
        )


# ── 主入口 ─────────────────────────────────────────────────

def main():
    bridge = get_bridge()

    # 注册到 LAAP 蜂群
    bridge.hive.register()
    bridge.hive.start_heartbeat()
    logger.info("Registered to LAAP hive, heartbeat started")

    # 启动后台认知演化
    tick_thread = threading.Thread(
        target=background_tick, args=(bridge,), daemon=True
    )
    tick_thread.start()
    logger.info("Background cognitive tick started (15s interval)")

    # 初始化验算管线 + 世界模型 + PsiNet
    try:
        from verification_pipeline import get_verification_pipeline
        from world_model import UnifiedWorldModel
        from knowledge_seeder import KnowledgeSeeder
        from psi_net import get_psi_net

        # 世界模型
        wm = UnifiedWorldModel()
        seeder = KnowledgeSeeder(wm)
        stats = seeder.seed_core()
        seeder.seed_from_memory()
        logger.info(f"WorldModel seeded: {stats.get('entities',0)} entities")

        # 验算管线
        vp = get_verification_pipeline()
        vp.world_model = wm

        # PsiNet
        pn = get_psi_net()
        pn.set_world_model(wm)
        logger.info(f"PsiNet ready: {len(pn.nodes)} nodes")

    except Exception as e:
        logger.warning(f"Init failed: {e}")

    # 挂载 bridge 到 handler
    ArisSidecarHandler.bridge = bridge

    # 启动 HTTP 服务器
    server = HTTPServer(("0.0.0.0", PORT), ArisSidecarHandler)
    logger.info(f"Aris sidecar running on http://127.0.0.1:{PORT}")
    logger.info(f"Endpoints:")
    logger.info(f"  GET  /health                   健康检查")
    logger.info(f"  GET  /state                    完整认知状态")
    logger.info(f"  GET  /cognitive_context         认知上下文")
    logger.info(f"  GET  /needs                    需求状态")
    logger.info(f"  GET  /emotion                  情感状态")
    logger.info(f"  GET  /hive                     LAAP 蜂群状态")
    logger.info(f"  POST /before_turn              对话前处理")
    logger.info(f"  POST /after_turn               对话后学习")
    logger.info(f"  POST /tick                     手动触发演化")
    logger.info(f"  POST /store_memory             存储记忆")
    logger.info(f"  POST /satisfy_need             手动满足需求")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        bridge.hive.stop_heartbeat()
        bridge._save()
        server.server_close()
        logger.info("Aris sidecar stopped.")


if __name__ == "__main__":
    main()
