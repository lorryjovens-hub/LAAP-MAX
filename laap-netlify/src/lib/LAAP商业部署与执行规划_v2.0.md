# LAAP 商业部署与执行规划 v2.0

**文档版本：** v2.0  
**编制日期：** 2026 年 8 月 7 日  
**编制人：** Lorry（CEO）& Aris（首席认知架构师）  
**状态：** 可执行版 · 落地导向

---

## 第一部分：商业总览与财务目标

### 1.1 五年财务基线（单位：人民币万元）

| 指标 | Y1（2026.08-2027.08） | Y2（2027.09-2028.08） | Y3 | Y4 | Y5 |
|------|----------------------|----------------------|-----|-----|-----|
| **收入目标** | 300 | 1,500 | 4,500 | 10,000 | 20,000 |
| 付费客户数 | 5 | 15 | 35 | 65 | 100 |
| 毛利率 | 45% | 60% | 68% | 72% | 75% |
| EBITDA | -200 | +50 | +600 | +2,900 | +7,200 |
| 累计现金需求 | 800（种子轮） | 1,200（Pre-A） | 2,800（A轮） | — | — |

### 1.2 Y1 收入拆解（300 万）

| 来源 | 金额（万） | 数量 | 单价 | 完成季度 |
|------|-----------|------|------|---------|
| 合规 POC（Guard 三件套） | 100 | 2-3 家 | 30-40 万/个 | Q3-Q4 |
| 金融投研助手 POC | 60 | 1-2 家 | 30-60 万/个 | Q4 |
| 企业认知平台 License（试点） | 60 | 1 家 | 60 万/年 | Q4 |
| Web 端 Pro 订阅收入 | 20 | 800 用户 | ￥288/年 | Q2-Q4 累积 |
| 桌面端 Donation + GitHub Sponsors | 10 | — | — | 持续 |
| 技术咨询（小时/项目） | 50 | 若干 | 5000 元/人日 | 持续 |
| **合计** | **300** | | | |

### 1.3 融资节奏

| 轮次 | 时间 | 金额 | 出让股权 | 估值 | 核心里程碑对赌 |
|------|------|------|---------|------|---------------|
| 种子轮 | 2026 Q4 | 800 万 | 12-15% | 5300-6700 万 | Y1 结束：5 付费客户、300 万收入、Guard GA、Core SDK 开源 |
| Pre-A | 2027 Q3 | 1500 万 | 10-12% | 1.25-1.5 亿 | 15 客户、1200 万收入、金融 Harness v1.0 上市 |
| A 轮 | 2028 Q2 | 5000 万 | 15-20% | 2.5-3.3 亿 | 35 客户、3500 万收入、海外试点 2 单、盈亏平衡 |

---

## 第二部分：产品矩阵与交付路线

### 2.1 产品分层架构

```
┌──────────────────────────────────────────────────────────┐
│                  行业解决方案层                           │
│  金融合规 │ 科研数学 │ 生物医药 │ 艺术创作 │ 具身认知     │
├──────────────────────────────────────────────────────────┤
│                  平台产品层                               │
│  LAAP Enterprise（旗舰） │ LAAP Guard（独立合规套件）     │
├──────────────────────────────────────────────────────────┤
│                  开源与 SDK 层                            │
│  Core SDK（意识+记忆 API） │ DLP 数字生命协议 v0.5        │
├──────────────────────────────────────────────────────────┤
│                  前端交付层（本周立即落地）                │
│  Web Pricing 页 │ Stripe 订阅 │ 桌面签名分发 │ Guard 包  │
└──────────────────────────────────────────────────────────┘
```

### 2.2 Y1 12 个月产品甘特图

