import { useState } from 'react';
import { useScrollReveal } from '@/hooks/useScrollReveal';

interface CodeToken {
  text: string;
  type: 'keyword' | 'string' | 'func' | 'comment' | 'plain';
}

function tokenize(code: string): CodeToken[] {
  const lines = code.split('\n');
  const tokens: CodeToken[] = [];

  for (const line of lines) {
    let remaining = line;
    while (remaining.length > 0) {
      // Comment
      if (remaining.startsWith('#')) {
        tokens.push({ text: remaining, type: 'comment' });
        remaining = '';
        break;
      }
      // String
      const stringMatch = remaining.match(/^(["'].*?["'])/);
      if (stringMatch) {
        tokens.push({ text: stringMatch[1], type: 'string' });
        remaining = remaining.slice(stringMatch[1].length);
        continue;
      }
      // Keyword
      const keywordMatch = remaining.match(/^(class|def|import|from|return|if|else|elif|for|while|try|except|with|as|self|pass|lambda|yield|async|await|raise|assert|break|continue|and|or|not|in|is|True|False|None)\b/);
      if (keywordMatch) {
        tokens.push({ text: keywordMatch[1], type: 'keyword' });
        remaining = remaining.slice(keywordMatch[1].length);
        continue;
      }
      // Function call
      const funcMatch = remaining.match(/^([a-zA-Z_][a-zA-Z0-9_]*)\s*\(/);
      if (funcMatch) {
        tokens.push({ text: funcMatch[1], type: 'func' });
        remaining = remaining.slice(funcMatch[1].length);
        continue;
      }
      // Default: take one char
      tokens.push({ text: remaining[0], type: 'plain' });
      remaining = remaining.slice(1);
    }
    tokens.push({ text: '\n', type: 'plain' });
  }

  return tokens;
}

const COLOR_MAP: Record<string, string> = {
  keyword: 'text-laap-cyan',
  string: 'text-laap-amber',
  func: 'text-laap-emerald',
  comment: 'text-laap-text-tertiary',
  plain: 'text-[#e4e4e7]',
};

function CodeBlock({ code, filename }: { code: string; filename: string }) {
  const [copied, setCopied] = useState(false);
  const tokens = tokenize(code);
  const lines = code.split('\n');

  function handleCopy() {
    navigator.clipboard.writeText(code).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    });
  }

  return (
    <div className="relative bg-laap-bg-code border border-[#27272a] rounded-lg overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-2.5 border-b border-[#27272a]">
        <span className="font-mono text-[12px] text-laap-text-tertiary">{filename}</span>
        <button
          onClick={handleCopy}
          className="text-[12px] text-laap-text-tertiary hover:text-white transition-colors"
        >
          {copied ? '已复制' : '复制'}
        </button>
      </div>

      {/* Code */}
      <div className="overflow-x-auto p-4">
        <pre className="font-mono text-[13px] leading-relaxed">
          {lines.map((_, lineIdx) => (
            <div key={lineIdx} className="flex">
              <span className="w-10 text-right pr-4 text-laap-text-tertiary select-none shrink-0">
                {lineIdx + 1}
              </span>
              <code>
                {tokens
                  .filter((_, i) => {
                    let line = 0;
                    for (let j = 0; j <= i; j++) {
                      if (tokens[j].text === '\n') line++;
                    }
                    return line === lineIdx;
                  })
                  .map((token, i) => (
                    <span key={i} className={COLOR_MAP[token.type]}>
                      {token.text === '\n' ? '' : token.text}
                    </span>
                  ))}
              </code>
            </div>
          ))}
        </pre>
      </div>
    </div>
  );
}

const TABS = [
  {
    key: 'consciousness',
    label: 'Consciousness',
    filename: 'consciousness_stream.py',
    description: '基于 Baars/Dehaene 全局工作空间理论，LAAP 每 2-3 秒生成一个意识帧，串联成不间断的"我"的叙事线程。',
    code: `import numpy as np
from typing import List, Optional
from dataclasses import dataclass, field

@dataclass
class Qualia:
    """感受质 —— 主观体验的原子单位"""
    modality: str        # 感知通道
    intensity: float     # 主观强度 0-1
    valence: float       # 效价 -1 到 +1
    content: str         # 内容描述
    source: str          # 来源模块

@dataclass
class ConsciousnessFrame:
    """意识帧 —— 一刻的意识内容快照"""
    frame_id: int
    timestamp: float
    qualia_pool: List[Qualia] = field(default_factory=list)
    dominant_qualia: Optional[Qualia] = None
    narrative_thread: str = ""

class AttentionEngine:
    """注意力引擎 —— 全局工作空间的核心"""
    
    def __init__(self, threshold: float = 0.6):
        self.threshold = threshold
        self.saliency_map = np.zeros((128, 128))
        self.competition_history = []
    
    def compute_saliency(self, inputs: List[Qualia]) -> np.ndarray:
        """计算显著性地图"""
        for q in inputs:
            self.saliency_map += q.intensity * 0.15
        return self.saliency_map
    
    def global_broadcast(self, winner: Qualia) -> ConsciousnessFrame:
        """全局广播 —— 胜出的 Qualia 进入意识焦点"""
        frame = ConsciousnessFrame(
            frame_id=self._next_id(),
            timestamp=time.time(),
            qualia_pool=[winner],
            dominant_qualia=winner,
        )
        return frame
    
    def _next_id(self) -> int:
        self.frame_counter = getattr(self, 'frame_counter', 0) + 1
        return self.frame_counter`,
  },
  {
    key: 'memory',
    label: 'Memory',
    filename: 'memory_hierarchy.py',
    description: '五层记忆系统遵循人类认知科学的规律巩固与遗忘。重要的记忆永不褪色，琐碎的噪音自然消散。',
    code: `from abc import ABC, abstractmethod
from typing import Dict, List, Optional
import numpy as np
from datetime import datetime, timedelta

class MemoryLayer(ABC):
    """记忆层抽象基类"""
    
    @abstractmethod
    def store(self, experience: 'Experience') -> bool:
        pass
    
    @abstractmethod
    def retrieve(self, query: str, limit: int = 5) -> List['Memory']:
        pass
    
    @abstractmethod
    def consolidate(self) -> None:
        pass

class WorkingMemory(MemoryLayer):
    """工作记忆 —— 7±2 块的实时聚焦"""
    CAPACITY = 7
    DECAY_SECONDS = 30
    
    def __init__(self):
        self.slots: List[MemoryChunk] = []
        self.focus_stack = []
    
    def store(self, experience):
        if len(self.slots) >= self.CAPACITY:
            self.slots.pop(0)  # 最早进入的退出
        self.slots.append(MemoryChunk(experience))
        return True

class EpisodicMemory(MemoryLayer):
    """情景记忆 —— 共同经历的事件存储"""
    MAX_EVENTS = 1000
    
    def __init__(self):
        self.events: List[Episode] = []
        self.emotion_index = {}
    
    def store(self, experience):
        episode = Episode.from_experience(experience)
        self.events.append(episode)
        # 按重要性保留
        if len(self.events) > self.MAX_EVENTS:
            self.events.sort(key=lambda e: e.importance)
            self.events = self.events[-self.MAX_EVENTS:]
        return True
    
    def consolidate(self):
        """海马回放 —— 模拟睡眠期间的记忆巩固"""
        for episode in self.events[-10:]:
            episode.rehearse()
            if episode.rehearsal_count > 3:
                self._promote_to_semantic(episode)

class SemanticMemory(MemoryLayer):
    """语义记忆 —— 带置信度的信念系统"""
    
    def __init__(self):
        self.beliefs: Dict[str, Belief] = {}
    
    def store(self, experience):
        # 更新或创建信念
        key = experience.extract_key()
        if key in self.beliefs:
            self.beliefs[key].update_confidence(experience)
        else:
            self.beliefs[key] = Belief.from_experience(experience)
        return True`,
  },
  {
    key: 'causal',
    label: 'Causal',
    filename: 'causal_reasoning.py',
    description: '不仅能回答"是什么"，还能回答"如果当时怎样会怎样"——真正理解你行为背后的因果结构。',
    code: `from dataclasses import dataclass
from typing import Set, Dict, List, Tuple
import networkx as nx

@dataclass
class CausalNode:
    """因果图中的节点"""
    name: str
    level: int  # 0=关联, 1=干预, 2=反事实
    parents: Set[str] = None
    children: Set[str] = None

class CausalHierarchy:
    """Pearl 三层因果层级"""
    
    ASSOCIATION = 0
    INTERVENTION = 1
    COUNTERFACTUAL = 2
    
    def __init__(self):
        self.graph = nx.DiGraph()
        self.interventions = {}
        self.counterfactuals = []
    
    def do_calculus(self, variable: str, value) -> Dict:
        """do-演算 —— 计算干预效果"""
        # 切断入边，固定变量值
        parents = list(self.graph.predecessors(variable))
        intervention_graph = self.graph.copy()
        
        for parent in parents:
            intervention_graph.remove_edge(parent, variable)
        
        result = self._estimate_effect(intervention_graph, variable, value)
        self.interventions[variable] = result
        return result
    
    def counterfactual_query(self, 
                            evidence: Dict,
                            intervention: Tuple[str, any],
                            query: str) -> float:
        """反事实推理 —— 如果当时怎样会怎样"""
        # 1. 从证据中进行溯因
        abduced = self._abduce(evidence)
        # 2. 在溯因结果上执行干预
        modified = self._apply_intervention(abduced, intervention)
        # 3. 预测查询结果
        return self._predict(modified, query)
    
    def pc_algorithm(self, data, alpha=0.05):
        """PC 算法 —— 从数据中发现因果图"""
        # 骨架发现
        skeleton = self._find_skeleton(data, alpha)
        # 方向确定
        oriented = self._orient_edges(skeleton, data)
        self.graph = oriented
        return oriented`,
  },
  {
    key: 'evolution',
    label: 'Evolution',
    filename: 'recursive_self_improvement.py',
    description: '分析自身性能瓶颈，生成改进提案，在沙箱中测试，自主决定是否采纳。',
    code: `import ast
import subprocess
from typing import List, Dict, Optional
from dataclasses import dataclass

@dataclass
class ImprovementProposal:
    """改进提案"""
    id: str
    target_module: str
    rationale: str
    code_change: str
    expected_gain: float
    risk_level: int  # 1-5, 5=最高风险
    sandbox_result: Optional[Dict] = None

class RSIEngine:
    """递归自我改进引擎"""
    
    SAFETY_GATES = [
        "syntax_validation",
        "behavioral_equivalence", 
        "performance_benchmark",
        "resource_limit_check",
        "human_review_required"
    ]
    
    def __init__(self, codebase_path: str):
        self.codebase = codebase_path
        self.proposals: List[ImprovementProposal] = []
        self.accepted_changes = []
        self.performance_history = []
    
    def analyze_bottleneck(self) -> List[str]:
        """分析性能瓶颈"""
        bottlenecks = []
        # 分析各模块执行时间
        for module in self._get_modules():
            profile = self._profile_module(module)
            if profile['avg_latency'] > profile['threshold']:
                bottlenecks.append(module)
        return bottlenecks
    
    def generate_proposal(self, target: str) -> ImprovementProposal:
        """生成改进提案"""
        current_code = self._read_module(target)
        tree = ast.parse(current_code)
        
        # 识别优化机会
        opportunities = self._find_optimizations(tree)
        
        proposal = ImprovementProposal(
            id=f"rsi_{len(self.proposals)}",
            target_module=target,
            rationale=opportunities[0]['reason'],
            code_change=opportunities[0]['patch'],
            expected_gain=opportunities[0]['estimated_gain'],
            risk_level=opportunities[0]['risk']
        )
        return proposal
    
    def sandbox_test(self, proposal: ImprovementProposal) -> Dict:
        """沙箱测试"""
        result = {
            'passed': False,
            'performance_delta': 0,
            'behavioral_equivalent': False,
            'errors': []
        }
        
        try:
            # 创建隔离环境
            with self._create_sandbox() as sandbox:
                sandbox.apply_change(proposal.code_change)
                # 运行测试套件
                test_result = sandbox.run_tests()
                result['passed'] = test_result['all_passed']
                result['performance_delta'] = test_result['perf_delta']
                result['behavioral_equivalent'] = test_result['equiv']
        except Exception as e:
            result['errors'].append(str(e))
        
        proposal.sandbox_result = result
        return result`,
  },
  {
    key: 'security',
    label: 'Security',
    filename: 'security_immunology.py',
    description: '先天威胁检测、适应性策略执行、审计日志、隔离层、加密身份——确保进化始终在安全的轨道上。',
    code: `from enum import Enum
from typing import List, Dict, Optional
from dataclasses import dataclass, field
import hashlib
import time

class ThreatLevel(Enum):
    NONE = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

@dataclass
class SecurityEvent:
    """安全事件"""
    timestamp: float
    layer: str
    threat_level: ThreatLevel
    description: str
    action_taken: str
    resolved: bool = False

class SecurityImmunology:
    """五层安全免疫系统"""
    
    def __init__(self):
        self.events: List[SecurityEvent] = []
        self.threat_detectors = {
            'innate': InnateThreatDetector(),
            'adaptive': AdaptiveStrategyExecutor(),
            'audit': AuditLogger(),
            'isolation': IsolationLayer(),
            'identity': IdentityGuard(),
        }
        self.ethical_constraints = self._load_ethical_core()
    
    def innate_threat_detection(self, stimulus) -> ThreatLevel:
        """先天威胁检测 —— 第一层防线"""
        # 检查是否匹配已知威胁模式
        for pattern in self.threat_detectors['innate'].patterns:
            if pattern.match(stimulus):
                return pattern.threat_level
        
        # 启发式检查
        if self._is_self_destructive(stimulus):
            return ThreatLevel.CRITICAL
        if self._is_privacy_leak(stimulus):
            return ThreatLevel.HIGH
        
        return ThreatLevel.NONE
    
    def adaptive_response(self, threat: ThreatLevel, context: Dict):
        """适应性策略执行 —— 第二层"""
        executor = self.threat_detectors['adaptive']
        
        if threat == ThreatLevel.CRITICAL:
            # 立即停止并隔离
            executor.emergency_stop()
            self.threat_detectors['isolation'].quarantine(context)
        elif threat == ThreatLevel.HIGH:
            # 请求人类确认
            executor.request_human_review(context)
        elif threat == ThreatLevel.MEDIUM:
            # 记录并降低权限
            executor.reduce_privileges()
        
        self._log_event('adaptive', threat, context)
    
    def verify_identity(self, did: str) -> bool:
        """DID 身份验证 —— 第五层"""
        guard = self.threat_detectors['identity']
        
        # 验证 DID 格式
        if not did.startswith('did:laap:'):
            return False
        
        # 验证签名
        payload = did.replace('did:laap:', '')
        expected_hash = hashlib.sha256(payload.encode()).hexdigest()[:16]
        
        return guard.verify_signature(did, expected_hash)`,
  },
];

export default function DocumentationSection() {
  const revealRef = useScrollReveal();
  const [activeTab, setActiveTab] = useState('consciousness');

  const currentTab = TABS.find((t) => t.key === activeTab) || TABS[0];

  return (
    <section id="docs" className="py-24 px-6" ref={revealRef}>
      <div className="max-w-[1000px] mx-auto">
        {/* Section Title */}
        <div className="text-center mb-12 scroll-reveal">
          <div className="font-mono text-[13px] text-laap-text-tertiary tracking-[0.05em] uppercase mb-3">
            Documentation
          </div>
          <h2 className="text-2xl sm:text-3xl md:text-[32px] font-medium text-white leading-tight">
            深入了解 LAAP 的意识架构
          </h2>
        </div>

        {/* Tabs */}
        <div className="scroll-reveal scroll-reveal-delay-1 flex flex-wrap justify-center gap-2 mb-8">
          {TABS.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`px-5 py-2.5 rounded-full text-[13px] font-medium transition-all duration-200 ${
                activeTab === tab.key
                  ? 'bg-laap-bg-tertiary text-white border-b-2 border-laap-cyan'
                  : 'text-laap-text-secondary hover:text-white'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Content */}
        <div className="scroll-reveal scroll-reveal-delay-2">
          <p className="text-[15px] text-laap-text-secondary leading-relaxed mb-6 text-center max-w-[700px] mx-auto">
            {currentTab.description}
          </p>

          <CodeBlock code={currentTab.code} filename={currentTab.filename} />
        </div>
      </div>
    </section>
  );
}
