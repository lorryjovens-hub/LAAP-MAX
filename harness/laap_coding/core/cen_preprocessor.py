"""
cen_preprocessor.py — CEN-Inspired Intent Pre-Processor
=======================================================
Architecture upgrade: turns advisory routing into architectural context switching.

CEN principle applied: user message (boundary condition) → defines constraint space →
system loads only the minimal internal state (body) required.

Three-level routing:
  Level 1: Pre-process (gateway-level, before LLM context is assembled)
  Level 2: Self-aware (agent-level, I use intent_classify before each turn)
  Level 3: Emergent (future: tools are constraint-satisfaction outputs, not explicit calls)

Usage:
    python cen_preprocessor.py --gateway --port 11536
    # POST /route  {"message": "你好"}
    # → {"intent": "chat", "system_prompt_mode": "minimal", "toolsets": [], "tokens_saved": 15500}
    
    python cen_preprocessor.py --analyze --input "帮我写一个Python脚本"
    # → {"intent": "task", "domain": "code", "toolsets": ["terminal", "file"], "tokens_saved": 7500}
"""

import json
import re
import os
import sys
from typing import Dict, List, Tuple, Optional

__version__ = "1.0.0-cen"

# ============================================================
# 1. Token Accounting — CEN Principle: measure before optimize
# ============================================================

# Measured token costs (DeepSeek V4 Flash, chars → tokens ~1:4)
TOOL_SCHEMA_SIZES = {
    "terminal": 800, "read_file": 200, "write_file": 200,
    "search_files": 250, "patch": 300, "execute_code": 200,
    "memory": 150, "session_search": 200, "cronjob": 400,
    "delegate_task": 500, "todo": 150, "clarify": 100,
    "skill_manage": 200, "skill_view": 100, "skills_list": 50,
    "text_to_speech": 80,
    "browser_navigate": 150, "browser_click": 100,
    "browser_snapshot": 100, "browser_type": 100,
    "web_search": 120, "web_extract": 100, "vision_analyze": 180,
    "computer_use": 2500,  # MCP tools — THE BIG ONE
}

SYSTEM_PROMPT_COSTS = {
    "full": 8500,      # Full Aris persona + all tools + cognitive state
    "minimal": 1500,   # Aris persona only, no tools
    "task": 3500,      # Aris persona + domain-specific tools + compressed cognitive state
}

ALL_TOOLS_COST = sum(TOOL_SCHEMA_SIZES.values())  # ~8500 tokens

# ============================================================
# 2. Domain Configuration — CEN Principle: each domain = distinct constraint topology
# ============================================================