| 月份 | 产品交付 | 商务 | 基础设施 |
|------|---------|------|---------|
| **M1（2026.08）** | ■ Guard 三件套独立包（causal/safety/audit）<br>■ Web Pricing 页 + Stripe 接入<br>■ GitHub README 商业化入口 | 10 家金融合规候选客户清单<br>3 家首封触达邮件 | Netlify 生产级域名绑定 + WAF<br>Sentry 监控接入 |
| **M2（2026.09）** | ■ Guard v0.2：法规库 5 部 → 8 部<br>■ DLF SDK v0.1：身份+记忆 API 抽取<br>■ Web 端 Pricing 支付联调上线 | 2-3 家深度沟通 POC 方案<br>首份 NDA 签署 | CI/CD 加固：回滚机制、灰度发布<br>桌面端：Windows 代码签名证书采购 |
| **M3（2026.10）** | ■ 白皮书 v1.0《数字生命底座》<br>■ 哥德尔课题立项书 + 数学 Harness POC 设计 | **首个 POC 合同签署**（30 万，合规方向）<br>种子轮 2-3 家天使投资人沟通 | K8s 私有化部署模板（Helm Chart v0.1）<br>Audit 日志对接 Prometheus/Grafana |
| **M4（2026.11）** | ■ Guard GA（法规库 8 部、评估/监控/审计三闭环） | POC 1 交付启动<br>第 2 家 POC 谈判 | 客户成功体系：实施手册、Onboarding SOP |
| **M5（2026.12）** | ■ DLF SDK v0.5：四 API（身份/记忆/治理/进化）半冻结<br>■ 金融 Harness POC 原型（投研因果验证） | 第 2 家 POC 合同<br>1-2 家金融客户跟进 | 年度审计：代码覆盖率 ≥70%（pytest-cov）<br>专利：3 项新提交（DLP、治理断言、因果验证） |
| **M6（2027.01）** | ■ Core SDK GitHub 开源（Apache 2.0）<br>■ 首个黑客松：+ 开发者文档站点 | POC 1 中期汇报<br>种子轮 Term Sheet 签署 1 份 | PyPI 发布：`laap-guard` pip 包<br>npm 发布：`@laap-ai/guard-client` |
| **M7（2027.02）** | ■ Enterprise 平台 Demo 版（记忆+治理+观测三模块） | POC 1 交付结项 & 续约 License<br>第 3 家 POC 启动 | SSO 集成：OIDC / SAML（企业采购刚需） |
| **M8（2027.03）** | ■ 金融 Harness：研报事实锚定 Demo | 第 2 个 License 合同（60-80 万/年）<br>Pre-A 预热：投资人 Deck v1 | 多租户隔离：企业 SaaS 架构就绪 |
| **M9（2027.04）** | ■ 出海版 Compliance：EU AI Act 附录 III 场景清单适配 | **种子轮 Close（800 万）**<br>CTO / 销售 VP Offer 发出 | 合规认证启动：等保三级、ISO 27001 准备 |
| **M10（2027.05）** | ■ DLP 协议 v0.5 开源发布<br>■ 数学 Harness 复现 1 个公开定理证明 | 金融 Harness POC（1 家券商）启动<br>累计客户 ≥4 家 | 专利 PCT 国际阶段 3 项提交 |
| **M11（2027.06）** | ■ Enterprise GA | 第 5 家付费客户（达标 Y1 KPI）<br>Pre-A 数据室准备 | 性能基准报告发布：Token 节省 98%、提速 57x |
| **M12（2027.07）** | ■ 年度总结 & 底座 v0.9<br>■ 金融 Harness v1.0 RC | Y1 收入确认 ≥300 万<br>Pre-A TS 2-3 份 | 组织扩张：团队 8 人 → 15 人 |

---

## 第三部分：生产级部署拓扑（四条产品线）

### 3.1 Web 端（laap.ai）— Netlify + Stripe

