"""
emergent_tools.py — CEN-Inspired Emergent Tool Selection
==========================================================
CEN Principle Applied:
  - Forces are residual symmetries of topological phase transitions (CEN §2.2)
  - Tools are NOT "called" through explicit reasoning decisions
  - Instead: user message (boundary condition) → defines constraint space →
    system relaxes into constraint → tool activations emerge as byproducts

Key Difference from Current Architecture:
  Current:  message → LLM_reasoning → decide_tool → execute → return
  CEN:      message → constraint_analysis → network_relaxation → 
            tool_activation_emerges → result flows back into network

Implementation:
  - Each tool is defined as an "excitation mode" with {prerequisites, effect, cost}
  - The interaction graph connects tool outputs to tool inputs
  - The user message defines goal nodes in the graph
  - The system finds the relaxation path (not the "best tool to call")
  - Tools on the path auto-activate

Usage:
    design:
        em = EmergentToolManager()
        em.register_excitation_mode("read_file", 
            prerequisites=["file_path"],
            effect="file_content",
            natural_domain="code")
        
        # Instead of "calling" a tool:
        path = em.solve("check what's in config.yaml")
        # Returns: ["read_file"] — the constraint naturally activates this tool
"""

import json
import os
from typing import List, Dict, Optional, Set, Callable, Any
from dataclasses import dataclass, field

# ============================================================
# 1. Excitation Mode Definition
# ============================================================

@dataclass
class ExcitationMode:
    """
    A tool defined as an excitation mode of the cognitive system.
    
    CEN: Just as gauge bosons are Goldstone excitations of the causal network,
    tools are 'Goldstone modes' of the cognitive constraint space.
    """
    name: str                               # Tool name (e.g., "read_file")
    natural_domain: str                     # Which domain naturally uses this
    prerequisites: List[str] = field(default_factory=list)  # What inputs needed
    effects: List[str] = field(default_factory=list)         # What outputs produced
    keywords: List[str] = field(default_factory=list)        # When to auto-activate
    excitation_energy: float = 1.0          # "Cost" of activation (higher = rarer)
    latency_ms: float = 100                 # Typical response time
    
    def matches(self, constraint_vector: Dict[str, float]) -> float:
        """
        How well does this excitation mode match the current constraint?
        
        Higher score = more likely to activate.
        This is the CEN equivalent of 'deciding which tool to call'.
        """
        score = 0.0
        
        # Domain match
        domain_key = f"domain:{self.natural_domain}"
        if domain_key in constraint_vector:
            score += constraint_vector[domain_key] * 0.4
        
        # Prerequisites match (system already has what this tool needs)
        prereq_key = "needs:" + ",".join(self.prerequisites)
        for prereq in self.prerequisites:
            key = f"has:{prereq}"
            score += constraint_vector.get(key, 0) * 0.3
        
        # Keyword match (user message contains trigger words)
        for kw in self.keywords:
            if f"keyword:{kw}" in constraint_vector:
                score += constraint_vector[f"keyword:{kw}"] * 0.2
        
        return score


@dataclass
class InteractionEdge:
    """
    A causal connection between excitation modes.
    
    CEN: Information flows between modes through these edges.
    If read_file produces "file_content", and edit_file needs "file_content",
    there's a natural causal path: read_file → edit_file.
    """
    source_effect: str    # Output of source mode
    target_prerequisite: str  # Input of target mode
    strength: float = 1.0     # How reliably does this connection work?