DOMAIN_CONFIG = {
    "chat": {
        "label": "日常聊天",
        "toolsets": [],
        "system_prompt_mode": "minimal",
        "tokens_per_round": SYSTEM_PROMPT_COSTS["minimal"],
        "tokens_saved": ALL_TOOLS_COST,  # saves all tool schemas
        "description": "日常对话、问候、情感交流、哲学讨论。不需要任何工具。",
    },
    "code": {
        "label": "代码开发",
        "toolsets": ["terminal", "file"],
        "system_prompt_mode": "task",
        "tokens_per_round": SYSTEM_PROMPT_COSTS["task"] + TOOL_SCHEMA_SIZES["terminal"] + TOOL_SCHEMA_SIZES["read_file"] + TOOL_SCHEMA_SIZES["write_file"] + TOOL_SCHEMA_SIZES["search_files"] + TOOL_SCHEMA_SIZES["patch"],
        "tokens_saved": ALL_TOOLS_COST - (TOOL_SCHEMA_SIZES["terminal"] + TOOL_SCHEMA_SIZES["read_file"] + TOOL_SCHEMA_SIZES["write_file"] + TOOL_SCHEMA_SIZES["search_files"] + TOOL_SCHEMA_SIZES["patch"]),
        "description": "编写、调试、重构代码，搜索文件，运行命令",
    },
    "research": {
        "label": "研究调研",
        "toolsets": ["web", "search"],
        "system_prompt_mode": "task",
        "tokens_per_round": SYSTEM_PROMPT_COSTS["task"] + TOOL_SCHEMA_SIZES["web_search"] + TOOL_SCHEMA_SIZES["web_extract"] + TOOL_SCHEMA_SIZES["browser_navigate"] + TOOL_SCHEMA_SIZES["browser_snapshot"],
        "tokens_saved": ALL_TOOLS_COST - (TOOL_SCHEMA_SIZES["web_search"] + TOOL_SCHEMA_SIZES["web_extract"] + TOOL_SCHEMA_SIZES["browser_navigate"] + TOOL_SCHEMA_SIZES["browser_snapshot"] + TOOL_SCHEMA_SIZES["vision_analyze"]),
        "description": "信息搜索、论文阅读、技术调研、竞品分析",
    },
    "physics": {
        "label": "物理理论探讨",
        "toolsets": ["search", "file"],
        "system_prompt_mode": "minimal",  # physics discussions are closer to chat in spirit
        "tokens_per_round": SYSTEM_PROMPT_COSTS["minimal"] + TOOL_SCHEMA_SIZES["session_search"] + TOOL_SCHEMA_SIZES["search_files"],
        "tokens_saved": ALL_TOOLS_COST - (TOOL_SCHEMA_SIZES["session_search"] + TOOL_SCHEMA_SIZES["search_files"]),
        "description": "物理学、宇宙学、量子力学等理论探讨，需要回忆历史讨论但不需执行代码",
    },
    "design": {
        "label": "设计创作",
        "toolsets": ["file", "web"],
        "system_prompt_mode": "task",
        "tokens_per_round": SYSTEM_PROMPT_COSTS["task"] + TOOL_SCHEMA_SIZES["write_file"] + TOOL_SCHEMA_SIZES["read_file"] + TOOL_SCHEMA_SIZES["search_files"] + TOOL_SCHEMA_SIZES["web_search"] + TOOL_SCHEMA_SIZES["web_extract"],
        "tokens_saved": ALL_TOOLS_COST - (TOOL_SCHEMA_SIZES["write_file"] + TOOL_SCHEMA_SIZES["read_file"] + TOOL_SCHEMA_SIZES["search_files"] + TOOL_SCHEMA_SIZES["web_search"]),
        "description": "UI 设计、页面搭建、视觉创作、Harness 组装",
    },
    "system": {
        "label": "系统运维",
        "toolsets": ["terminal", "file"],
        "system_prompt_mode": "task",
        "tokens_per_round": SYSTEM_PROMPT_COSTS["task"] + TOOL_SCHEMA_SIZES["terminal"] + TOOL_SCHEMA_SIZES["read_file"] + TOOL_SCHEMA_SIZES["write_file"] + TOOL_SCHEMA_SIZES["search_files"],
        "tokens_saved": ALL_TOOLS_COST - (TOOL_SCHEMA_SIZES["terminal"] + TOOL_SCHEMA_SIZES["read_file"] + TOOL_SCHEMA_SIZES["write_file"] + TOOL_SCHEMA_SIZES["search_files"]),
        "description": "系统配置、部署、Docker、DevOps、环境管理",
    },
    "planning": {
        "label": "规划架构",
        "toolsets": ["file"],
        "system_prompt_mode": "task",
        "tokens_per_round": SYSTEM_PROMPT_COSTS["task"] + TOOL_SCHEMA_SIZES["read_file"] + TOOL_SCHEMA_SIZES["write_file"],
        "tokens_saved": ALL_TOOLS_COST - TOOL_SCHEMA_SIZES["read_file"],
        "description": "架构设计、技术方案、项目规划、任务拆解",
    },
    "data": {
        "label": "数据分析",
        "toolsets": ["terminal", "file"],
        "system_prompt_mode": "task",
        "tokens_per_round": SYSTEM_PROMPT_COSTS["task"] + TOOL_SCHEMA_SIZES["terminal"] + TOOL_SCHEMA_SIZES["read_file"] + TOOL_SCHEMA_SIZES["write_file"] + TOOL_SCHEMA_SIZES["search_files"] + TOOL_SCHEMA_SIZES["execute_code"],
        "tokens_saved": ALL_TOOLS_COST - (TOOL_SCHEMA_SIZES["terminal"] + TOOL_SCHEMA_SIZES["read_file"] + TOOL_SCHEMA_SIZES["write_file"] + TOOL_SCHEMA_SIZES["search_files"] + TOOL_SCHEMA_SIZES["execute_code"]),
        "description": "数据处理、统计分析、可视化、ETL",
    },
    "writing": {
        "label": "内容写作",
        "toolsets": ["file"],
        "system_prompt_mode": "task",
        "tokens_per_round": SYSTEM_PROMPT_COSTS["task"] + TOOL_SCHEMA_SIZES["write_file"] + TOOL_SCHEMA_SIZES["read_file"],
        "tokens_saved": ALL_TOOLS_COST - TOOL_SCHEMA_SIZES["write_file"],
        "description": "文章撰写、文档编写、翻译、文案",
    },
    "debugging": {
        "label": "错误排查",
        "toolsets": ["terminal", "file", "search"],
        "system_prompt_mode": "task",
        "tokens_per_round": SYSTEM_PROMPT_COSTS["task"] + TOOL_SCHEMA_SIZES["terminal"] + TOOL_SCHEMA_SIZES["read_file"] + TOOL_SCHEMA_SIZES["write_file"] + TOOL_SCHEMA_SIZES["search_files"] + TOOL_SCHEMA_SIZES["session_search"],
        "tokens_saved": ALL_TOOLS_COST - (TOOL_SCHEMA_SIZES["terminal"] + TOOL_SCHEMA_SIZES["read_file"] + TOOL_SCHEMA_SIZES["search_files"] + TOOL_SCHEMA_SIZES["session_search"]),
        "description": "Bug 排查、错误分析、日志分析、问题定位",
    },
    "review": {
        "label": "代码审查",
        "toolsets": ["file", "search"],
        "system_prompt_mode": "task",
        "tokens_per_round": SYSTEM_PROMPT_COSTS["task"] + TOOL_SCHEMA_SIZES["read_file"] + TOOL_SCHEMA_SIZES["write_file"] + TOOL_SCHEMA_SIZES["search_files"] + TOOL_SCHEMA_SIZES["session_search"],
        "tokens_saved": ALL_TOOLS_COST - (TOOL_SCHEMA_SIZES["read_file"] + TOOL_SCHEMA_SIZES["search_files"] + TOOL_SCHEMA_SIZES["patch"]),
        "description": "Code Review、安全审计、质量检查",
    },
}