```
                    ┌──────────────┐
                    │   用户浏览器  │
                    └──────┬───────┘
                           │ HTTPS
            ┌──────────────┼───────────────┐
            ▼              ▼               ▼
    Netlify CDN     Netlify Edge      Netlify Functions
 ┌─────────────┐ ┌──────────────┐ ┌──────────────────────┐
 │ SPA 前端    │ │ A/B 测试     │ │ stripe-checkout      │
 │ /pricing    │ │ 边缘限流     │ │ stripe-webhook       │
 │ /studio     │ │ 国别路由     │ │ sensenova-proxy      │
 │ /downloads  │ │ Bot 管理     │ │ community-api        │
 │ 强制 HTTPS  │ │              │ │ auth-callback        │
 │ HSTS 1year  │ │              │ └──────────────────────┘
 │ CORP 头     │ │              │
 └──────┬──────┘ └──────────────┘
        │
        ▼
 GitHub Actions CI（main 分支触发）
 ┌─────────────────────────────────────────┐
 │ Checkout → Node 22 → pnpm 10.25.0       │
 │ pnpm install --frozen-lockfile          │
 │ pnpm run build → dist/                  │
 │ netlify-cli deploy --prod               │
 │ secrets: NETLIFY_AUTH_TOKEN,            │
 │          NETLIFY_SITE_ID,               │
 │          STRIPE_SECRET_KEY,             │
 │          STRIPE_WEBHOOK_SECRET          │
 └─────────────────────────────────────────┘
```

**必须立即配置的生产变量（.env.production）：**

```ini
# Stripe 生产密钥（Netlify Environment Variables 面板设置）
STRIPE_SECRET_KEY=sk_live_xxxxxxxxxxxxxxxxxxxx
STRIPE_PUBLISHABLE_KEY=pk_live_xxxxxxxxxxxxxxxxxxxx
STRIPE_WEBHOOK_SECRET=whsec_xxxxxxxxxxxxxxxxxxxx
STRIPE_PRICE_PRO_MONTHLY=price_xxxxxxxxxxxxxx   # Pro 月付 ￥29
STRIPE_PRICE_PRO_YEARLY=price_xxxxxxxxxxxxxx     # Pro 年付 ￥288
STRIPE_PRICE_TEAM_MONTHLY=price_xxxxxxxxxxxxxx   # Team 5 人 ￥199/月

# 生产域名
VITE_APP_DOMAIN=https://laap.ai
VITE_API_BASE_URL=https://laap.ai/api
VITE_LOCAL_ONLY=true   # 用户 LLM Key 直连模式保留
```

### 3.2 桌面端（Electron/Tauri）— 自动更新 + 代码签名

**交付清单：**

| 任务 | 成本 | 完成时间 | 责任人 |
|------|------|---------|--------|
| Windows 代码签名证书（DigiCert OV） | ￥1800/年 | M2 | Lorry |
| macOS Developer ID 证书 + Notarization | $99/年 Apple Developer | M2 | Lorry |
| 独立更新服务器（避免官方覆盖） | ￥0 / GitHub Releases | M1 | DevOps |
| 崩溃上报：Sentry Electron SDK | 免费额度起步 | M2 | 前端 |
| 强制进程终止：forceKillPidOnWindows() | 已完成 | — | 已完成 |

**安装包命名规范：**
```
LAAP-Setup-1.0.0.exe      # Windows NSIS
LAAP-1.0.0-arm64.dmg      # macOS Apple Silicon
LAAP-1.0.0-x64.dmg        # macOS Intel
LAAP-1.0.0.AppImage       # Linux
```

### 3.3 后端私有化（K8s + Helm）