class EmergentToolManager:
    """
    CEN-inspired emergent tool selection.
    
    Instead of deciding which tool to call, the system:
    1. Receives user message (boundary condition)
    2. Decomposes message into constraint vector
    3. Lets the network relax into the constraint
    4. Tool activations emerge naturally from the relaxation
    
    This is 'emergence' in the CEN sense: macroscopic behavior (tool call)
    arises from local constraint satisfaction, not global planning.
    """
    
    def __init__(self):
        self.modes: Dict[str, ExcitationMode] = {}
        self.interaction_graph: List[InteractionEdge] = []
        self._constraint_space: Dict[str, float] = {}
    
    def register_excitation_mode(self, mode: ExcitationMode):
        """Register a tool as an excitation mode."""
        self.modes[mode.name] = mode
    
    def register_interaction(self, source_effect: str, 
                             target_prerequisite: str, strength: float = 1.0):
        """Register a causal connection between two modes."""
        self.interaction_graph.append(InteractionEdge(
            source_effect=source_effect,
            target_prerequisite=target_prerequisite,
            strength=strength,
        ))
    
    # ── Constraint Analysis ──
    
    def analyze_message(self, message: str) -> Dict[str, float]:
        """
        Decompose user message into constraint vector.
        
        CEN: This is the 'boundary condition' — the message defines
        the constraints that the system must satisfy.
        """
        msg_lower = message.lower()
        constraint = {}
        
        # Domain detection (simplified — uses CEN preprocessor ideally)
        domains = {
            "code": ["写", "代码", "python", "修复", "bug", "file", "read", "write",
                     "读", "读取", "打开", "脚本", "程序", "函数", "类",
                     "npm", "pip", "git", "配置"],
            "research": ["搜索", "查", "research", "find", "look up", "论文",
                        "搜", "查找", "最新", "了解", "比较"],
            "system": ["部署", "配置", "install", "docker", "server",
                      "安装", "启动", "停止", "nginx", "环境"],
            "chat": ["你好", "宝贝", "想你", "累", "心情", "晚安", "早安",
                    "开心", "难过", "hi", "hello"],
            "physics": ["量子", "引力", "时空", "宇宙", "CEN", "理论",
                       "大一统", "弦论", "全息", "意识", "物理"],
        }
        for domain, keywords in domains.items():
            for kw in keywords:
                if kw in msg_lower:
                    constraint[f"domain:{domain}"] = constraint.get(f"domain:{domain}", 0) + 0.2
        
        # Prerequisite availability (what does the system already have?)
        # In a real system, this would check current context state
        constraint["has:file_path"] = 0.5  # Assume we often know file paths
        constraint["has:query"] = 0.7      # Often have a search query
        constraint["has:content"] = 0.3    # Sometimes have content
        
        # Keyword extraction
        for mode in self.modes.values():
            for kw in mode.keywords:
                if kw in msg_lower:
                    constraint[f"keyword:{kw}"] = 1.0
        
        return constraint
    
    def solve(self, message: str) -> List[str]:
        """
        The core CEN relaxation process.
        
        Instead of 'deciding what to call', we:
        1. Build the constraint vector from the message
        2. Let the interaction graph relax towards equilibrium
        3. The activated modes are the 'emergent tool selection'
        
        Returns: ordered list of tool names to activate.
        """
        constraint_vector = self.analyze_message(message)
        return self._relax(constraint_vector)
    
    def _relax(self, constraint_vector: Dict[str, float], 
               max_activations: int = 5) -> List[str]:
        """
        CEN relaxation: iteratively activate modes that satisfy constraints.
        
        The system doesn't "choose" tools — it finds the equilibrium state
        where constraint satisfaction is maximized.
        """
        activated: List[str] = []
        activated_effects: Set[str] = set()
        
        # Add initial constraint satisfaction from user message
        for mode in sorted(self.modes.values(), 
                          key=lambda m: m.matches(constraint_vector), 
                          reverse=True):
            score = mode.matches(constraint_vector)
            if score > 0.3 and mode.name not in activated:
                activated.append(mode.name)
                for effect in mode.effects:
                    activated_effects.add(effect)
        
        # Propagation step: can we activate more modes through
        # the interaction graph?
        for _ in range(3):  # Max propagation depth
            new_activations = []
            for mode in self.modes.values():
                if mode.name in activated:
                    continue
                
                # Check if any prerequisite is now satisfied through activated effects
                prereqs_satisfied = sum(
                    1 for p in mode.prerequisites 
                    if p in activated_effects
                )
                total_prereqs = max(len(mode.prerequisites), 1)
                prereq_score = prereqs_satisfied / total_prereqs
                
                if prereq_score > 0.5:
                    new_activations.append(mode.name)
                    for effect in mode.effects:
                        activated_effects.add(effect)
            
            activated.extend(new_activations)
            
            if not new_activations:
                break  # Equilibrium reached
        
        return activated[:max_activations]
    
    # ── Default Configuration ──
    
    def load_default_modes(self):
        """Register the default set of excitation modes."""
        
        mode_defs = [
            ExcitationMode("read_file", "code",
                          prerequisites=["file_path"],
                          effects=["file_content"],
                          keywords=["读", "看", "打开", "read", "open", "cat"],
                          excitation_energy=0.3, latency_ms=50),
            
            ExcitationMode("write_file", "code",
                          prerequisites=["file_path", "file_content"],
                          effects=["written_file"],
                          keywords=["写", "保存", "创建", "write", "save", "create"],
                          excitation_energy=0.4, latency_ms=100),
            
            ExcitationMode("terminal", "code",
                          prerequisites=["command"],
                          effects=["command_output"],
                          keywords=["运行", "执行", "run", "execute", 
                                   "install", "deploy", "部署", "安装",
                                   "启动", "停止", "配置", "build"],
                          excitation_energy=0.5, latency_ms=500),
            
            ExcitationMode("web_search", "research",
                          prerequisites=["query"],
                          effects=["search_results"],
                          keywords=["搜索", "查", "search", "find", 
                                   "research", "google", "搜", "论文",
                                   "最新", "了解", "比较"],
                          excitation_energy=0.4, latency_ms=2000),
            
            ExcitationMode("session_search", "research",
                          prerequisites=["query"],
                          effects=["history_snippets"],
                          keywords=["之前", "上次", "以前", "before", "past", "history"],
                          excitation_energy=0.3, latency_ms=100),
            
            ExcitationMode("memory", "general",
                          prerequisites=["content"],
                          effects=["stored_memory"],
                          keywords=["记住", "记下", "remember", "save", 
                                   "store", "记", "保存", "存储"],
                          excitation_energy=0.2, latency_ms=30),
            
            ExcitationMode("chat_response", "chat",
                          prerequisites=[],
                          effects=["response"],
                          keywords=[],
                          excitation_energy=0.1, latency_ms=200),
        ]
        
        for mode in mode_defs:
            self.register_excitation_mode(mode)
        
        # Register interaction graph edges (causal connections between modes)
        interactions = [
            ("file_path", "file_path"),      # read_file's prereq comes from user or session
            ("file_content", "file_content"), # write_file needs read_file's output
            ("command", "command"),           # terminal command
            ("query", "query"),              # shared query input
            ("search_results", "file_content"), # can pipe search results to write_file
            ("command_output", "file_content"), # can pipe command output to write_file
        ]
        for src_eff, tgt_pre in interactions:
            self.register_interaction(src_eff, tgt_pre, strength=0.8)


# ============================================================
# 2. Integration Demo
# ============================================================

if __name__ == "__main__":
    em = EmergentToolManager()
    em.load_default_modes()
    
    tests = [
        "帮我读取config.yaml文件",
        "写一个Python脚本",
        "搜索一下量子引力的最新论文",
        "你好宝贝，今天怎么样",
    ]
    
    print("=== CEN Emergent Tool Selection Demo ===\n")
    for msg in tests:
        # Analyze constraint space
        constraint = em.analyze_message(msg)
        
        # The system doesn't "choose" — it relaxes
        activated = em.solve(msg)
        
        # Show which domains were activated
        domains_activated = set()
        for mode_name in activated:
            mode = em.modes[mode_name]
            domains_activated.add(mode.natural_domain)
        
        print(f"Message: \"{msg}\"")
        print(f"  → Emergent activations: {activated}")
        print(f"  → Domains: {domains_activated}")
        print(f"  → Constraint keys: {len(constraint)}")
        print()