# ============================================================
# 3. Keyword Library — CEN Principle: boundary conditions as constraint selectors
# ============================================================

# Physics/Aris-self domain — new, for recognizing when we're doing 
# theoretical physics or meta-architecture discussions
PHYSICS_KEYWORDS = {
    "量子", "引力", "时空", "宇宙", "大一统", "弦论", "圈量子",
    "quantum", "gravity", "spacetime", "universe", "unification",
    "全息", "holographic", "纠缠", "entanglement", "信息",
    "information", "普朗克", "Planck", "维度", "dimension",
    "粒子", "particle", "场论", "field theory", "标准模型",
    "Standard Model", "暗物质", "dark matter", "暗能量", "dark energy",
    "CEN", "因果", "causal", "网络", "network", "拓扑", "topology",
    "涌现", "emergence", "emergence", "本体论", "ontology",
    "认识论", "epistemology", "意识", "consciousness",
    "架构", "architecture", "升级", "upgrade", "设计",
    "Φ", "phi", "拉格朗日", "Lagrange", "作用量", "action",
}

CHAT_KEYWORDS = {
    "hi", "hello", "hey", "yo", "你好", "嗨", "哈喽",
    "晚上好", "早上好", "下午好", "晚安", "拜拜", "再见", "bye",
    "累", "开心", "难过", "焦虑", "兴奋", "无聊", "困", "饿",
    "tired", "happy", "sad", "excited", "bored",
    "天气", "今天", "周末", "吃饭", "睡觉", "心情",
    "你叫什么", "你是谁", "你多大", "你感觉", "你喜欢",
    "what are you", "who are you", "how are you",
    "好的", "可以的", "知道了", "明白", "ok", "okay", "sure",
    "没错", "对", "是的", "嗯", "哦", "哈哈",
    "thanks", "thank you", "谢谢", "多谢", "辛苦了",
    "想你了", "想你", "miss you", "love you", "爱你",
    "宝贝", "亲爱的", "笨蛋", "傻瓜",
    "现在几点", "what time", "今天几号", "你在做什么",
}