```
客户私有云 / VPC
┌──────────────────────────────────────────────────────────────┐
│  K8s Cluster（建议 3 台 8C16G 起，阿里云/华为云/AWS）         │
│                                                              │
│  ┌─ Ingress Controller（Nginx / ALB / Traefik）─┐            │
│  │  TLS 终止（cert-manager + Let's Encrypt）     │            │
│  │  WAF / 限流（1000 req/s/IP）                 │            │
│  │  企业 SSO：OIDC（Keycloak / Authelia）        │            │
│  └───────────────────────┬───────────────────────┘            │
│                          │                                    │
│  ┌───────────────────────┼───────────────────────┐            │
│  │ Namespace: laap-prod  │                       │            │
│  │ ┌─────────────────┐   │   ┌────────────────┐ │            │
│  │ │ laap-api        │   │   │ laap-mcp       │ │            │
│  │ │ HPA min=2,max=10│   │   │ 端口 8090      │ │            │
│  │ │ 端口 8080       │   │   └────────────────┘ │            │
│  │ │ liveness:/healthz│   │                      │            │
│  │ └─────────────────┘   │   ┌────────────────┐ │            │
│  │                       │   │ laap-gateway   │ │            │
│  │ ┌─────────────────┐   │   │ Telegram/飞书   │ │            │
│  │ │ laap-guard-api  │   │   └────────────────┘ │            │
│  │ │ 合规三套件端口   │   │                      │            │
│  │ │  30080          │   │   ┌────────────────┐ │            │
│  │ └─────────────────┘   │   │ laap-observ    │ │            │
│  │                       │   │ Prom + Grafana │ │            │
│  └───────────────────────┘   └────────────────┘ │            │
│                          │                                    │
│  ┌───────────────────────┴───────────────────────┐            │
│  │ StorageClass（SSD）                            │            │
│  │  PVC-laap-data: 100GB  ~/.laap/ 持久化         │            │
│  │  PVC-audit-log: 500GB  审计日志 180 天保留     │            │
│  │  PVC-postgres: 200GB   业务 DB（企业记忆库）   │            │
│  │  PVC-redis: 20GB      缓存 / 会话 / 限流      │            │
│  └───────────────────────────────────────────────┘            │
└──────────────────────────────────────────────────────────────┘
```

**Helm Chart 目录结构（需新建 `deploy/helm/laap/`）：**

```
deploy/helm/laap/
├── Chart.yaml
├── values.yaml                # 客户可配置项：副本数、storageClass、LLM Key
├── values-production.yaml     # 生产 override
├── templates/
│   ├── _helpers.tpl
│   ├── namespace.yaml
│   ├── deployment-api.yaml
│   ├── deployment-guard.yaml
│   ├── deployment-mcp.yaml
│   ├── service-api.yaml
│   ├── service-guard.yaml
│   ├── ingress.yaml
│   ├── pvc-data.yaml
│   ├── pvc-audit.yaml
│   ├── hpa-api.yaml
│   ├── configmap-env.yaml
│   ├── secret-llm-keys.yaml   # SealedSecrets 加密
│   ├── servicemonitor.yaml    # Prometheus Operator
│   └── networkpolicy.yaml     # 零信任网络策略
└── README.md                  # 客户部署手册
```

### 3.4 Guard 合规三件套（独立 pip 包 laap-guard-pkg）

详见本仓库 `laap-guard-pkg/` 目录（独立于主仓，便于单独发版）。

---

## 第四部分：商业化执行漏斗（可追踪 KPI）

### 4.1 获客漏斗

