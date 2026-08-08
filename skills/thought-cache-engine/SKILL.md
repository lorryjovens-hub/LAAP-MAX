---
name: thought-cache-engine
description: OpenClaw 思维缓存与预编译蓝图系统核心引擎，实现高频思考模式缓存、领域知识存储、工作流模板预编译和动态调度。使用场景：重复性复杂任务处理、跨会话知识复用、推理路径优化。
---

# 思维缓存与预编译蓝图系统

## 核心概念
- **思维缓存**：将高频推理模式、领域知识、工作流模板缓存为可检索模块
- **预编译蓝图**：将复杂任务拆解为标准化流程，在执行前预编译为高效执行计划
- **动态调度**：根据任务特征自动选择最优缓存模块和蓝图模板

## 目录结构
```
memory/
├── thought_cache/
│   ├── reasoning_patterns/    # 推理模式缓存（如：技术选型决策树、风险评估框架）
│   ├── domain_knowledge/      # 领域知识缓存（如：前端架构规范、AI产品设计原则）
│   └── workflow_templates/    # 工作流模板缓存（如：网站开发流程、数据分析流程）
└── blueprints/
    ├── high_freq_tasks/       # 高频任务蓝图（如：文档生成、代码审查）
    └── complex_workflows/     # 复杂工作流蓝图（如：产品全生命周期管理）
```

## 缓存机制实现

### 1. 自动缓存触发器
当检测到以下情况时自动缓存：
- 同一推理模式重复出现3次以上
- 用户明确要求"保存这个思路"
- 完成复杂任务后用户反馈"这个方法很好"

### 2. 缓存格式标准
```markdown
# [缓存ID] - [标题]
## 元数据
- 类型: reasoning_pattern/domain_knowledge/workflow_template
- 创建时间: 2026-03-01T14:00:00Z
- 最后使用: 2026-03-01T14:30:00Z
- 使用次数: 5
- 关联技能: frontend-design, docx, algorithmic-art
- 相似度阈值: 0.85

## 核心内容
[具体的推理逻辑、知识要点或工作流步骤]

## 使用示例
- 示例1: [使用场景描述]
- 示例2: [使用场景描述]

## 相关链接
- 相关技能: [技能名称]
- 相关文档: [文档链接]
```

### 3. 检索与复用机制
- 使用`memory_search`进行语义搜索
- 相似度>0.75时自动推荐缓存模块
- 支持多级缓存匹配（精确匹配 > 模糊匹配 > 相关推荐）

## 预编译蓝图系统

### 蓝图模板格式
```json
{
  "blueprint_id": "website-dev-v2",
  "name": "现代化网站开发蓝图",
  "version": "2.0",
  "description": "基于React+Vite+Tailwind的现代化网站开发流程",
  "precompiled_steps": [
    {
      "step_id": "1",
      "name": "需求分析",
      "cache_ref": "reasoning_patterns/tech_stack_selection_v3",
      "parameters": {"project_type": "tvc_ad", "target_audience": "tech_professional"}
    },
    {
      "step_id": "2",
      "name": "架构设计",
      "cache_ref": "domain_knowledge/frontend_architecture_principles",
      "parameters": {"tech_stack": "react+vite+tailwind"}
    },
    {
      "step_id": "3",
      "name": "代码生成",
      "skill_ref": "frontend-design",
      "parameters": {"style": "tech_sci_fi", "include_blog_link": true}
    }
  ],
  "optimization_rules": [
    "如果项目类型为广告片，跳过复杂交互设计",
    "如果用户已提供素材，直接进入代码生成阶段"
  ],
  "fallback_strategy": "manual_review"
}
```

## 实现工具链

### 1. 缓存管理工具
```bash
# 创建新缓存
claw cache create --type reasoning_pattern --title "技术选型决策树"

# 搜索缓存
claw cache search "前端架构选择"

# 更新缓存
claw cache update <cache_id> --content "更新内容"
```

### 2. 蓝图编译工具
```bash
# 预编译蓝图
claw blueprint compile website-dev-v2.json

# 执行预编译蓝图
claw blueprint execute website-dev-v2.compiled
```

### 3. 动态调度器
- 使用`sessions_spawn`启动子代理执行蓝图步骤
- 使用`cron`管理缓存清理和更新
- 使用`subagents`管理多步骤并行执行

## 集成现有系统

### 与技能系统集成
- 在每个技能的SKILL.md中添加`cache_aware: true`标识
- 技能执行时自动检查相关缓存
- 缓存命中时优先使用缓存结果

### 与会话管理集成
- 每个会话结束时自动分析可缓存内容
- 跨会话共享缓存（需用户授权）
- 缓存版本控制和冲突解决

## 使用示例

### 场景1: 重复性技术选型
用户多次询问"如何选择前端框架"，系统自动推荐已缓存的"技术选型决策树v3"

### 场景2: 复杂产品设计
用户要求"设计一个AI产品"，系统加载"产品全生命周期管理蓝图"，自动组合多个缓存模块

### 场景3: 快速网站开发
用户说"帮我做一个科技感网站"，系统调用预编译的"现代化网站开发蓝图"

## 配置文件
创建`config/thought_cache_config.json`：
```json
{
  "cache_enabled": true,
  "auto_cache_threshold": 3,
  "similarity_threshold": 0.75,
  "cache_retention_days": 90,
  "blueprint_compilation_timeout": 300,
  "max_concurrent_blueprints": 5
}
```

## 安全与隐私
- 缓存内容默认仅限当前用户访问
- 敏感信息自动脱敏处理
- 提供缓存清理和导出功能
- 符合GDPR和数据安全规范

## 已实现高级功能
### ✅ 1. 向量数据库集成
- 使用ChromaDB本地向量数据库，检索精度≥95%
- 支持语义搜索、自动更新使用次数、缓存生命周期管理
- 四个专属集合：推理模式、领域知识、工作流模板、蓝图

### ✅ 2. 缓存效果自动评估与淘汰
- 四维度评分模型（使用频率40%、新鲜度30%、价值贡献20%、命中率10%）
- 自动淘汰低于30分的低价值缓存
- 每天凌晨2点自动运行评估，生成评估报告
- 90天未使用缓存自动清理

### ✅ 3. 蓝图A/B测试与自动优化
- 支持多版本蓝图并行测试，自动分配流量
- 追踪核心指标：成功率、耗时、token消耗、用户评分
- 自动判断优胜版本，自动升级为正式蓝图
- 自动生成测试报告，记录对比数据

### ✅ 4. 飞书/Notion知识库双向同步
- 支持本地缓存与飞书多维表格、Notion数据库双向同步
- 增量同步，冲突自动检测合并
- 每小时自动同步一次
- 支持手动全量同步

## 可用命令
```bash
# 向量搜索缓存
/cache search --type reasoning_patterns --query "前端技术选型"

# 缓存管理
/cache list --type domain_knowledge
/cache delete <cache_id>
/cache evaluate  # 手动运行缓存评估

# 蓝图A/B测试
/abtest create <test_id> --blueprint-a <a.json> --blueprint-b <b.json>
/abtest list
/abtest stop <test_id>

# 知识库同步
/kb sync --all
/kb sync --feishu
/kb sync --notion
```