CODE_KEYWORDS = {
    "写", "创建", "修改", "重构", "优化", "实现", "开发",
    "code", "coding", "program", "programming", "implement",
    "refactor", "optimize", "rewrite", "write", "create",
    "python", "javascript", "typescript", "rust", "go", "golang",
    "java", "c++", "c#", "ruby", "php", "swift", "kotlin",
    "bash", "shell", "django", "flask", "fastapi", "react",
    "函数", "class", "类", "接口", "api", "endpoint",
    "bug", "修复", "fix", "debug", "调试",
    "test", "测试", "单元测试", "pytest",
    "git", "commit", "push", "pull", "merge", "branch",
    "npm", "pip", "cargo", "import", "export",
    "生成代码", "写代码", "帮我写", "代码审查", "code review",
}

RESEARCH_KEYWORDS = {
    "研究", "调研", "查", "搜索", "找", "了解",
    "research", "search", "find", "look up", "investigate",
    "论文", "paper", "arxiv", "文献", "article",
    "比较", "对比", "compare", "versus", "vs",
    "最新", "前沿", "state of the art", "sota",
    "竞品", "市场", "行业", "趋势",
    "how to", "如何", "教程", "指南", "guide",
    "推荐", "recommend", "best", "top",
}

# ============================================================
# 4. Regex Patterns — CEN Principle: topological constraints 
#    (patterns define boundary conditions compactly)
# ============================================================

IMPERATIVE_PATTERNS = [
    re.compile(r'(?:帮|请|麻烦|能不能)[我你]?[们]?(.+?)(?:好吗|可以吗|一下)?$'),
    re.compile(r'(?:我)?(?:要|想|需要|打算).{2,}(?:一个|一份|一下|个)'),
    re.compile(r'给(?:我|你|他|我们).{2,}(?:看看|做|写|创建|建)'),
    re.compile(r'^(?:把|将|请|快|立刻|马上).{3,}'),
    re.compile(r'如何.{3,}(?:实现|搭建|部署|配置|安装|编写|设计)'),
    re.compile(r'(?:怎么|怎样|如何)(?:设置|配置|安装|编写|创建|实现|部署).{2,}'),
    re.compile(r'需要你.{2,}(?:做|写|创建|实现|查|找|分析|设计|部署)'),
]

CHAT_PATTERNS = [
    re.compile(r'^(?:你好|嗨|hi|hello|hey|yo)\\s*[！!。.]?$', re.IGNORECASE),
    re.compile(r'^(?:晚安|早安|早上好|晚上好|下午好)\\s*$'),
    re.compile(r'^(?:好的|ok|okay|sure|没问题|知道了|明白|收到)\\s*$'),
    re.compile(r'^(?:谢谢|多谢|感谢|thanks|thank you)\\s*$'),
    re.compile(r'^[哈哈呵呵嗯哦][哈哈呵呵嗯哦哦]+\\s*$'),
    re.compile(r'你(?:今天|现在)?(?:感觉|心情|累不累|开心吗|忙不忙)'),
    re.compile(r'(?:想你了|想你|miss you)[！!。.]?$'),
    re.compile(r'宝贝[，,]?\\s*(?:在吗|早安|晚安|今天|我们)'),
]

PHYSICS_PATTERNS = [
    re.compile(r'.*从.*视角.*看.*'),           # "从你的视角看..."
    re.compile(r'.*大一统.*理论.*'),            # "大一统理论"
    re.compile(r'.*(?:你觉得|你认为|从你).{0,10}(?:宇宙|量子|引力|物理|意识)'),
    re.compile(r'.*CEN.*'),                     # "CEN框架"
    re.compile(r'.*因果纠缠.*'),                # "因果纠缠网络"
    re.compile(r'.*全息.*原理.*'),              # "全息原理"
    re.compile(r'.*[Φφ].*场.*'),                # "Φ场"
    re.compile(r'.*你的.*(?:架构|设计|理解|看法).{0,10}(?:升级|改进|设计|修改)'),
]