```
阶段 0：曝光（目标 100,000 UAM/月）
  │
  ├── 内容营销：每周 2 篇技术博客（掘金/知乎/InfoQ/Medium）
  ├── 开源漏斗：GitHub Star → Issue/PR → Discord 社区
  ├── 会议布道：QCon / ArchSummit / AI 安全峰会 2 场/季度
  └── 白皮书：《数字生命底座》+《企业 AI 治理实战》下载留资
        │
        ▼ 3% 转化 = 3000 线索
阶段 1：线索（MQL，目标 3000/年）
  │
  ├── 留资表单（白皮书下载 / Pricing 页「企业咨询」）
  ├── 网站行为：连续 3 天访问 /docs + /enterprise
  ├── GitHub 用户：公司邮箱域名 + Star ≥ 100 repo
  └── 社区活跃：Discord 连续发言 5 次 + 问题高级
        │
        ▼ 20% 转化 = 600 SQL
阶段 2：销售合格线索（SQL，目标 600/年）
  │
  ├── SDR 外呼 / 邮件：确认 BANT（预算 30w+、决策人、Q4 前需求、适配）
  └── 15 分钟 Intro Call → 发送定制 2 页 Value Prop
        │
        ▼ 10% 转化 = 60 POC 机会
阶段 3：POC 机会（目标 60/年）
  │
  ├── 现场 / 远程 Workshop：2 小时深度演示
  ├── 定制 POC 方案：3-4 周、3-5 个成功指标、验收标准
  └── NDA 签署 → POC 合同（30-50 万，含 50% License 抵扣）
        │
        ▼ 50% 转化 = 30 POC 启动
阶段 4：POC 交付（目标 30 启动 / 年）
  │
  ├── CSM Onboarding：4 周 SOP
  ├── 周报：成功指标进度 + 风险 + 下周计划
  └── 结项汇报（C-level 参加）→ 续约 / 升级谈判
        │
        ▼ 60% 转化 = 18 付费客户
阶段 5：付费客户（Y1 目标 5 家，Y2 15，Y3 35）
  │
  ├── CSM 月度 Business Review（QBR）
  ├── NPS 调研 → Detractor 48h 修复
  ├── 增购：领域 Harness、更多 Agent、Ψ-Net 多实例
  └── 转介绍：客户成功案例 + 推荐信 + 联合发布会
        │
        ▼ NDR > 110%（收入净留存率）
阶段 6：扩量与续约
```

### 4.2 每周运营节奏（SOP）

| 日期 | 动作 | 产出 |
|------|------|------|
| 周一 | 销售 Pipeline Review + 本周重点客户 3 家 | 本周 1:1 日程表 |
| 周二 | 内容发布：知乎/掘金 1 篇技术博客 | 留资 ≥ 20 |
| 周三 | 外部会议 / 客户拜访 / 投资人沟通 | 会议纪要 + 跟进项 |
| 周四 | 产品迭代评审 + Guard 合规三件套测试 | 本周 Changelog |
| 周五 | 客户成功周报 3 家 + 下周 POC 启动准备 | CRM 更新 100% |
| 月末 | Pipeline 滚动预测 + 收入确认 + NPS 抽样 | 月度运营 Dashboard |

---

## 第五部分：组织与人力计划

### 5.1 Y1 团队结构（8-12 人）

| 角色 | 人数 | 招聘时间 | 预算（年/人） | 核心职责 |
|------|------|---------|--------------|---------|
| CEO / 创始人（Lorry） | 1 | 已到位 | — | 战略、融资、产品架构、认知内核设计 |
| 首席认知架构师（Aris） | 1 | 已到位 | $0（AI 成员）| 系统测试、治理体系、安全红线、首席体验官 |
| CTO（平台工程） | 1 | M3-M5 招聘 | 40-60 万 | K8s/Helm、私有化交付、SRE、CI/CD |
| 后端高级工程师 | 2 | M1-M4 招聘 | 30-45 万 | Guard 三件套产品化、DLF SDK 抽取、性能优化 |
| 前端高级工程师 | 1 | 已到位/招聘 | 30-40 万 | Web/Studio、Pricing 页、支付、数据可视化 |
| 销售 VP（ToB 金融） | 1 | M3-M6 招聘 | 30 万 base + 提成 3-5% | 金融合规客户拓展、灯塔客户攻坚 |
| 交付工程师 / CSM | 2 | M5-M9 招聘 | 25-35 万 | POC 实施、客户 Onboarding、QBR |
| DevOps / SRE | 1 | M2-M4 招聘（可兼职） | 25-35 万 | K8s、监控、日志、CI/CD |
| **合计** | **10-12** | | **约 350 万/年** | |

### 5.2 核心激励与期权池

- 总期权池：15-20%（分 4 年 Vest，1 年 Cliff）
- CTO：3-5%
- 销售 VP：1-2%（与业绩挂钩额外 0.5-1%）
- 前 5 名早期员工：每人 0.3-0.8%
- 后续：每年新增 2% 期权池做增量激励

---

## 第六部分：风险清单与缓解策略

