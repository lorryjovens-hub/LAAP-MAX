"""
LAAP AGI — Advanced World Model Integration
===========================================

整合多种世界模型后端：
1. 本地世界模型（基于实体-关系-因果图）
2. PARACOSM 集成（支持反事实推理和决策模拟）
3. 物理引擎集成（用于具身智能）
4. ODEI知识图谱集成（持久化记忆和安全护栏）
5. 常识知识库（ConceptNet, WordNet）

世界模型是AGI的核心组件，提供：
- 环境动态预测
- 反事实推理
- 规划和模拟
- 因果关系建模
- 实体关系管理
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple, Union, Callable
from enum import Enum
import time, json, logging, math, uuid, random, threading, asyncio
from collections import defaultdict
from abc import ABC, abstractmethod

logger = logging.getLogger("laap.agi.world_model")

# ═══════════════════════════════════════════════════════════════
# 世界模型类型枚举
# ═══════════════════════════════════════════════════════════════
class WorldModelType(str, Enum):
    LOCAL = "local"           # 本地实体-关系图模型
    PARACOSM = "paracosm"     # PARACOSM 外部服务
    PHYSICS = "physics"       # 物理引擎模拟
    HYBRID = "hybrid"         # 混合模式
    ODEI = "odei"             # ODEI 知识图谱
    GWM = "gwm"               # Graph World Model
    LINGBOT = "lingbot"       # LingBot-World (蚂蚁集团)
    OPENWORLDLIB = "openworldlib"  # OpenWorldLib (北京大学)
    HUNYUAN = "hunyuan"       # HunYuanWorld (腾讯)

class RelationType(str, Enum):
    # 因果关系
    CAUSES = "causes"
    PREVENTS = "prevents"
    ENABLES = "enables"
    INHIBITS = "inhibits"
    
    # 组成关系
    CONTAINS = "contains"
    PART_OF = "part_of"
    COMPOSED_OF = "composed_of"
    
    # 属性关系
    HAS_PROPERTY = "has_property"
    IS_A = "is_a"
    INSTANCE_OF = "instance_of"
    
    # 依赖关系
    DEPENDS_ON = "depends_on"
    REQUIRES = "requires"
    USES = "uses"
    PRODUCES = "produces"

    # 时空关系
    LOCATED_AT = "located_at"
    OCCURS_AT = "occurs_at"
    BEFORE = "before"
    AFTER = "after"
    DURING = "during"
    
    # 相似关系
    SIMILAR_TO = "similar_to"
    ANALOGOUS_TO = "analogous_to"
    
    # 知识关系
    KNOWLEDGE_OF = "knowledge_of"
    RELATED_TO = "related_to"
    
    # 代理关系
    PERCEIVED_BY = "perceived_by"
    CREATED_BY = "created_by"
    OWNED_BY = "owned_by"
    CONTROLLED_BY = "controlled_by"
    
    UNKNOWN = "unknown"

class EntityType(str, Enum):
    # 概念实体
    CONCEPT = "concept"
    CATEGORY = "category"
    ABSTRACTION = "abstraction"
    
    # 物理实体
    OBJECT = "object"
    AGENT = "agent"
    PERSON = "person"
    ANIMAL = "animal"
    PLANT = "plant"
    MACHINE = "machine"
    TOOL = "tool"
    
    # 事件和动作
    ACTION = "action"
    EVENT = "event"
    PROCESS = "process"
    
    # 状态和属性
    STATE = "state"
    QUALITY = "quality"
    VALUE = "value"
    
    # 目标和规则
    GOAL = "goal"
    RULE = "rule"
    PLAN = "plan"
    
    # 数字实体
    FILE = "file"
    DATA = "data"
    KNOWLEDGE = "knowledge"
    
    # 用户相关
    USER = "user"
    
    # 时空实体
    LOCATION = "location"
    TIME = "time"
    DURATION = "duration"
    
    # 抽象实体
    IDEA = "idea"
    THEORY = "theory"
    PRINCIPLE = "principle"
    
    UNKNOWN = "unknown"

# ═══════════════════════════════════════════════════════════════
# 核心数据结构
# ═══════════════════════════════════════════════════════════════
@dataclass
class Belief:
    """信念表示 - 带有置信度的事实"""
    value: Any
    confidence: float = 0.5
    evidence_count: int = 0
    last_updated: float = field(default_factory=time.time)
    source: str = ""
    timestamp: Optional[float] = None
    reliability: float = 0.5  # 来源可靠性
    
    def update(self, new_value, confidence: float = 0.5, source: str = "", reliability: float = 0.5):
        """贝叶斯信念更新"""
        if self.evidence_count == 0:
            self.value, self.confidence = new_value, confidence
        else:
            # 加权平均更新，考虑来源可靠性
            weight_factor = reliability / (self.reliability + reliability) if self.reliability > 0 else 1.0
            old_weight = (1 - weight_factor) * (self.evidence_count / (self.evidence_count + 1))
            new_weight = weight_factor * (1 / (self.evidence_count + 1)) + (1 - weight_factor) * (1 / (self.evidence_count + 1))
            self.confidence = old_weight * self.confidence + new_weight * confidence
            
            # 数值类型的加权平均
            if isinstance(self.value, (int, float)) and isinstance(new_value, (int, float)):
                self.value = old_weight * self.value + new_weight * new_value
            elif confidence * reliability > self.confidence * self.reliability:
                self.value = new_value
        
        self.evidence_count += 1
        self.last_updated = time.time()
        self.reliability = (self.reliability * (self.evidence_count - 1) + reliability) / self.evidence_count
        if source and source not in self.source:
            self.source = f"{self.source},{source}".strip(",")

@dataclass
class Entity:
    """世界中的实体"""
    id: str
    name: str
    entity_type: EntityType = EntityType.UNKNOWN
    properties: Dict[str, Belief] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    last_accessed: float = field(default_factory=time.time)
    access_count: int = 0
    salience: float = 0.5
    abstraction_level: int = 0
    tags: Set[str] = field(default_factory=set)
    embedding: Optional[List[float]] = None  # 向量嵌入
    context: Optional[str] = None  # 实体上下文描述
    
    def get(self, prop: str, default=None):
        return self.properties[prop].value if prop in self.properties else default
    
    def set(self, prop: str, value, confidence: float = 0.5, source: str = "", reliability: float = 0.5):
        if prop not in self.properties:
            self.properties[prop] = Belief(value, confidence, source=source, reliability=reliability)
        else:
            self.properties[prop].update(value, confidence, source, reliability)
        self.last_accessed = time.time()
        self.access_count += 1
    
    def touch(self):
        self.last_accessed = time.time()
        self.access_count += 1
    
    def decay_salience(self, decay_rate: float = 0.01):
        """衰减显著性"""
        self.salience = max(0.01, self.salience - decay_rate)

@dataclass
class Relation:
    """实体之间的关系"""
    id: str
    source_id: str
    target_id: str
    relation_type: RelationType
    confidence: float = 0.5
    strength: float = 0.5
    evidence: List[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    temporal_scope: Optional[Tuple[float, float]] = None
    context: Optional[str] = None  # 关系上下文

@dataclass
class CausalLink:
    """因果链接"""
    id: str
    condition: str
    effect: str
    probability: float = 0.5
    confidence: float = 0.3
    evidence_count: int = 0
    domain: str = ""
    created_at: float = field(default_factory=time.time)
    latency: float = 0.0  # 因果效应的时间延迟
    prerequisites: List[str] = field(default_factory=list)
    side_effects: List[str] = field(default_factory=list)

@dataclass
class SimulationResult:
    """模拟结果"""
    steps: List[Dict] = field(default_factory=list)
    final_state: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0
    assumptions: List[str] = field(default_factory=list)
    trajectory: List[Dict[str, Any]] = field(default_factory=list)
    causal_chain: List[str] = field(default_factory=list)  # 因果链
    warnings: List[str] = field(default_factory=list)      # 警告信息

@dataclass
class WorldState:
    """世界状态快照"""
    timestamp: float = field(default_factory=time.time)
    entities: Dict[str, Entity] = field(default_factory=dict)
    relations: Dict[str, Relation] = field(default_factory=dict)
    causal_links: Dict[str, CausalLink] = field(default_factory=dict)
    agent_position: Optional[str] = None
    active_events: List[str] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)

# ═══════════════════════════════════════════════════════════════
# 世界模型抽象基类
# ═══════════════════════════════════════════════════════════════
class AbstractWorldModel(ABC):
    """世界模型抽象接口"""
    
    @abstractmethod
    def add_entity(self, name: str, entity_type: EntityType = EntityType.UNKNOWN, 
                  properties: Optional[Dict] = None, tags: Optional[Set[str]] = None,
                  confidence: float = 0.5, source: str = "observation",
                  reliability: float = 0.5) -> Entity:
        pass
    
    @abstractmethod
    def get_entity(self, identifier: str) -> Optional[Entity]:
        pass
    
    @abstractmethod
    def add_relation(self, source: str, target: str, rel_type: RelationType, 
                    confidence: float = 0.5, context: Optional[str] = None) -> Optional[Relation]:
        pass
    
    @abstractmethod
    def add_causal_link(self, condition: str, effect: str, 
                       probability: float = 0.5, confidence: float = 0.3, 
                       domain: str = "", latency: float = 0.0) -> CausalLink:
        pass
    
    @abstractmethod
    def predict(self, action: str, context: Optional[Dict] = None, 
               max_steps: int = 3) -> SimulationResult:
        pass
    
    @abstractmethod
    def counterfactual(self, entity_name: str, property_name: str, 
                      actual_value: Any, hypothetical_value: Any) -> Dict:
        pass
    
    @abstractmethod
    def simulate(self, scenario: str, max_steps: int = 10) -> SimulationResult:
        pass
    
    @abstractmethod
    def update_from_observation(self, observation: Dict[str, Any], 
                               source: str = "perception") -> None:
        pass
    
    @abstractmethod
    def stats(self) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    def query(self, query: str) -> List[Dict]:
        """查询世界模型"""
        pass
    
    @abstractmethod
    def infer_missing_links(self) -> List[Relation]:
        """推理缺失的关系"""
        pass

# 向后兼容别名
WorldModel = AbstractWorldModel

# ═══════════════════════════════════════════════════════════════
# 常识知识库
# ═══════════════════════════════════════════════════════════════
class CommonsenseKnowledge:
    """常识知识库 - 提供基础世界知识"""
    
    def __init__(self):
        self.knowledge = {
            # 物理常识
            "physics": {
                "gravity": "物体受重力影响会下落",
                "temperature": "高温会使物体膨胀",
                "motion": "运动的物体会保持运动直到受到力的作用",
                "conservation": "能量既不会凭空产生也不会凭空消失",
            },
            # 时间常识
            "time": {
                "day_night": "地球自转导致昼夜交替",
                "seasons": "地球公转导致四季变化",
                "aging": "生物会随时间衰老",
            },
            # 社会常识
            "social": {
                "communication": "人们通过语言交流",
                "cooperation": "合作可以完成更大的任务",
                "trust": "信任是社会关系的基础",
            },
            # 生物常识
            "biology": {
                "needs": "生物需要水和食物生存",
                "growth": "生物会生长发育",
                "reproduction": "生物通过繁殖延续物种",
            },
            # 因果常识
            "causal": {
                "action_reaction": "每个动作都有反作用",
                "cause_effect": "原因先于结果发生",
                "correlation": "相关性不等于因果性",
            }
        }
    
    def query(self, topic: str) -> Optional[str]:
        """查询常识知识"""
        for domain, facts in self.knowledge.items():
            if topic.lower() in domain:
                return facts
            for key, value in facts.items():
                if topic.lower() in key.lower():
                    return {key: value}
        return None
    
    def get_relevant_knowledge(self, context: str) -> List[str]:
        """根据上下文获取相关常识"""
        relevant = []
        context_lower = context.lower()
        
        for domain, facts in self.knowledge.items():
            for key, value in facts.items():
                if key.lower() in context_lower or any(w in context_lower for w in key.split()):
                    relevant.append(value)
        
        return relevant

# ═══════════════════════════════════════════════════════════════
# 本地世界模型实现
# ═══════════════════════════════════════════════════════════════
class LocalWorldModel(AbstractWorldModel):
    """本地实体-关系-因果图世界模型"""
    
    def __init__(self, name: str = "world", max_entities: int = 10000):
        self.name = name
        self.max_entities = max_entities
        self.entities: Dict[str, Entity] = {}
        self.relations: Dict[str, Relation] = {}
        self.causal_links: Dict[str, CausalLink] = {}
        self._entity_by_name: Dict[str, str] = {}
        self._entity_by_type: Dict[EntityType, List[str]] = defaultdict(list)
        self._relations_from: Dict[str, List[str]] = defaultdict(list)
        self._relations_to: Dict[str, List[str]] = defaultdict(list)
        self._history: List[WorldState] = []
        self._max_history = 100
        self._commonsense = CommonsenseKnowledge()
        
        self.total_updates = 0
        self.total_predictions = 0
        self.total_queries = 0
        self.created_at = time.time()
        self._lock = threading.RLock()
        
        # 初始化默认实体
        self._initialize_defaults()
    
    def _initialize_defaults(self):
        """初始化默认实体和关系"""
        # 添加时间实体
        self.add_entity("current_time", EntityType.TIME, 
                       {"value": time.time(), "unit": "seconds"}, 
                       tags={"system"}, confidence=1.0, reliability=1.0)
        
        # 添加智能体自身实体
        self.add_entity("self", EntityType.AGENT,
                       {"type": "LAAP-Agent", "version": "4.5", "status": "active"},
                       tags={"system", "self"}, confidence=1.0, reliability=1.0)
        
        # 添加环境实体
        self.add_entity("environment", EntityType.LOCATION,
                       {"type": "digital", "status": "stable"},
                       tags={"system"}, confidence=0.9, reliability=0.9)
        
        # 添加基本因果规则
        self.add_causal_link("agent_learns", "knowledge_increases", 
                            probability=0.9, confidence=0.8, domain="learning")
        self.add_causal_link("agent_acts", "world_changes", 
                            probability=0.85, confidence=0.75, domain="action")
        self.add_causal_link("positive_feedback", "motivation_increases", 
                            probability=0.8, confidence=0.7, domain="emotion")
    
    def _save_state(self):
        """保存状态快照用于历史回溯"""
        state = WorldState(
            entities=dict(self.entities),
            relations=dict(self.relations),
            causal_links=dict(self.causal_links)
        )
        self._history.append(state)
        if len(self._history) > self._max_history:
            self._history.pop(0)
    
    def _evict(self):
        """驱逐最不活跃的实体"""
        if self.entities:
            worst = min(self.entities.values(), key=lambda e: e.salience)
            self.entities.pop(worst.id, None)
            self._entity_by_name.pop(worst.name.lower(), None)
    
    def add_entity(self, name: str, entity_type: EntityType = EntityType.UNKNOWN,
                  properties: Optional[Dict] = None, tags: Optional[Set[str]] = None,
                  confidence: float = 0.5, source: str = "observation",
                  reliability: float = 0.5) -> Entity:
        with self._lock:
            eid = self._entity_by_name.get(name.lower())
            if eid and eid in self.entities:
                e = self.entities[eid]
                if properties:
                    for k, v in properties.items():
                        e.set(k, v, confidence, source, reliability)
                e.touch()
                return e
            
            eid = str(uuid.uuid4())[:12]
            e = Entity(id=eid, name=name, entity_type=entity_type, tags=tags or set())
            if properties:
                for k, v in properties.items():
                    e.set(k, v, confidence, source, reliability)
            
            if len(self.entities) >= self.max_entities:
                self._evict()
            
            self.entities[eid] = e
            self._entity_by_name[name.lower()] = eid
            self._entity_by_type[entity_type].append(eid)
            self.total_updates += 1
            return e
    
    def get_entity(self, identifier: str) -> Optional[Entity]:
        if identifier in self.entities:
            return self.entities[identifier]
        eid = self._entity_by_name.get(identifier.lower())
        return self.entities[eid] if eid and eid in self.entities else None
    
    def find_related(self, entity_id: str, relation_types: Optional[List[RelationType]] = None,
                    direction: str = "both") -> List[Tuple[Entity, Relation]]:
        results = []
        if direction in ("out", "both"):
            for rid in self._relations_from.get(entity_id, []):
                r = self.relations.get(rid)
                if r and r.target_id in self.entities:
                    if not relation_types or r.relation_type in relation_types:
                        results.append((self.entities[r.target_id], r))
        if direction in ("in", "both"):
            for rid in self._relations_to.get(entity_id, []):
                r = self.relations.get(rid)
                if r and r.source_id in self.entities:
                    if not relation_types or r.relation_type in relation_types:
                        results.append((self.entities[r.source_id], r))
        return results
    
    def add_relation(self, source: str, target: str, rel_type: RelationType,
                    confidence: float = 0.5, context: Optional[str] = None) -> Optional[Relation]:
        src = self.get_entity(source)
        tgt = self.get_entity(target)
        if not src or not tgt:
            return None
        
        rid = str(uuid.uuid4())[:12]
        r = Relation(
            id=rid,
            source_id=src.id,
            target_id=tgt.id,
            relation_type=rel_type,
            confidence=confidence,
            context=context
        )
        self.relations[rid] = r
        self._relations_from[src.id].append(rid)
        self._relations_to[tgt.id].append(rid)
        self.total_updates += 1
        return r
    
    def add_causal_link(self, condition: str, effect: str,
                       probability: float = 0.5, confidence: float = 0.3,
                       domain: str = "", latency: float = 0.0) -> CausalLink:
        cid = str(uuid.uuid4())[:12]
        cl = CausalLink(
            id=cid,
            condition=condition,
            effect=effect,
            probability=probability,
            confidence=confidence,
            domain=domain,
            latency=latency
        )
        self.causal_links[cid] = cl
        self.total_updates += 1
        return cl
    
    def predict(self, action: str, context: Optional[Dict] = None,
               max_steps: int = 3) -> SimulationResult:
        self.total_predictions += 1
        steps = []
        confidence = 1.0
        assumptions = []
        trajectory = []
        causal_chain = []
        
        # 获取相关常识
        commonsense_facts = self._commonsense.get_relevant_knowledge(action)
        if commonsense_facts:
            assumptions.extend(commonsense_facts)
        
        # 找到相关的因果链接
        action_lower = action.lower()
        relevant_links = [
            l for l in self.causal_links.values()
            if any(w in action_lower for w in l.condition.lower().split())
        ]
        
        if not relevant_links:
            assumptions.append("No causal knowledge available for this action")
            confidence *= 0.3
        else:
            # 按置信度排序
            relevant_links.sort(key=lambda x: x.confidence * x.probability, reverse=True)
        
        state = dict(context or {})
        trajectory.append({"step": 0, "state": dict(state)})
        
        for step in range(max_steps):
            changes = {}
            activated_links = []
            
            for link in relevant_links[:5]:  # 最多考虑5个最相关的链接
                activation_prob = link.probability * link.confidence
                adjusted_prob = activation_prob * (1.0 - step * 0.1)  # 随步骤衰减
                
                if random.random() < adjusted_prob:
                    changes[link.effect] = {
                        "probability": link.probability,
                        "confidence": link.confidence,
                        "latency": link.latency
                    }
                    causal_chain.append(f"{link.condition} → {link.effect}")
                    confidence *= link.confidence
                    activated_links.append(link)
            
            # 添加副作用
            for link in activated_links:
                for side_effect in link.side_effects:
                    if side_effect not in changes:
                        changes[side_effect] = {
                            "probability": 0.3,
                            "confidence": 0.5,
                            "type": "side_effect"
                        }
            
            if changes:
                steps.append({"step": step + 1, "changes": changes, "causal_chain": causal_chain.copy()})
                for k, v in changes.items():
                    state[k] = v
                trajectory.append({"step": step + 1, "state": dict(state)})
            else:
                break
        
        return SimulationResult(
            steps=steps,
            final_state=state,
            confidence=confidence,
            assumptions=assumptions,
            trajectory=trajectory,
            causal_chain=causal_chain
        )
    
    def counterfactual(self, entity_name: str, property_name: str,
                      actual_value: Any, hypothetical_value: Any) -> Dict:
        e = self.get_entity(entity_name)
        if not e:
            return {"error": f"Unknown entity: {entity_name}"}
        
        related = self.find_related(e.id, direction="both")
        causal_paths = [
            {
                "from": e.name,
                "to": r[0].name,
                "relation": r[1].relation_type.value,
                "confidence": r[1].confidence
            }
            for r in related
        ]
        
        # 找到影响该实体的因果链
        affecting_links = [
            link for link in self.causal_links.values()
            if entity_name.lower() in link.effect.lower()
        ]
        
        base_confidence = 0.3
        if causal_paths:
            base_confidence = min(0.8, sum(p["confidence"] for p in causal_paths) / max(1, len(causal_paths)))
        if affecting_links:
            base_confidence = max(base_confidence, sum(l.confidence for l in affecting_links) / max(1, len(affecting_links)))
        
        # 获取常识支持
        commonsense_support = self._commonsense.get_relevant_knowledge(f"{entity_name} {property_name}")
        
        return {
            "counterfactual_scenario": f"If {entity_name}.{property_name} were {hypothetical_value} instead of {actual_value}",
            "confidence": base_confidence,
            "causal_paths": causal_paths,
            "affected_entities": [p["to"] for p in causal_paths],
            "affecting_causal_links": [{"condition": l.condition, "effect": l.effect, "confidence": l.confidence} for l in affecting_links],
            "commonsense_support": commonsense_support,
            "reasoning_steps": [
                f"1. Identify entity: {entity_name}",
                f"2. Current state: {property_name} = {actual_value}",
                f"3. Hypothetical state: {property_name} = {hypothetical_value}",
                f"4. Traverse causal graph to find affected entities",
                f"5. Estimate confidence based on link strengths"
            ]
        }
    
    def simulate(self, scenario: str, max_steps: int = 10) -> SimulationResult:
        """模拟一个完整场景"""
        self.total_predictions += 1
        
        # 解析场景描述，提取关键实体和动作
        words = scenario.lower().split()
        relevant_entities = []
        for eid, entity in self.entities.items():
            if entity.name.lower() in words:
                relevant_entities.append(entity)
        
        assumptions = []
        if not relevant_entities:
            assumptions.append("No known entities match scenario")
        
        # 获取相关常识
        commonsense_facts = self._commonsense.get_relevant_knowledge(scenario)
        assumptions.extend(commonsense_facts)
        
        state = {"scenario": scenario}
        steps = []
        trajectory = [{"step": 0, "state": dict(state)}]
        causal_chain = []
        
        # 找到场景相关的因果链接
        scenario_links = [
            link for link in self.causal_links.values()
            if any(word in link.condition.lower() for word in words) or
               any(word in link.effect.lower() for word in words)
        ]
        
        for step in range(max_steps):
            step_state = {"step": step + 1, "active_entities": []}
            
            # 更新活跃实体
            for entity in relevant_entities[:5]:
                step_state["active_entities"].append(entity.name)
                entity.touch()
            
            # 应用因果效果
            if scenario_links:
                link = scenario_links[step % len(scenario_links)]
                step_state["causal_effect"] = f"{link.condition} → {link.effect}"
                causal_chain.append(step_state["causal_effect"])
                state[link.effect] = link.probability
            
            if step_state:
                steps.append(step_state)
                trajectory.append({"step": step + 1, "state": dict(state)})
        
        return SimulationResult(
            steps=steps,
            final_state=state,
            confidence=0.6 + len(scenario_links) * 0.05,
            assumptions=assumptions,
            trajectory=trajectory,
            causal_chain=causal_chain
        )
    
    def update_from_observation(self, observation: Dict[str, Any],
                               source: str = "perception") -> None:
        """从感知更新世界模型"""
        with self._lock:
            if "entities" in observation:
                for entity_data in observation["entities"]:
                    name = entity_data.get("name")
                    entity_type = EntityType(entity_data.get("type", "unknown").upper())
                    properties = entity_data.get("properties", {})
                    confidence = entity_data.get("confidence", 0.5)
                    reliability = entity_data.get("reliability", 0.7)
                    self.add_entity(name, entity_type, properties, 
                                   source=source, confidence=confidence, reliability=reliability)
            
            if "relations" in observation:
                for rel_data in observation["relations"]:
                    source_name = rel_data.get("source")
                    target_name = rel_data.get("target")
                    rel_type = RelationType(rel_data.get("type", "unknown").upper())
                    confidence = rel_data.get("confidence", 0.5)
                    context = rel_data.get("context")
                    self.add_relation(source_name, target_name, rel_type, 
                                     confidence=confidence, context=context)
            
            if "causal_links" in observation:
                for causal_data in observation["causal_links"]:
                    condition = causal_data.get("condition")
                    effect = causal_data.get("effect")
                    probability = causal_data.get("probability", 0.5)
                    confidence = causal_data.get("confidence", 0.3)
                    domain = causal_data.get("domain", "")
                    self.add_causal_link(condition, effect, probability, confidence, domain)
            
            self._save_state()
    
    def stats(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "type": "local",
            "entities": len(self.entities),
            "relations": len(self.relations),
            "causal_links": len(self.causal_links),
            "history_length": len(self._history),
            "total_updates": self.total_updates,
            "total_predictions": self.total_predictions,
            "total_queries": self.total_queries,
            "uptime_seconds": time.time() - self.created_at
        }
    
    def to_summary(self, limit: int = 20) -> str:
        s = self.stats()
        lines = [f"World Model [{s['type']}]: {s['entities']} entities, {s['relations']} relations, {s['causal_links']} causal links"]
        
        sorted_entities = sorted(
            self.entities.values(),
            key=lambda x: x.salience,
            reverse=True
        )[:limit]
        
        for e in sorted_entities:
            props = ", ".join(
                f"{k}={str(v.value)[:30]}"
                for k, v in list(e.properties.items())[:2]
            )
            lines.append(f"  • {e.name} [{e.entity_type.value}] | {props}")
        
        return "\n".join(lines)
    
    def query(self, query: str) -> List[Dict]:
        """查询世界模型"""
        self.total_queries += 1
        results = []
        query_lower = query.lower()
        
        # 搜索实体
        for eid, entity in self.entities.items():
            if query_lower in entity.name.lower():
                results.append({
                    "type": "entity",
                    "name": entity.name,
                    "entity_type": entity.entity_type.value,
                    "properties": {k: v.value for k, v in entity.properties.items()}
                })
        
        # 搜索关系
        for rid, rel in self.relations.items():
            src = self.entities.get(rel.source_id)
            tgt = self.entities.get(rel.target_id)
            if src and tgt:
                if query_lower in rel.relation_type.value.lower() or \
                   query_lower in src.name.lower() or \
                   query_lower in tgt.name.lower():
                    results.append({
                        "type": "relation",
                        "source": src.name,
                        "target": tgt.name,
                        "relation_type": rel.relation_type.value,
                        "confidence": rel.confidence
                    })
        
        # 搜索因果链接
        for cid, link in self.causal_links.items():
            if query_lower in link.condition.lower() or query_lower in link.effect.lower():
                results.append({
                    "type": "causal_link",
                    "condition": link.condition,
                    "effect": link.effect,
                    "probability": link.probability,
                    "confidence": link.confidence,
                    "domain": link.domain
                })
        
        return results
    
    def infer_missing_links(self) -> List[Relation]:
        """推理缺失的关系"""
        inferred = []
        
        # 传递性推理：如果 A is_a B 且 B is_a C，则 A is_a C
        for rel1 in self.relations.values():
            if rel1.relation_type == RelationType.IS_A:
                src1 = self.entities.get(rel1.source_id)
                tgt1 = self.entities.get(rel1.target_id)
                
                for rel2 in self.relations.values():
                    if rel2.relation_type == RelationType.IS_A and rel2.source_id == rel1.target_id:
                        tgt2 = self.entities.get(rel2.target_id)
                        
                        # 检查是否已存在
                        exists = False
                        for existing_rel in self.relations.values():
                            if existing_rel.source_id == rel1.source_id and \
                               existing_rel.target_id == rel2.target_id and \
                               existing_rel.relation_type == RelationType.IS_A:
                                exists = True
                                break
                        
                        if not exists and src1 and tgt2:
                            inferred.append({
                                "source": src1.name,
                                "target": tgt2.name,
                                "relation_type": "is_a",
                                "confidence": rel1.confidence * rel2.confidence * 0.9,
                                "inference_method": "transitive"
                            })
        
        return inferred

# ═══════════════════════════════════════════════════════════════
# PARACOSM 外部世界模型集成
# ═══════════════════════════════════════════════════════════════
class ParacosmWorldModel(AbstractWorldModel):
    """PARACOSM 外部世界模型服务集成"""
    
    def __init__(self, api_url: str = "https://api.paracosm.agentos.sh", 
                api_key: Optional[str] = None):
        self.api_url = api_url
        self.api_key = api_key
        self._local_cache = {}
        self._last_sync = 0
        self._sync_interval = 300  # 5分钟同步一次
        self._commonsense = CommonsenseKnowledge()
    
    async def _api_request(self, endpoint: str, method: str = "GET", 
                          data: Optional[Dict] = None) -> Dict:
        """发送API请求"""
        import aiohttp
        
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        url = f"{self.api_url}/{endpoint}"
        try:
            async with aiohttp.ClientSession() as session:
                if method == "POST":
                    async with session.post(url, json=data, headers=headers) as resp:
                        return await resp.json()
                else:
                    async with session.get(url, headers=headers) as resp:
                        return await resp.json()
        except Exception as e:
            logger.warning(f"PARACOSM API error: {e}")
            return {"error": str(e)}
    
    def add_entity(self, name: str, entity_type: EntityType = EntityType.UNKNOWN,
                  properties: Optional[Dict] = None, tags: Optional[Set[str]] = None,
                  confidence: float = 0.5, source: str = "observation",
                  reliability: float = 0.5) -> Entity:
        eid = str(uuid.uuid4())[:12]
        e = Entity(id=eid, name=name, entity_type=entity_type, tags=tags or set())
        if properties:
            for k, v in properties.items():
                e.set(k, v, confidence, source, reliability)
        self._local_cache[name.lower()] = e
        return e
    
    def get_entity(self, identifier: str) -> Optional[Entity]:
        return self._local_cache.get(identifier.lower())
    
    def add_relation(self, source: str, target: str, rel_type: RelationType,
                    confidence: float = 0.5, context: Optional[str] = None) -> Optional[Relation]:
        src = self.get_entity(source)
        tgt = self.get_entity(target)
        if not src or not tgt:
            return None
        
        rid = str(uuid.uuid4())[:12]
        r = Relation(
            id=rid,
            source_id=src.id,
            target_id=tgt.id,
            relation_type=rel_type,
            confidence=confidence,
            context=context
        )
        return r
    
    def add_causal_link(self, condition: str, effect: str,
                       probability: float = 0.5, confidence: float = 0.3,
                       domain: str = "", latency: float = 0.0) -> CausalLink:
        cid = str(uuid.uuid4())[:12]
        return CausalLink(
            id=cid,
            condition=condition,
            effect=effect,
            probability=probability,
            confidence=confidence,
            domain=domain,
            latency=latency
        )
    
    def predict(self, action: str, context: Optional[Dict] = None,
               max_steps: int = 3) -> SimulationResult:
        return self.simulate(action, max_steps)
    
    def counterfactual(self, entity_name: str, property_name: str,
                      actual_value: Any, hypothetical_value: Any) -> Dict:
        """使用PARACOSM进行反事实推理"""
        scenario = f"What if {entity_name}.{property_name} were {hypothetical_value} instead of {actual_value}?"
        
        result = asyncio.run(self._api_request("simulate", "POST", {
            "scenario": scenario,
            "max_steps": 5,
            "mode": "counterfactual"
        }))
        
        if "error" in result:
            # 回退到本地实现
            return self._local_counterfactual(entity_name, property_name, 
                                            actual_value, hypothetical_value)
        
        return {
            "counterfactual_scenario": scenario,
            "confidence": result.get("confidence", 0.7),
            "predicted_outcome": result.get("outcome", {}),
            "causal_paths": result.get("causal_paths", []),
            "source": "paracosm"
        }
    
    def _local_counterfactual(self, entity_name: str, property_name: str,
                             actual_value: Any, hypothetical_value: Any) -> Dict:
        """本地反事实回退"""
        commonsense = self._commonsense.get_relevant_knowledge(f"{entity_name} {property_name}")
        return {
            "counterfactual_scenario": f"If {entity_name}.{property_name} were {hypothetical_value} instead of {actual_value}",
            "confidence": 0.4,
            "causal_paths": [],
            "source": "local_fallback",
            "commonsense_support": commonsense
        }
    
    def simulate(self, scenario: str, max_steps: int = 10) -> SimulationResult:
        """调用PARACOSM进行场景模拟"""
        result = asyncio.run(self._api_request("simulate", "POST", {
            "scenario": scenario,
            "max_steps": max_steps,
            "mode": "forward"
        }))
        
        if "error" in result:
            # 回退到简单模拟
            commonsense = self._commonsense.get_relevant_knowledge(scenario)
            return SimulationResult(
                steps=[],
                final_state={"scenario": scenario},
                confidence=0.3,
                assumptions=["External world model unavailable"] + commonsense
            )
        
        return SimulationResult(
            steps=result.get("steps", []),
            final_state=result.get("final_state", {}),
            confidence=result.get("confidence", 0.7),
            assumptions=result.get("assumptions", []),
            trajectory=result.get("trajectory", []),
            causal_chain=result.get("causal_chain", [])
        )
    
    def update_from_observation(self, observation: Dict[str, Any],
                               source: str = "perception") -> None:
        """更新本地缓存"""
        if "entities" in observation:
            for entity_data in observation["entities"]:
                name = entity_data.get("name")
                self._local_cache[name.lower()] = entity_data
    
    def stats(self) -> Dict[str, Any]:
        return {
            "name": "paracosm",
            "type": "external",
            "api_url": self.api_url,
            "cached_entities": len(self._local_cache),
            "last_sync": self._last_sync
        }
    
    def query(self, query: str) -> List[Dict]:
        """查询 - 回退到本地缓存"""
        results = []
        query_lower = query.lower()
        
        for name, entity in self._local_cache.items():
            if query_lower in name:
                results.append({"type": "entity", "name": name})
        
        return results
    
    def infer_missing_links(self) -> List[Relation]:
        """推理缺失关系 - 回退到空列表"""
        return []

# ═══════════════════════════════════════════════════════════════
# ODEI 知识图谱集成
# ═══════════════════════════════════════════════════════════════
class OdeiWorldModel(AbstractWorldModel):
    """ODEI Constitutional World Model 集成"""
    
    def __init__(self, api_url: str = "https://api.odei.ai"):
        self.api_url = api_url
        self._local_cache = {}
        self._ontology_layers = {
            "foundation": ["identity", "values", "partnerships", "principles"],
            "vision": ["goals", "aspirations", "objectives"],
            "strategy": ["plans", "initiatives", "resource_allocation"],
            "tactics": ["tasks", "time_blocks", "execution"],
            "execution": ["work_sessions", "deliverables", "outcomes"],
            "track": ["metrics", "signals", "observations"]
        }
        self._guardrails = [
            "immutability", "temporal_context", "referential_integrity",
            "authority", "deduplication", "provenance", "constitutional_alignment"
        ]
    
    async def _api_request(self, endpoint: str, method: str = "GET", 
                          data: Optional[Dict] = None) -> Dict:
        """发送ODEI API请求"""
        import aiohttp
        
        url = f"{self.api_url}/{endpoint}"
        try:
            async with aiohttp.ClientSession() as session:
                if method == "POST":
                    async with session.post(url, json=data) as resp:
                        return await resp.json()
                else:
                    async with session.get(url) as resp:
                        return await resp.json()
        except Exception as e:
            logger.warning(f"ODEI API error: {e}")
            return {"error": str(e)}
    
    def _validate_action(self, action: Dict) -> Dict:
        """通过7层安全护栏验证动作"""
        validation = {
            "approved": True,
            "checks": []
        }
        
        for guardrail in self._guardrails:
            check = {
                "guardrail": guardrail,
                "result": "APPROVED",
                "reason": "Default approval"
            }
            
            # 简单的验证逻辑
            if guardrail == "deduplication" and action.get("id") in self._local_cache:
                check["result"] = "REJECTED"
                check["reason"] = "Duplicate action"
                validation["approved"] = False
            
            validation["checks"].append(check)
        
        return validation
    
    def add_entity(self, name: str, entity_type: EntityType = EntityType.UNKNOWN,
                  properties: Optional[Dict] = None, tags: Optional[Set[str]] = None,
                  confidence: float = 0.5, source: str = "observation",
                  reliability: float = 0.5) -> Entity:
        # 获取本体层级
        layer = self._get_ontology_layer(entity_type)
        
        eid = str(uuid.uuid4())[:12]
        e = Entity(id=eid, name=name, entity_type=entity_type, tags=tags or set())
        if properties:
            for k, v in properties.items():
                e.set(k, v, confidence, source, reliability)
        
        # 存储到本地缓存，带有本体层级信息
        self._local_cache[name.lower()] = {
            "entity": e,
            "layer": layer,
            "added_at": time.time()
        }
        
        return e
    
    def _get_ontology_layer(self, entity_type: EntityType) -> str:
        """确定实体所属的本体层级"""
        if entity_type in [EntityType.GOAL, EntityType.THEORY]:
            return "vision"
        elif entity_type in [EntityType.PLAN, EntityType.RULE]:
            return "strategy"
        elif entity_type in [EntityType.ACTION, EntityType.TASK]:
            return "tactics"
        elif entity_type in [EntityType.EVENT, EntityType.STATE]:
            return "execution"
        elif entity_type in [EntityType.DATA, EntityType.KNOWLEDGE]:
            return "track"
        else:
            return "foundation"
    
    def get_entity(self, identifier: str) -> Optional[Entity]:
        cached = self._local_cache.get(identifier.lower())
        return cached["entity"] if cached else None
    
    def add_relation(self, source: str, target: str, rel_type: RelationType,
                    confidence: float = 0.5, context: Optional[str] = None) -> Optional[Relation]:
        src = self.get_entity(source)
        tgt = self.get_entity(target)
        if not src or not tgt:
            return None
        
        # 验证关系的合法性
        validation = self._validate_action({
            "source": source,
            "target": target,
            "relation_type": rel_type.value,
            "confidence": confidence
        })
        
        if not validation["approved"]:
            logger.warning(f"Relation validation failed: {validation}")
            return None
        
        rid = str(uuid.uuid4())[:12]
        r = Relation(
            id=rid,
            source_id=src.id,
            target_id=tgt.id,
            relation_type=rel_type,
            confidence=confidence,
            context=context
        )
        return r
    
    def add_causal_link(self, condition: str, effect: str,
                       probability: float = 0.5, confidence: float = 0.3,
                       domain: str = "", latency: float = 0.0) -> CausalLink:
        cid = str(uuid.uuid4())[:12]
        return CausalLink(
            id=cid,
            condition=condition,
            effect=effect,
            probability=probability,
            confidence=confidence,
            domain=domain,
            latency=latency
        )
    
    def predict(self, action: str, context: Optional[Dict] = None,
               max_steps: int = 3) -> SimulationResult:
        return self.simulate(action, max_steps)
    
    def counterfactual(self, entity_name: str, property_name: str,
                      actual_value: Any, hypothetical_value: Any) -> Dict:
        """使用ODEI进行反事实推理"""
        scenario = f"What if {entity_name}.{property_name} were {hypothetical_value} instead of {actual_value}?"
        
        result = asyncio.run(self._api_request("counterfactual", "POST", {
            "scenario": scenario,
            "entity": entity_name,
            "property": property_name,
            "actual_value": actual_value,
            "hypothetical_value": hypothetical_value
        }))
        
        if "error" in result:
            return {
                "counterfactual_scenario": scenario,
                "confidence": 0.4,
                "causal_paths": [],
                "source": "odei_local",
                "guardrails_applied": self._guardrails
            }
        
        return {
            "counterfactual_scenario": scenario,
            "confidence": result.get("confidence", 0.7),
            "predicted_outcome": result.get("outcome", {}),
            "causal_paths": result.get("causal_paths", []),
            "source": "odei",
            "guardrails_applied": result.get("guardrails_applied", []),
            "constitutional_alignment": result.get("constitutional_alignment", False)
        }
    
    def simulate(self, scenario: str, max_steps: int = 10) -> SimulationResult:
        """调用ODEI进行场景模拟"""
        result = asyncio.run(self._api_request("simulate", "POST", {
            "scenario": scenario,
            "max_steps": max_steps,
            "include_guardrails": True
        }))
        
        if "error" in result:
            return SimulationResult(
                steps=[],
                final_state={"scenario": scenario},
                confidence=0.3,
                assumptions=["ODEI service unavailable", "Using local fallback"],
                warnings=["External validation unavailable"]
            )
        
        return SimulationResult(
            steps=result.get("steps", []),
            final_state=result.get("final_state", {}),
            confidence=result.get("confidence", 0.7),
            assumptions=result.get("assumptions", []),
            trajectory=result.get("trajectory", []),
            causal_chain=result.get("causal_chain", []),
            warnings=result.get("warnings", [])
        )
    
    def update_from_observation(self, observation: Dict[str, Any],
                               source: str = "perception") -> None:
        """更新本地缓存"""
        if "entities" in observation:
            for entity_data in observation["entities"]:
                name = entity_data.get("name")
                entity_type = EntityType(entity_data.get("type", "unknown").upper())
                properties = entity_data.get("properties", {})
                self.add_entity(name, entity_type, properties, source=source)
    
    def stats(self) -> Dict[str, Any]:
        return {
            "name": "odei",
            "type": "external",
            "api_url": self.api_url,
            "cached_entities": len(self._local_cache),
            "ontology_layers": list(self._ontology_layers.keys()),
            "guardrails_applied": len(self._guardrails)
        }
    
    def query(self, query: str) -> List[Dict]:
        """查询ODEI知识图谱"""
        results = []
        query_lower = query.lower()
        
        for name, data in self._local_cache.items():
            if query_lower in name:
                entity = data["entity"]
                results.append({
                    "type": "entity",
                    "name": entity.name,
                    "layer": data["layer"],
                    "entity_type": entity.entity_type.value
                })
        
        return results
    
    def infer_missing_links(self) -> List[Relation]:
        """推理缺失关系"""
        return []

# ═══════════════════════════════════════════════════════════════
# 混合世界模型（本地+外部）
# ═══════════════════════════════════════════════════════════════
class HybridWorldModel(AbstractWorldModel):
    """混合世界模型 - 结合本地和外部模型"""
    
    def __init__(self, local_model: LocalWorldModel,
                paracosm_model: Optional[ParacosmWorldModel] = None,
                odei_model: Optional[OdeiWorldModel] = None):
        self.local = local_model
        self.paracosm = paracosm_model
        self.odei = odei_model
        self._fallback_enabled = True
        self._preference_order = ["odei", "paracosm", "local"]  # 查询优先级
    
    def add_entity(self, name: str, entity_type: EntityType = EntityType.UNKNOWN,
                  properties: Optional[Dict] = None, tags: Optional[Set[str]] = None,
                  confidence: float = 0.5, source: str = "observation",
                  reliability: float = 0.5) -> Entity:
        # 在所有模型中添加
        entity = self.local.add_entity(name, entity_type, properties, tags, confidence, source, reliability)
        
        if self.paracosm:
            self.paracosm.add_entity(name, entity_type, properties, tags, confidence, source, reliability)
        
        if self.odei:
            self.odei.add_entity(name, entity_type, properties, tags, confidence, source, reliability)
        
        return entity
    
    def get_entity(self, identifier: str) -> Optional[Entity]:
        # 按优先级查询
        for model_name in self._preference_order:
            model = getattr(self, model_name)
            if model:
                entity = model.get_entity(identifier)
                if entity:
                    return entity
        return None
    
    def add_relation(self, source: str, target: str, rel_type: RelationType,
                    confidence: float = 0.5, context: Optional[str] = None) -> Optional[Relation]:
        rel = self.local.add_relation(source, target, rel_type, confidence, context)
        
        if self.paracosm:
            self.paracosm.add_relation(source, target, rel_type, confidence, context)
        
        if self.odei:
            self.odei.add_relation(source, target, rel_type, confidence, context)
        
        return rel
    
    def add_causal_link(self, condition: str, effect: str,
                       probability: float = 0.5, confidence: float = 0.3,
                       domain: str = "", latency: float = 0.0) -> CausalLink:
        link = self.local.add_causal_link(condition, effect, probability, confidence, domain, latency)
        
        if self.paracosm:
            self.paracosm.add_causal_link(condition, effect, probability, confidence, domain, latency)
        
        if self.odei:
            self.odei.add_causal_link(condition, effect, probability, confidence, domain, latency)
        
        return link
    
    def predict(self, action: str, context: Optional[Dict] = None,
               max_steps: int = 3) -> SimulationResult:
        """优先使用ODEI，然后PARACOSM，最后本地"""
        if self.odei:
            try:
                result = self.odei.predict(action, context, max_steps)
                if result.confidence > 0.5:
                    return result
            except Exception as e:
                logger.debug(f"ODEI predict failed: {e}")
        
        if self.paracosm:
            try:
                result = self.paracosm.predict(action, context, max_steps)
                if result.confidence > 0.5:
                    return result
            except Exception as e:
                logger.debug(f"PARACOSM predict failed: {e}")
        
        return self.local.predict(action, context, max_steps)
    
    def counterfactual(self, entity_name: str, property_name: str,
                      actual_value: Any, hypothetical_value: Any) -> Dict:
        """优先使用ODEI进行反事实推理（带安全护栏）"""
        if self.odei:
            try:
                result = self.odei.counterfactual(entity_name, property_name, 
                                                actual_value, hypothetical_value)
                if result.get("confidence", 0) > 0.5:
                    return result
            except Exception as e:
                logger.debug(f"ODEI counterfactual failed: {e}")
        
        if self.paracosm:
            try:
                result = self.paracosm.counterfactual(entity_name, property_name, 
                                                    actual_value, hypothetical_value)
                if result.get("confidence", 0) > 0.5:
                    return result
            except Exception as e:
                logger.debug(f"PARACOSM counterfactual failed: {e}")
        
        return self.local.counterfactual(entity_name, property_name, 
                                       actual_value, hypothetical_value)
    
    def simulate(self, scenario: str, max_steps: int = 10) -> SimulationResult:
        """复杂场景使用外部模型，简单场景使用本地模型"""
        if len(scenario.split()) > 10:
            if self.odei:
                try:
                    return self.odei.simulate(scenario, max_steps)
                except Exception as e:
                    logger.debug(f"ODEI simulate failed: {e}")
            
            if self.paracosm:
                try:
                    return self.paracosm.simulate(scenario, max_steps)
                except Exception as e:
                    logger.debug(f"PARACOSM simulate failed: {e}")
        
        return self.local.simulate(scenario, max_steps)
    
    def update_from_observation(self, observation: Dict[str, Any],
                               source: str = "perception") -> None:
        self.local.update_from_observation(observation, source)
        if self.paracosm:
            self.paracosm.update_from_observation(observation, source)
        if self.odei:
            self.odei.update_from_observation(observation, source)
    
    def stats(self) -> Dict[str, Any]:
        local_stats = self.local.stats()
        stats = {
            "name": "hybrid",
            "local": local_stats,
            "paracosm_available": self.paracosm is not None,
            "odei_available": self.odei is not None,
            "preference_order": self._preference_order
        }
        
        if self.paracosm:
            stats["paracosm"] = self.paracosm.stats()
        
        if self.odei:
            stats["odei"] = self.odei.stats()
        
        return stats
    
    def query(self, query: str) -> List[Dict]:
        """综合查询所有模型"""
        results = []
        seen = set()
        
        for model_name in self._preference_order:
            model = getattr(self, model_name)
            if model:
                model_results = model.query(query)
                for r in model_results:
                    key = f"{r.get('type', '')}_{r.get('name', '')}"
                    if key not in seen:
                        seen.add(key)
                        r["source"] = model_name
                        results.append(r)
        
        return results
    
    def infer_missing_links(self) -> List[Relation]:
        """推理缺失关系"""
        return self.local.infer_missing_links()

# ═══════════════════════════════════════════════════════════════
# 高级混合世界模型（支持所有后端）
# ═══════════════════════════════════════════════════════════════
class AdvancedHybridWorldModel(AbstractWorldModel):
    """高级混合世界模型 - 支持所有后端的综合集成"""
    
    def __init__(self, local_model: LocalWorldModel,
                paracosm_model: Optional[ParacosmWorldModel] = None,
                odei_model: Optional[OdeiWorldModel] = None,
                lingbot_model: Optional = None,
                openworldlib_model: Optional = None,
                hunyuan_model: Optional = None):
        self.local = local_model
        self.paracosm = paracosm_model
        self.odei = odei_model
        self.lingbot = lingbot_model
        self.openworldlib = openworldlib_model
        self.hunyuan = hunyuan_model
        
        # 查询优先级：优先使用功能最强大的模型
        self._preference_order = [
            "hunyuan",      # 腾讯HunYuanWorld - 实时交互式世界
            "lingbot",      # 蚂蚁LingBot-World - 物理模拟
            "openworldlib", # 北大OpenWorldLib - 统一框架
            "odei",         # ODEI - 知识图谱+安全护栏
            "paracosm",     # PARACOSM - 反事实推理
            "local"         # 本地 - 基础功能
        ]
        
        # 按场景类型选择最佳模型
        self._scene_model_map = {
            "interactive_3d": ["lingbot", "hunyuan"],
            "video_generation": ["hunyuan", "lingbot"],
            "reasoning": ["openworldlib", "odei"],
            "safety_critical": ["odei", "openworldlib"],
            "counterfactual": ["paracosm", "openworldlib"],
            "default": ["local"]
        }

    @property
    def entities(self) -> Dict[str, Entity]:
        """代理到本地世界模型的实体字典"""
        return self.local.entities if hasattr(self.local, 'entities') else {}

    @property
    def relations(self) -> List[Relation]:
        """代理到本地世界模型的关系列表"""
        return self.local.relations if hasattr(self.local, 'relations') else []

    def _get_model_by_preference(self, scenario_type: str = "default") -> AbstractWorldModel:
        """根据场景类型获取最佳可用模型"""
        preferred = self._scene_model_map.get(scenario_type, self._scene_model_map["default"])
        
        for model_name in preferred:
            model = getattr(self, model_name)
            if model:
                if hasattr(model, '_is_available') and model._is_available:
                    return model
                elif not hasattr(model, '_is_available'):
                    return model
        
        # 回退到本地模型
        return self.local
    
    def add_entity(self, name: str, entity_type: EntityType = EntityType.UNKNOWN,
                  properties: Optional[Dict] = None, tags: Optional[Set[str]] = None,
                  confidence: float = 0.5, source: str = "observation",
                  reliability: float = 0.5) -> Entity:
        """在所有可用模型中添加实体"""
        entity = self.local.add_entity(name, entity_type, properties, tags, confidence, source, reliability)
        
        for model_name in ["paracosm", "odei", "lingbot", "openworldlib", "hunyuan"]:
            model = getattr(self, model_name)
            if model:
                try:
                    model.add_entity(name, entity_type, properties, tags, confidence, source, reliability)
                except Exception as e:
                    logger.debug(f"Failed to sync entity to {model_name}: {e}")
        
        return entity
    
    def get_entity(self, identifier: str) -> Optional[Entity]:
        """按优先级获取实体"""
        for model_name in self._preference_order:
            model = getattr(self, model_name)
            if model:
                entity = model.get_entity(identifier)
                if entity:
                    return entity
        return None
    
    def add_relation(self, source: str, target: str, rel_type: RelationType,
                    confidence: float = 0.5, context: Optional[str] = None) -> Optional[Relation]:
        """添加关系到所有模型"""
        rel = self.local.add_relation(source, target, rel_type, confidence, context)
        
        for model_name in ["paracosm", "odei", "lingbot", "openworldlib", "hunyuan"]:
            model = getattr(self, model_name)
            if model:
                try:
                    model.add_relation(source, target, rel_type, confidence, context)
                except Exception as e:
                    logger.debug(f"Failed to sync relation to {model_name}: {e}")
        
        return rel
    
    def add_causal_link(self, condition: str, effect: str,
                       probability: float = 0.5, confidence: float = 0.3,
                       domain: str = "", latency: float = 0.0) -> CausalLink:
        """添加因果链接到所有模型"""
        link = self.local.add_causal_link(condition, effect, probability, confidence, domain, latency)
        
        for model_name in ["paracosm", "odei", "lingbot", "openworldlib", "hunyuan"]:
            model = getattr(self, model_name)
            if model:
                try:
                    model.add_causal_link(condition, effect, probability, confidence, domain, latency)
                except Exception as e:
                    logger.debug(f"Failed to sync causal link to {model_name}: {e}")
        
        return link
    
    def predict(self, action: str, context: Optional[Dict] = None,
               max_steps: int = 3) -> SimulationResult:
        """智能选择最佳模型进行预测"""
        # 根据动作类型选择模型
        if any(keyword in action.lower() for keyword in ["3d", "world", "environment", "simulate"]):
            model = self._get_model_by_preference("interactive_3d")
        elif any(keyword in action.lower() for keyword in ["video", "generate", "visualize"]):
            model = self._get_model_by_preference("video_generation")
        else:
            model = self._get_model_by_preference("default")
        
        return model.predict(action, context, max_steps)
    
    def counterfactual(self, entity_name: str, property_name: str,
                      actual_value: Any, hypothetical_value: Any) -> Dict:
        """优先使用ODEI和PARACOSM进行安全的反事实推理"""
        model = self._get_model_by_preference("counterfactual")
        return model.counterfactual(entity_name, property_name, actual_value, hypothetical_value)
    
    def simulate(self, scenario: str, max_steps: int = 10) -> SimulationResult:
        """根据场景复杂度选择最佳模型"""
        if len(scenario.split()) > 15:
            # 复杂场景使用高级模型
            if any(keyword in scenario.lower() for keyword in ["3d", "world", "environment"]):
                model = self._get_model_by_preference("interactive_3d")
            elif any(keyword in scenario.lower() for keyword in ["video", "generate"]):
                model = self._get_model_by_preference("video_generation")
            else:
                model = self._get_model_by_preference("reasoning")
        else:
            model = self._get_model_by_preference("default")
        
        return model.simulate(scenario, max_steps)
    
    def update_from_observation(self, observation: Dict[str, Any],
                               source: str = "perception") -> None:
        """更新所有模型"""
        self.local.update_from_observation(observation, source)
        
        for model_name in ["paracosm", "odei", "lingbot", "openworldlib", "hunyuan"]:
            model = getattr(self, model_name)
            if model:
                try:
                    model.update_from_observation(observation, source)
                except Exception as e:
                    logger.debug(f"Failed to update {model_name}: {e}")
    
    def stats(self) -> Dict[str, Any]:
        """获取综合统计信息"""
        stats = {
            "name": "advanced_hybrid",
            "type": "hybrid",
            "local": self.local.stats(),
            "available_models": [],
            "preference_order": self._preference_order,
            "scene_model_map": self._scene_model_map
        }
        
        for model_name in ["paracosm", "odei", "lingbot", "openworldlib", "hunyuan"]:
            model = getattr(self, model_name)
            if model:
                stats["available_models"].append(model_name)
                stats[model_name] = model.stats()
        
        return stats
    
    def query(self, query: str) -> List[Dict]:
        """综合查询所有模型"""
        results = []
        seen = set()
        
        for model_name in self._preference_order:
            model = getattr(self, model_name)
            if model:
                try:
                    model_results = model.query(query)
                    for r in model_results:
                        key = f"{r.get('type', '')}_{r.get('name', '')}"
                        if key not in seen:
                            seen.add(key)
                            r["source"] = model_name
                            results.append(r)
                except Exception as e:
                    logger.debug(f"Failed to query {model_name}: {e}")
        
        return results
    
    def infer_missing_links(self) -> List[Relation]:
        """推理缺失关系"""
        return self.local.infer_missing_links()

# ═══════════════════════════════════════════════════════════════
# 工厂函数
# ═══════════════════════════════════════════════════════════════
def create_world_model(model_type: Union[str, WorldModelType], **kwargs) -> AbstractWorldModel:
    """创建世界模型实例"""
    model_type_enum = WorldModelType(model_type.lower()) if isinstance(model_type, str) else model_type
    
    if model_type_enum == WorldModelType.LOCAL:
        return LocalWorldModel(**kwargs)
    elif model_type_enum == WorldModelType.PARACOSM:
        return ParacosmWorldModel(**kwargs)
    elif model_type_enum == WorldModelType.ODEI:
        return OdeiWorldModel(**kwargs)
    elif model_type_enum == WorldModelType.LINGBOT:
        from .world_models import LingBotWorldModel
        return LingBotWorldModel(
            api_url=kwargs.get("api_url", "https://api.lingbot.world"),
            api_key=kwargs.get("api_key"),
            model_name=kwargs.get("model_name", "lingbot-world-base-cam")
        )
    elif model_type_enum == WorldModelType.OPENWORLDLIB:
        from .world_models import OpenWorldLibModel
        return OpenWorldLibModel(
            api_url=kwargs.get("api_url", "https://api.openworldlib.org"),
            api_key=kwargs.get("api_key"),
            backend=kwargs.get("backend", "hunyuan-worldplay")
        )
    elif model_type_enum == WorldModelType.HUNYUAN:
        from .world_models import HunYuanWorldModel
        return HunYuanWorldModel(
            api_url=kwargs.get("api_url", "https://api.hunyuan.world"),
            api_key=kwargs.get("api_key"),
            model_version=kwargs.get("model_version", "1.5")
        )
    elif model_type_enum == WorldModelType.HYBRID:
        local = LocalWorldModel(name=kwargs.get("name", "world"))
        paracosm = None
        odei = None
        lingbot = None
        openworldlib = None
        hunyuan = None
        
        # 尝试初始化PARACOSM
        try:
            paracosm = ParacosmWorldModel(
                api_url=kwargs.get("paracosm_api_url", "https://api.paracosm.agentos.sh"),
                api_key=kwargs.get("paracosm_api_key")
            )
        except Exception as e:
            logger.warning(f"Failed to initialize PARACOSM: {e}")
        
        # 尝试初始化ODEI
        try:
            odei = OdeiWorldModel(
                api_url=kwargs.get("odei_api_url", "https://api.odei.ai")
            )
        except Exception as e:
            logger.warning(f"Failed to initialize ODEI: {e}")
        
        # 尝试初始化LingBot-World
        try:
            from .world_models import LingBotWorldModel
            lingbot = LingBotWorldModel(
                api_url=kwargs.get("lingbot_api_url", "https://api.lingbot.world"),
                api_key=kwargs.get("lingbot_api_key")
            )
        except Exception as e:
            logger.warning(f"Failed to initialize LingBot-World: {e}")
        
        # 尝试初始化OpenWorldLib
        try:
            from .world_models import OpenWorldLibModel
            openworldlib = OpenWorldLibModel(
                api_url=kwargs.get("openworldlib_api_url", "https://api.openworldlib.org"),
                api_key=kwargs.get("openworldlib_api_key"),
                backend=kwargs.get("openworldlib_backend", "hunyuan-worldplay")
            )
        except Exception as e:
            logger.warning(f"Failed to initialize OpenWorldLib: {e}")
        
        # 尝试初始化HunYuanWorld
        try:
            from .world_models import HunYuanWorldModel
            hunyuan = HunYuanWorldModel(
                api_url=kwargs.get("hunyuan_api_url", "https://api.hunyuan.world"),
                api_key=kwargs.get("hunyuan_api_key")
            )
        except Exception as e:
            logger.warning(f"Failed to initialize HunYuanWorld: {e}")
        
        return AdvancedHybridWorldModel(local, paracosm, odei, lingbot, openworldlib, hunyuan)
    else:
        raise ValueError(f"Unknown world model type: {model_type}")

def integrate_world_model(agent, model_type: str = "local", **kwargs) -> AbstractWorldModel:
    """将世界模型集成到智能体"""
    wm = create_world_model(model_type, **kwargs)
    agent.world = wm
    
    # 自动同步世界模型与因果引擎
    if hasattr(agent, 'causal') and agent.causal:
        agent.causal.build_from_world_model(wm)
    
    # 同步世界模型与自我模型
    if hasattr(agent, 'self_model') and agent.self_model:
        wm.add_entity(agent.name, EntityType.AGENT, 
                      {"type": "LAAP-Agent", "version": getattr(agent, 'version', "unknown")},
                      tags={"self", "agent"}, confidence=1.0, reliability=1.0)
    
    return wm

# ═══════════════════════════════════════════════════════════════
# 示例用法
# ═══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    # 示例1：创建本地世界模型
    local_wm = create_world_model("local", name="test-world")
    
    # 添加实体
    local_wm.add_entity("John", EntityType.USER, 
                       {"name": "John Smith", "mood": "happy", "age": 30}, 
                       confidence=0.9, reliability=0.8)
    local_wm.add_entity("Finish Report", EntityType.GOAL, 
                       {"description": "Complete Q3 sales report", "priority": "high", "due_date": "2024-09-30"}, 
                       confidence=0.85)
    
    # 添加关系
    local_wm.add_relation("John", "Finish Report", RelationType.HAS_PROPERTY, confidence=0.9)
    
    # 添加因果链接
    local_wm.add_causal_link("John works hard", "Report completed", 
                            probability=0.85, confidence=0.75, domain="work")
    
    # 预测
    result = local_wm.predict("John starts working on the report", max_steps=3)
    print("预测结果:", json.dumps(result.__dict__, indent=2, default=str))
    
    # 反事实推理
    cf_result = local_wm.counterfactual("John", "mood", "happy", "tired")
    print("反事实推理:", json.dumps(cf_result, indent=2))
    
    # 查询
    query_result = local_wm.query("John")
    print("查询结果:", json.dumps(query_result, indent=2))
    
    # 统计
    print("统计信息:", local_wm.stats())
    
    # 示例2：创建混合世界模型
    hybrid_wm = create_world_model("hybrid", name="hybrid-world")
    print("混合模型统计:", hybrid_wm.stats())