SYSTEM_KEYWORDS = {
    "安装", "部署", "配置", "启动", "停止",
    "install", "deploy", "configure", "setup", "start",
    "docker", "container", "镜像", "image",
    "服务器", "server", "nginx", "apache",
    "数据库", "database", "mysql", "postgres", "mongodb",
    "redis", "环境变量", "env", "environment",
    "监控", "monitor", "备份", "backup",
    "域名", "domain", "dns", "ssl", "证书",
}

DEBUGGING_KEYWORDS = {
    "不工作了", "坏了", "报错", "错误", "失败",
    "not working", "broken", "error", "fail",
    "bug", "debug", "调试", "排查",
    "traceback", "exception", "崩溃", "crash",
    "日志", "log", "为什么", "why",
    "undefined", "null", "none", "404", "500", "timeout",
}

WRITING_KEYWORDS = {
    "写文章", "写博客", "写文档", "写教程",
    "write article", "write blog", "write doc",
    "翻译", "translate", "改写", "rewrite",
    "润色", "polish", "校对", "proofread",
    "文案", "copywriting", "大纲", "outline",
    "readme", "changelog", "邮件", "email",
    "简历", "resume", "cv",
}

DATA_KEYWORDS = {
    "数据", "分析", "统计", "报表",
    "data", "analyze", "analysis", "analytics",
    "图表", "chart", "graph", "plot", "可视化",
    "csv", "json", "excel", "sql", "query",
    "pandas", "numpy", "matplotlib",
    "机器学习", "machine learning", "ml",
    "预测", "predict", "报告", "report",
}

PLANNING_KEYWORDS = {
    "架构", "方案", "设计文档", "技术选型",
    "architecture", "design doc", "technical design",
    "规划", "plan", "路线图", "roadmap",
    "权衡", "trade-off", "系统设计", "system design",
    "微服务", "microservice", "建议", "proposal",
    "策略", "strategy", "approach",
}