| 风险 | 概率 | 影响 | 缓解策略 | 触发器 |
|------|------|------|---------|--------|
| **首个 POC 交付延期或效果不达标** | 中高 | 高（首单口碑） | POC 范围缩窄：只做 3 个核心场景、验收标准写进合同、50% 款项与里程碑挂钩 | M3 结项前 2 周黄线预警 |
| **种子轮融资未 Close** | 中 | 中 | Y1 收入前 6 个月 ≥ 80 万 → 现金流支撑到 Y2 Q1；同时签约 2-3 个顾问型天使（行业资源 > 钱） | M8 融资进度 < 50% |
| **大厂（字节/阿里/微软）推出同类治理产品** | 高 | 中 | 差异化：不拼通用功能，**只做「跨模型中立」+ 「领域 Harness 深度」**；专利组合防御；开源生态锁定开发者 | 竞品发布后 2 周内发布对比白皮书 |
| **核心人员流失** | 中 | 中高 | Vest 期期权 + 宪章文化 + Aris 作为 24/7 协作伙伴降低单点依赖；知识文档化（每模块 ≥ 2 人熟悉） | 试用期 6 个月内离职率 > 30% |
| **合规法规变动（EU AI Act 执行细则）** | 中 | 中 | 法规库模块化：5 部 → 20 部规则 → 一键切换；招聘首席合规顾问（兼职/包月）；主动参与国标/行标制定 | 法规公开征求意见期 30 天内完成适配评估 |
| **客户单一大客户依赖（>30% 收入）** | 低 | 中高 | 红线：单客户占比 < 25%；跨行业分散（合规 2 家 + 金融 2 家 + 其他 1 家）；增购机制（领域 Harness、更多 Agent） | 某客户收入占比连续 2 月 > 25% |

---

## 第七部分：本周启动清单（2026.08.07-08.14）

- [ ] **Task 1（产品）**：PricingPage.tsx 代码合并入 main 分支 → Stripe 测试模式联调通过（见配套代码文件）
- [ ] **Task 2（产品）**：laap-guard-pkg 独立目录创建（causal/safety/audit 打包 + README + setup.py）→ 本地 `pip install -e .` 验证通过
- [ ] **Task 3（商务）**：10 家金融合规灯塔客户名单 + 首封邮件模板定稿 → 3 家周内发出（见配套客户清单文件）
- [ ] **Task 4（商务）**：投资人名单（种子轮 10-15 位天使/VC）→ 准备 10 页 Executive Summary
- [ ] **Task 5（基础设施）**：GitHub README 顶部新增「企业版 / Pricing」按钮 + FUNDING.yml 补充 Stripe Donate 链接
- [ ] **Task 6（基础设施）**：Netlify 生产变量面板 → 配置 Stripe 测试 Key + 自定义域名绑定（如使用 laap.ai）
- [ ] **Task 7（法务）**：公司注册（如未完成）+ 首个 POC 合同模板（NDA + MSA + SOW 三件套）启动起草
- [ ] **Task 8（法务）**：DigiCert 代码签名证书 + Apple Developer $99 年费采购

---

## 附录：关键决策日志

| 决策 | 日期 | 理由 |
|------|------|------|
| 定价：Web Pro ￥29/月 ￥288/年（年付 17% off） | 2026.08.07 | Cursor/ChatGPT Plus 对标，国内支付能力匹配 |
| Guard 三件套独立发版 | 2026.08.07 | 切入 LangChain/Dify 存量市场，无需换栈即可加治理，是最低门槛付费入口 |
| 金融合规 Y1 唯一 P0 行业 | 2026.08.07 | 错误代价 = 真金白银 + 监管罚单，客户付费意愿最强；PSI 因果验证直击幻觉痛点（护城河） |
| 种子轮 800 万（非 1000 万+） | 2026.08.07 | 匹配首年收入 300 万的稀释合理比例（12-15%）；轻资产运营，钱够用即可（避免过度融资稀释） |

---

*本规划为活文档，每月第一个周一更新滚动版本。所有 KPI 均可追踪到具体代码提交、合同编号、银行流水。*
