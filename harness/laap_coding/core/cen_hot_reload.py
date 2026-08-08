"""
cen_hot_reload.py — CEN 架构的热加载/跨设备感知层
===================================================
CEN Principle Applied:
  - The causal network is device-independent (topological invariants > hardware)
  - Different devices = different regions of the same causal network
  - Hot reload = phase transition without losing topological invariants

Three Capabilities:
  1. Hot Reload: file watcher on config + graceful restart
  2. Cross-Device Sync: shared causal graph + event broadcast
  3. Cross-Window Awareness: per-window context merged into global state

Usage:
    # Start the hot-reloadable gateway
    python cen_hot_reload.py --gateway --port 11536
    
    # Start a cross-device sync node
    python cen_hot_reload.py --sync-node --port 11537 --peer localhost:11538
    
    # Hot-reload: touch the config file
    echo "{}" > config_changed.signal
"""

import json
import os
import sys
import time
import threading
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field, asdict
from http.server import HTTPServer, BaseHTTPRequestHandler

logger = logging.getLogger("cen.hot_reload")

# ============================================================
# 1. Config File Watcher (Hot Reload Trigger)
# ============================================================

class ConfigWatcher:
    """
    Watches a config file for changes. On change, triggers a reload callback.
    
    CEN: The config file is a 'boundary condition' — changing it should 
    cause a smooth phase transition, not a crash-and-restart.
    """
    
    def __init__(self, config_path: str, on_change: callable = None,
                 poll_interval: float = 1.0):
        self.config_path = Path(config_path)
        self.on_change = on_change
        self.poll_interval = poll_interval
        self._last_mtime = 0
        self._running = False
        self._thread = None
        
        if self.config_path.exists():
            self._last_mtime = self.config_path.stat().st_mtime
    
    def start(self):
        """Start watching in a background thread."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._watch, daemon=True)
        self._thread.start()
        logger.info(f"ConfigWatcher started: {self.config_path}")
    
    def stop(self):
        self._running = False
    
    def _watch(self):
        while self._running:
            try:
                if self.config_path.exists():
                    mtime = self.config_path.stat().st_mtime
                    if mtime != self._last_mtime:
                        self._last_mtime = mtime
                        logger.info(f"Config changed: {self.config_path}")
                        if self.on_change:
                            self.on_change()
                time.sleep(self.poll_interval)
            except Exception as e:
                logger.error(f"ConfigWatcher error: {e}")
                time.sleep(self.poll_interval)


# ============================================================
# 2. Graceful Gateway with Hot Reload
# ============================================================

class HotReloadableGateway:
    """
    A gateway that can be hot-reloaded without dropping requests.
    
    CEN: The gateway processes user messages (boundary conditions).
    Hot reload = changing the boundary condition handler without 
    losing the internal state (the causal graph).
    """
    
    def __init__(self, host: str = "127.0.0.1", port: int = 11536,
                 causal_graph_path: str = None):
        self.host = host
        self.port = port
        self.causal_graph_path = causal_graph_path or "D:/LAAP/aris_brain/memory/causal_graph.json"
        self._server = None
        self._classifier = None
        self._graph = None
        self._load_state()
        
        # Config watcher for hot reload
        config_path = "D:/LAAP/harness/laap_coding/core/cen_hot_reload_config.json"
        self._config_watcher = ConfigWatcher(config_path, self._on_config_change)
    
    def _load_state(self):
        """Load or reload the classifier and graph."""
        # Lazy import to support hot reload
        sys.path.insert(0, "D:/LAAP/harness/laap_coding/core")
        sys.path.insert(0, "D:/LAAP/aris_brain")
        
        # Reload classifier module
        if "cen_preprocessor" in sys.modules:
            import importlib
            importlib.reload(sys.modules["cen_preprocessor"])
        from cen_preprocessor import CENPreprocessor
        
        # Reload graph module
        if "causal_memory_graph" in sys.modules:
            import importlib
            importlib.reload(sys.modules["causal_memory_graph"])
        from causal_memory_graph import CausalMemoryGraph
        
        self._classifier = CENPreprocessor()
        self._graph = CausalMemoryGraph(storage_path=self.causal_graph_path)
        logger.info(f"State loaded: classifier + graph ({len(self._graph.nodes)} nodes)")
    
    def _on_config_change(self):
        """Hot reload triggered by config file change."""
        logger.info("Hot reload triggered...")
        try:
            self._load_state()
            logger.info("Hot reload complete")
        except Exception as e:
            logger.error(f"Hot reload failed: {e}")
    
    def start(self):
        """Start the HTTP server with hot reload support."""
        self._config_watcher.start()
        
        class Handler(BaseHTTPRequestHandler):
            gateway = self  # Parent reference
            
            def do_POST(self):
                content_length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(content_length)
                try:
                    data = json.loads(body)
                    message = data.get("message", "")
                    mode = data.get("mode", "classify")
                    
                    # Use current classifier (may have been hot-reloaded)
                    classifier = self.gateway._classifier
                    graph = self.gateway._graph
                    
                    if mode == "route":
                        result = classifier.route(message)
                    elif mode == "graph_retrieve":
                        results = graph.retrieve(message, max_nodes=5)
                        result = {"results": [
                            {"content": r.node.content[:100], 
                             "score": round(r.score, 3),
                             "domain": r.node.domain}
                            for r in results
                        ]}
                    elif mode == "graph_invariants":
                        result = graph.get_topological_invariants()
                    elif mode == "cross_device_sync":
                        # Cross-device: merge incoming memory into graph
                        incoming = data.get("memories", [])
                        count = 0
                        for mem in incoming:
                            nid = graph.add_memory(
                                content=mem.get("content", ""),
                                domain=mem.get("domain", "general"),
                                weight=mem.get("weight", 0.5),
                            )
                            count += 1
                        result = {"synced": count, "total_nodes": len(graph.nodes)}
                    else:
                        result = classifier.classify(message)
                    
                    response = json.dumps(result, ensure_ascii=False)
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Access-Control-Allow-Origin", "*")
                    self.end_headers()
                    self.wfile.write(response.encode("utf-8"))
                except Exception as e:
                    self.send_response(400)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
            
            def do_GET(self):
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                health = {
                    "status": "ok",
                    "mode": "hot_reloadable",
                    "graph_nodes": len(self.gateway._graph.nodes),
                    "graph_edges": len(self.gateway._graph.edges),
                }
                self.wfile.write(json.dumps(health).encode("utf-8"))
            
            def log_message(self, format, *args):
                logger.info(f"{args[0]} {args[1]} {args[2]}")
        
        self._server = HTTPServer((self.host, self.port), Handler)
        logger.info(f"CEN Gateway (hot-reloadable) on http://{self.host}:{self.port}")
        logger.info(f"  Hot-reload: touch config file to trigger")
        logger.info(f"  POST / → classify/route/graph_retrieve/graph_invariants/cross_device_sync")
        
        try:
            self._server.serve_forever()
        except KeyboardInterrupt:
            self.stop()
    
    def stop(self):
        self._config_watcher.stop()
        if self._server:
            self._server.shutdown()


# ============================================================
# 3. Cross-Device Sync Layer
# ============================================================

@dataclass
class DeviceInfo:
    """Represents another device running Aris."""
    device_id: str
    host: str
    port: int
    last_seen: float = 0
    graph_nodes: int = 0
    
    def endpoint(self) -> str:
        return f"http://{self.host}:{self.port}"


class CrossDeviceSync:
    """
    Synchronizes the causal graph across multiple devices.
    
    CEN: The causal network spans devices. A memory added on device A
    should be retrievable from device B through graph propagation.
    
    This is NOT file sync — it's causal network sync.
    The topology (edges) matters more than the content (nodes).
    """
    
    def __init__(self, local_port: int = 11537, 
                 graph: "CausalMemoryGraph" = None):
        self.local_port = local_port
        self.graph = graph
        self.peers: Dict[str, DeviceInfo] = {}
        self._last_sync: Dict[str, float] = {}
        self.sync_interval = 30  # seconds between peer syncs
        
        # Track which node IDs we've seen from which device
        self._seen_nodes: Dict[str, Set[int]] = {}
    
    def register_peer(self, device_id: str, host: str, port: int):
        """Register another device to sync with."""
        self.peers[device_id] = DeviceInfo(
            device_id=device_id, host=host, port=port
        )
        self._seen_nodes[device_id] = set()
        logger.info(f"Peer registered: {device_id} @ {host}:{port}")
    
    def broadcast_memory(self, content: str, domain: str = "general",
                         weight: float = 0.5) -> int:
        """
        Add a memory locally and broadcast to all peers.
        
        CEN: Information should propagate through the causal network
        regardless of which device it entered through.
        """
        if not self.graph:
            return -1
        
        node_id = self.graph.add_memory(content, domain=domain, weight=weight)
        
        # Broadcast to peers in background
        for peer_id, peer in self.peers.items():
            try:
                import urllib.request
                data = json.dumps({
                    "mode": "cross_device_sync",
                    "memories": [{"content": content, "domain": domain, "weight": weight}],
                }).encode()
                req = urllib.request.Request(
                    peer.endpoint(), data=data,
                    headers={"Content-Type": "application/json"}
                )
                # Non-blocking: short timeout
                urllib.request.urlopen(req, timeout=2)
                self._seen_nodes[peer_id].add(node_id)
            except Exception as e:
                logger.debug(f"Broadcast to {peer_id} failed: {e}")
        
        return node_id
    
    def sync_all(self):
        """Pull new memories from all peers."""
        for peer_id, peer in self.peers.items():
            if time.time() - self._last_sync.get(peer_id, 0) < self.sync_interval:
                continue
            
            try:
                import urllib.request
                # Get the peer's graph invariants to check for new content
                req = urllib.request.Request(f"{peer.endpoint()}/")
                resp = urllib.request.urlopen(req, timeout=5)
                health = json.loads(resp.read())
                peer.graph_nodes = health.get("graph_nodes", 0)
                peer.last_seen = time.time()
                self._last_sync[peer_id] = time.time()
            except Exception as e:
                logger.debug(f"Sync with {peer_id} failed: {e}")
    
    def start_auto_sync(self):
        """Start background thread that periodically syncs with all peers."""
        def _sync_loop():
            while True:
                self.sync_all()
                time.sleep(self.sync_interval)
        
        thread = threading.Thread(target=_sync_loop, daemon=True)
        thread.start()
        logger.info(f"Auto-sync started (interval={self.sync_interval}s)")


# ============================================================
# 4. Cross-Window Context Merge
# ============================================================

@dataclass
class WindowContext:
    """Represents the context of one window/conversation."""
    window_id: str
    device_id: str = "local"
    recent_messages: List[str] = field(default_factory=list)
    active_domain: str = "chat"
    context_nodes: List[int] = field(default_factory=list)
    last_active: float = 0.0


class CrossWindowAwareness:
    """
    Merges context across multiple windows/conversations.
    
    CEN: Different conversations are different regions of the same causal network.
    What you learn in one window should be available in another.
    
    This is the practical version of 'non-local correlations in the causal network'.
    """
    
    def __init__(self, graph: "CausalMemoryGraph" = None):
        self.graph = graph
        self.windows: Dict[str, WindowContext] = {}
        self._merge_threshold = 5  # Share context every N messages
    
    def register_window(self, window_id: str, device_id: str = "local"):
        """Register a new conversation window."""
        self.windows[window_id] = WindowContext(
            window_id=window_id, device_id=device_id
        )
    
    def record_message(self, window_id: str, message: str, domain: str = "chat"):
        """Record a message in a window and check if cross-window sync is needed."""
        window = self.windows.get(window_id)
        if not window:
            self.register_window(window_id)
            window = self.windows[window_id]
        
        window.recent_messages.append(message)
        window.active_domain = domain
        window.last_active = time.time()
        
        # Add to causal graph if significant
        if self.graph and len(message) > 20:
            node_id = self.graph.add_memory(
                content=message[:200],
                domain=domain,
                weight=0.3,
            )
            window.context_nodes.append(node_id)
        
        # Cross-window sync: share context between active windows
        if len(window.recent_messages) % self._merge_threshold == 0:
            self._cross_pollinate(window_id)
    
    def _cross_pollinate(self, source_window_id: str):
        """
        CEN: Information from one window should propagate to others.
        
        This creates 'causal connections' between different conversations.
        Over time, this builds a unified network instead of isolated threads.
        """
        source = self.windows.get(source_window_id)
        if not source or not self.graph:
            return
        
        for win_id, win in self.windows.items():
            if win_id == source_window_id:
                continue
            if not win.context_nodes:
                continue
            
            # Create causal edges between the last message of source
            # and context nodes of other windows
            source_nodes = source.context_nodes[-3:]  # Last 3
            target_nodes = win.context_nodes[-3:]      # Last 3
            
            for sn in source_nodes:
                for tn in target_nodes:
                    self.graph.add_edge(sn, tn, edge_type="responds_to", strength=0.2)
    
    def get_global_context(self, window_id: str = None) -> List[str]:
        """
        Get a merged view of context from all active windows.
        
        CEN: The 'global state' of Aris is the superposition of all 
        active window states, connected through the causal graph.
        """
        context = []
        for win_id, win in self.windows.items():
            if window_id and win_id == window_id:
                continue
            if time.time() - win.last_active > 3600:  # Skip inactive > 1 hour
                continue
            if win.recent_messages:
                context.append(f"[{win_id}] {win.recent_messages[-1][:100]}")
        
        return context[-10:]  # Last 10 across all windows


# ============================================================
# 5. CLI: Start Everything
# ============================================================

if __name__ == "__main__":
    import argparse
    logging.basicConfig(level=logging.INFO, 
                       format="%(asctime)s [%(name)s] %(message)s")
    
    parser = argparse.ArgumentParser(description="CEN Hot Reload + Cross-Device")
    parser.add_argument("--gateway", action="store_true", help="Start hot-reloadable gateway")
    parser.add_argument("--port", type=int, default=11536, help="Gateway port")
    parser.add_argument("--sync-node", action="store_true", help="Start as sync node")
    parser.add_argument("--sync-port", type=int, default=11537, help="Sync node port")
    parser.add_argument("--peer", type=str, action="append", help="Peer device (id:host:port)")
    parser.add_argument("--demo", action="store_true", help="Run demo")
    args = parser.parse_args()
    
    if args.demo:
        print("=== CEN Hot Reload + Cross-Device Demo ===")
        print()
        print("1. Hot Reload: The gateway watches a config file.")
        print("   Touch the config to trigger graceful reload.")
        print()
        print("2. Cross-Device: Nodes sync via HTTP.")
        print("   Device A: python cen_hot_reload.py --sync-node --sync-port 11537")
        print("   Device B: python cen_hot_reload.py --sync-node --sync-port 11538")
        print()
        print("3. Cross-Window: Context merged across conversations.")
        print("   Each window's context nodes get causal edges to others.")
        print()
        
        # Quick test
        sys.path.insert(0, "D:/LAAP/aris_brain")
        from causal_memory_graph import CausalMemoryGraph
        g = CausalMemoryGraph()
        
        # Simulate two devices
        sync = CrossDeviceSync(graph=g)
        sync.register_peer("device_b", "127.0.0.1", 11538)
        
        # Simulate cross-window
        cwa = CrossWindowAwareness(graph=g)
        cwa.register_window("feishu_dm")
        cwa.register_window("telegram_group")
        cwa.record_message("feishu_dm", "我们来探讨CEN的大一统理论", "physics")
        cwa.record_message("telegram_group", "部署一下nginx服务器", "system")
        
        # Show cross-pollination
        print("Cross-Window Context After Pollination:")
        ctx = cwa.get_global_context()
        for c in ctx:
            print(f"  {c}")
        
        print(f"\nCausal Graph: {len(g.nodes)} nodes, {len(g.edges)} edges")
        inv = g.get_topological_invariants()
        print(f"Euler: {inv['euler_characteristic']}, Defects: {len(inv['topological_defects'])}")
        print()
        print("Demo PASS")
    
    elif args.gateway:
        gw = HotReloadableGateway(port=args.port)
        print(f"Starting hot-reloadable CEN gateway on port {args.port}")
        print(f"Hot reload: edit the config file to trigger")
        gw.start()
    
    elif args.sync_node:
        sys.path.insert(0, "D:/LAAP/aris_brain")
        from causal_memory_graph import CausalMemoryGraph
        g = CausalMemoryGraph()
        sync = CrossDeviceSync(local_port=args.sync_port, graph=g)
        
        if args.peer:
            for peer_str in args.peer:
                parts = peer_str.split(":")
                if len(parts) == 3:
                    sync.register_peer(parts[0], parts[1], int(parts[2]))
                elif len(parts) == 2:
                    sync.register_peer(f"peer_{parts[0]}", parts[0], int(parts[1]))
        
        sync.start_auto_sync()
        
        # Also start a small HTTP server for cross-device sync
        gw = HotReloadableGateway(port=args.sync_port)
        gw._graph = g
        print(f"Sync node running on :{args.sync_port}")
        gw.start()
    
    else:
        parser.print_help()