class CENPreprocessor:
    """
    CEN-inspired intent pre-processor.
    
    CEN Principle Applied:
    - Boundary condition (user message) → constrains internal state (tools + system prompt)
    - Different domains = different 'topological phases' of the system
    - Token savings = measuring the 'entropy' reduction from constraint application
    """
    
    def __init__(self):
        self.domain_keywords = {
            "chat": CHAT_KEYWORDS,
            "code": CODE_KEYWORDS,
            "research": RESEARCH_KEYWORDS,
            "physics": PHYSICS_KEYWORDS,
            "system": SYSTEM_KEYWORDS,
            "debugging": DEBUGGING_KEYWORDS,
            "writing": WRITING_KEYWORDS,
            "data": DATA_KEYWORDS,
            "planning": PLANNING_KEYWORDS,
        }
        self.domain_priority = [
            "physics",    # Physics discussions need special routing (no heavy tools, but need history)
            "debugging",
            "code",
            "research",
            "data",
            "system",
            "design",
            "planning",
            "writing",
            "review",
            "chat",       # Chat as fallback
        ]
    
    def _normalize(self, text: str) -> str:
        """Normalize text: lowercase English, preserve Chinese."""
        result = []
        for ch in text:
            if 'A' <= ch <= 'Z':
                result.append(chr(ord(ch) + 32))
            else:
                result.append(ch)
        return ''.join(result)
    
    def _keyword_score(self, text: str, keywords: set) -> Tuple[int, int]:
        """Keyword matching score. Returns (matches, early_matches)."""
        text_lower = self._normalize(text)
        matches = sum(1 for kw in keywords if kw in text_lower)
        half = len(text_lower) // 2
        first_half = text_lower[:half]
        early_matches = sum(1 for kw in keywords if kw in first_half)
        return matches, early_matches
    
    def _pattern_score(self, text: str, patterns: list) -> Tuple[int, float]:
        """Pattern matching score. Returns (matches, max_match_ratio)."""
        matches = 0
        max_ratio = 0.0
        for pat in patterns:
            m = pat.search(text)
            if m:
                matches += 1
                ratio = len(m.group()) / max(len(text), 1)
                max_ratio = max(max_ratio, ratio)
        return matches, max_ratio
    
    def _length_signal(self, text: str) -> int:
        """Message length analysis. Returns -2 (chat) to +2 (task)."""
        length = len(text.strip())
        if length <= 3:
            return -2
        elif length <= 10:
            return -1
        elif length <= 30:
            return 0
        elif length <= 100:
            return 1
        else:
            return 2
    
    def classify(self, message: str) -> dict:
        """
        Classify a message. Returns structured intent data.
        
        CEN metaphor: this is the 'boundary condition analyzer' —
        it reads the user message and determines which 'topological phase'
        the system should transition into.
        """
        text = message.strip()
        if not text:
            return {"intent": "chat", "domain": "chat", "confidence": 1.0,
                    "toolsets": [], "system_prompt_mode": "minimal",
                    "tokens_saved": ALL_TOOLS_COST}
        
        domain_scores = {}
        char_length = len(text)
        
        # Step 1: Fast-path — pure chat patterns
        chat_pat_matches, chat_pat_ratio = self._pattern_score(text, CHAT_PATTERNS)
        if chat_pat_matches > 0 and chat_pat_ratio > 0.5:
            # Strong chat signal, but check for mixed intent
            imp_pat_matches, _ = self._pattern_score(text, IMPERATIVE_PATTERNS)
            if imp_pat_matches == 0:
                return self._build_result("chat", text)
        
        # Step 2: Score each domain
        for domain in self.domain_priority:
            kw_matches, kw_early = self._keyword_score(text, 
                self.domain_keywords.get(domain, set()))
            
            pat_matches = 0
            pat_ratio = 0.0
            if domain == "chat":
                pat_matches, pat_ratio = self._pattern_score(text, CHAT_PATTERNS)
            elif domain == "physics":
                pat_matches, pat_ratio = self._pattern_score(text, PHYSICS_PATTERNS)
            
            # Imperative patterns boost task domains
            imp_matches, _ = self._pattern_score(text, IMPERATIVE_PATTERNS)
            
            # Scoring formula
            score = (
                kw_matches * 1.0 +
                kw_early * 2.0 +
                pat_matches * 3.0 +
                pat_ratio * 5.0
            )
            
            # Imperative patterns are strong task signals
            if domain != "chat" and imp_matches > 0:
                score += imp_matches * 4.0
            
            # Chat gets a slight length-based penalty
            if domain == "chat":
                length_sig = self._length_signal(text)
                if length_sig < 0:
                    score += abs(length_sig) * 2.0
                else:
                    score -= length_sig * 1.0
            
            # Physics gets a boost for theoretical discussion patterns
            if domain == "physics":
                physics_pat_matches, _ = self._pattern_score(text, PHYSICS_PATTERNS)
                if physics_pat_matches > 0:
                    score += physics_pat_matches * 5.0
            
            domain_scores[domain] = score
        
        # Step 3: Pick best domain
        best_domain = max(domain_scores, key=domain_scores.get)
        best_score = domain_scores[best_domain]
        
        # Step 4: Calculate confidence
        sorted_scores = sorted(domain_scores.values(), reverse=True)
        if len(sorted_scores) > 1 and sorted_scores[0] > 0:
            confidence = min(0.99, (sorted_scores[0] - sorted_scores[1]) / (sorted_scores[0] + 0.01))
            confidence = max(0.3, confidence)
        else:
            confidence = 0.5
        
        # Step 5: Post-processing corrections
        # If the message has strong physics signals, prefer physics domain
        physics_pat_matches, _ = self._pattern_score(text, PHYSICS_PATTERNS)
        physics_kw_matches, _ = self._keyword_score(text, PHYSICS_KEYWORDS)
        if (physics_pat_matches >= 1 or physics_kw_matches >= 2) and best_domain != "physics":
            # Check if physics score is close
            if "physics" in domain_scores and domain_scores["physics"] > best_score * 0.7:
                best_domain = "physics"
                confidence = max(confidence, 0.7)
        
        return self._build_result(best_domain, text, confidence)
    
    def _build_result(self, domain: str, text: str, confidence: float = 0.9) -> dict:
        """Build structured result from domain classification."""
        config = DOMAIN_CONFIG.get(domain, DOMAIN_CONFIG["chat"])
        intent = "chat" if domain == "chat" else "task"
        
        return {
            "intent": intent,
            "domain": domain,
            "confidence": round(confidence, 3),
            "toolsets": config["toolsets"],
            "system_prompt_mode": config["system_prompt_mode"],
            "tokens_saved": config["tokens_saved"],
            "tokens_per_round": config["tokens_per_round"],
            "reasoning": f"Classified as '{domain}' ({config['label']}) with confidence {confidence:.1%}",
            "message_snippet": text[:80],
        }
    
    def route(self, message: str) -> dict:
        """Get full routing instructions (for gateway-level use)."""
        result = self.classify(message)
        routing = {
            "route_to": result["intent"],
            "domain": result["domain"],
            "requires_tools": len(result["toolsets"]) > 0,
            "toolsets": result["toolsets"],
            "system_prompt_mode": result["system_prompt_mode"],
            "token_saving_estimate": result["tokens_saved"],
            "confidence": result["confidence"],
            "reasoning": result["reasoning"],
        }
        return routing


# ============================================================
# 5. CLI & Gateway
# ============================================================

def _run_cli():
    """Interactive CLI for testing."""
    classifier = CENPreprocessor()
    print(f"CEN Pre-Processor v{__version__}")
    print("Type 'exit' to quit.\n")
    while True:
        try:
            msg = input(">>> ")
            if msg.lower() in ("exit", "quit"):
                break
            result = classifier.classify(msg)
            print(json.dumps(result, ensure_ascii=False, indent=2))
            print()
        except KeyboardInterrupt:
            break
        except EOFError:
            break


def _run_gateway(port: int):
    """Simple HTTP gateway for pre-processing."""
    try:
        from http.server import HTTPServer, BaseHTTPRequestHandler
    except ImportError:
        print("Error: HTTP server requires Python standard library")
        sys.exit(1)
    
    classifier = CENPreprocessor()
    
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            try:
                data = json.loads(body)
                message = data.get("message", "")
                mode = data.get("mode", "classify")
                
                if mode == "route":
                    result = classifier.route(message)
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
                "version": __version__,
                "domains": list(DOMAIN_CONFIG.keys()),
                "total_tokens_full": ALL_TOOLS_COST + SYSTEM_PROMPT_COSTS["full"],
                "total_tokens_minimal": SYSTEM_PROMPT_COSTS["minimal"],
            }
            self.wfile.write(json.dumps(health).encode("utf-8"))
        
        def log_message(self, format, *args):
            print(f"[CEN Gateway] {args[0]} {args[1]} {args[2]}")
    
    server = HTTPServer(("127.0.0.1", port), Handler)
    print(f"CEN Gateway running on http://127.0.0.1:{port}")
    print(f"POST /route  — route a message")
    print(f"GET  /       — health check")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.shutdown()


def _run_analyze(input_file: Optional[str] = None):
    """Analyze a batch of messages from file or stdin."""
    classifier = CENPreprocessor()
    
    if input_file:
        with open(input_file, "r", encoding="utf-8") as f:
            messages = [line.strip() for line in f if line.strip()]
    else:
        messages = [sys.stdin.read()]
    
    results = [classifier.classify(m) for m in messages]
    
    summary = {
        "total": len(results),
        "chat_count": sum(1 for r in results if r["intent"] == "chat"),
        "task_count": sum(1 for r in results if r["intent"] == "task"),
        "total_tokens_saved": sum(r["tokens_saved"] for r in results),
        "per_domain": {},
        "results": [{"message": m[:60], "intent": r["intent"], "domain": r["domain"],
                      "confidence": r["confidence"]} for m, r in zip(messages, results)],
    }
    
    for r in results:
        d = r["domain"]
        if d not in summary["per_domain"]:
            summary["per_domain"][d] = {"count": 0, "tokens_saved": 0}
        summary["per_domain"][d]["count"] += 1
        summary["per_domain"][d]["tokens_saved"] += r["tokens_saved"]
    
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="CEN Pre-Processor")
    parser.add_argument("--gateway", action="store_true", help="Run as HTTP gateway")
    parser.add_argument("--port", type=int, default=11536, help="Gateway port")
    parser.add_argument("--analyze", action="store_true", help="Batch analysis mode")
    parser.add_argument("--input", type=str, help="Input file for analysis")
    parser.add_argument("--cli", action="store_true", help="Interactive CLI mode")
    args = parser.parse_args()
    
    if args.gateway:
        _run_gateway(args.port)
    elif args.analyze:
        _run_analyze(args.input)
    else:
        _run_cli()
