# LAAP 社区联网功能 · 规格说明（Spec）

> 版本：v1.0 · 2026-08-05 · 状态：规划确认，待实施
> 架构：**C 混合模式**（本地离线优先 + 云端公共社区）
> 社区范围：**多人公共社区**（需账号体系）
> 作品存储：**本地 + 云端同步**

---

## 1. 背景与目标

### 1.1 现状
- LAAP 社区服务器是本地 Node 服务（`community-server/server.cjs`，端口 8790），仅局域网可访问。
- 支持：浏览 / 发布 / 游玩用户生成的网页应用、网站、游戏；一键导出独立 APK。
- 作品存储在本机 `data/apps`，目录索引 `data/catalog.json`。
- 移动端 LAAP 通过 `http://<电脑局域网IP>:8790` 接入本地社区。

### 1.2 诉求
让 LAAP 社区**支持联网**：
1. 作品可发布到公网，任何人通过链接浏览 / 游玩。
2. 形成**多人公共社区**：多用户注册、发布、点赞、评论。
3. 本地开发、离线可用，上传到云端可分享——**本地与云端双向同步**。

### 1.3 目标能力
- 云端公共社区（公网 Web 前端 + REST API）。
- 账号体系（注册 / 登录 / 作者页）。
- 本地一键“发布到云端”，生成公网 URL。
- 浏览 / 点赞 / 播放计数 / 评论。
- 离线优先：本地社区始终可用，联网时同步。

---

## 2. 架构总览（混合模式）

```
┌─ 本地（离线优先）────────────────────────────────────────┐
│  LAAP 桌面 / 移动端                                      │
│    └─ server.cjs（本地社区，端口 8790）                  │
│        浏览 / 游玩 / 导出APK                            │
│        + sync agent（同步队列、本地缓存、登录态关联）      │
└──────────────┬──────────────────────────────────────────┘
               │ 双向同步 · HTTPS
               │ · push：发布 / 更新 / 下架作品
               │ · pull：社区列表 / 游玩 / 评论 / 点赞
┌──────────────▼──────────────────────────────────────────┐
│  云端公共社区（多人共享）                                 │
│    公网 Web 前端（社区页，可嵌入官网）                     │
│    REST API（作品 / 账号 / 点赞 / 评论 / 统计）            │
│    云数据库（User / Work / Comment / SyncCursor）         │
│    对象存储（作品文件：zip / html 资源）                   │
└─────────────────────────────────────────────────────────┘
```

### 2.1 关键设计原则
- **离线优先**：断网时本地社区照常浏览 / 游玩；联网后同步队列自动补传。
- **单一作品 ID**：本地与云端以同一 `work_id` 关联；云端为权威源。
- **游标同步**：`SyncCursor.last_synced_at` 增量拉取，避免全量。
- **最小改动**：保留现有 `server.cjs` 能力，新增模块而非重写。

---

## 3. 组件清单

| 模块 | 位置 | 说明 |
|---|---|---|
| 本地社区服务器 | `community-server/server.cjs`（已有） | 保留现有浏览/发布/游玩/导出 APK |
| 本地同步 Agent | `community-server/sync-agent.cjs`（新增） | 登录态、同步队列、发布到云端、增量拉取 |
| 云端社区 API | Netlify Functions（新增，`netlify/functions/community/*`） | REST API |
| 云端数据库 | Supabase / Neon（PostgreSQL） | 结构化数据 |
| 云端对象存储 | Netlify Blobs / OSS / S3 | 作品文件 |
| 公共前端 | 官网 `laap-netlify` 新增“社区”页（或独立子站） | 浏览/游玩/发布/点赞/评论 |
| 移动端接入 | LAAP-Mobile 社区 API base 切换 | 接入云端社区 + 本地社区双源 |

---

## 4. 数据模型

### 4.1 User（用户）
```
id            uuid       主键
email         string    唯一，登录凭证
password_hash string    加盐哈希（bcrypt/argon2）
name          string     昵称
avatar_url    string?    头像
bio           string?    简介
created_at    timestamptz
```

### 4.2 Work（作品）
```
id            uuid       主键（本地/云端共享）
owner_id      uuid       外键 → User.id
title         string
description   text?
type          enum       'webapp' | 'site' | 'game'
files_ref     string     对象存储路径/引用
size          bigint     字节数
tags          string[]?
likes         int        计数（冗余，便于列表）
plays         int        播放计数
status        enum       'published' | 'hidden' | 'reported'
published_at  timestamptz
updated_at    timestamptz
```

### 4.3 Comment（评论）
```
id            uuid
work_id       uuid       外键 → Work.id
user_id       uuid       外键 → User.id
text          text
created_at    timestamptz
```

### 4.4 SyncCursor（同步游标）
```
device_id     string     设备标识
user_id       uuid?
last_synced_at timestamptz
pending_ops   jsonb      待补传操作（本地→云端）
```

---

## 5. 同步协议

### 5.1 本地 → 云端（push）
| 操作 | 触发 | 说明 |
|---|---|---|
| `publish` | 本地发布/一键上传 | 上传作品文件到对象存储 + 写 Work 记录 |
| `update` | 编辑作品 | 更新元数据 / 替换文件 |
| `unpublish` | 下架 | 置 `status=hidden`（保留数据） |

### 5.2 云端 → 本地（pull）
| 操作 | 触发 | 说明 |
|---|---|---|
| `list` | 打开社区 | 按 `last_synced_at` 增量拉取作品列表 |
| `play` | 点开作品 | 流式拉取 / 代理作品文件 |
| `sync_meta` | 定时 | 拉取点赞数、播放数、评论变更 |

### 5.3 冲突处理
- 以云端 `Work.id` 为权威；本地 `updated_at` 较新时标记 `conflict`，由用户选择保留云端或重传。
- push 失败进入 `pending_ops`，联网后重试。

---

## 6. 云端 API 草案

### 6.1 认证
```
POST /api/auth/register   { email, password, name }
POST /api/auth/login      { email, password }
GET  /api/me              → 当前用户（JWT）
```
- JWT 会话，`Authorization: Bearer <token>`。

### 6.2 作品
```
GET  /api/works?page=&tag=&type=&sort=        # 列表/筛选/分页
POST /api/works                               # 发布（multipart: 元数据 + 文件）
GET  /api/works/:id                           # 详情
GET  /api/works/:id/files/:path               # 提供作品资源
PUT  /api/works/:id                           # 更新
DELETE /api/works/:id                         # 下架/删除
GET  /api/users/:id/works                     # 作者作品页
```

### 6.3 互动
```
POST /api/works/:id/like                      # 点赞（幂等）
POST /api/works/:id/play                      # 播放计数
GET  /api/works/:id/comments
POST /api/works/:id/comments
```

---

## 7. 部署拓扑

| 层 | 位置 | 技术 |
|---|---|---|
| 本地社区 | 用户电脑 | `server.cjs`（8790）+ `remote-bridge.cjs`（8791） |
| 云端 API | Netlify Functions | 无服务器函数 |
| 云端 DB | Supabase / Neon | PostgreSQL |
| 云端存储 | Netlify Blobs / OSS / S3 | 作品文件 |
| 公网前端 | 官网 `laap-netlify`「社区」页 / 独立子域 | Web |
| 域名 | 官网子路径或 `community.*` | HTTPS |

---

## 8. 分阶段实施

### 阶段1 · 联网地基
- [x] 云端数据库 Schema（User/Work/Comment/SyncCursor）+ 迁移脚本（`db/0001_init.sql`）
- [x] 对象存储接入（Supabase Storage，bucket `works`）
- [x] 账号 API：注册 / 登录 / 会话（JWT）（`netlify/functions/community-api.mjs`）
- [x] 本地 `sync-agent.cjs`：登录态、鉴权、push（发布/下架）+ pull（列表/导入/互动）
- [x] 部署到 Netlify，验证 `/api/health`

### 阶段2 · 发布同步
- [x] 本地“一键发布到云端”（push 文件 + 元数据）
- [x] 云端作品文件提供 `GET /works/:id/files/:path`（含 SPA fallback）
- [x] 公网社区页：浏览 / 游玩 / 作品详情（官网 `/community`）
- [ ] 增量 `pull` 同步（`last_synced_at`，当前为全量分页拉取）

### 阶段3 · 社区生态
- [x] 点赞 / 播放计数 / 评论
- [ ] 作者页、作品列表筛选 / 分页 / 搜索（分页已实现，筛选/搜索待完善）
- [ ] 移动端 LAAP 接入云端社区 + 本地双源
- [ ] 官网 / 文档中心更新（社区页与下载页已更新）

### 阶段4 · 运营与合规
- [ ] 内容审核（报告 / 隐藏 / 白名单）
- [ ] 上传配额、大小/类型限制、速率限制
- [ ] HTTPS / CDN / 数据备份
- [ ] 隐私与用户内容合规

---

## 9. 安全与合规

- **账号**：密码加盐哈希，JWT 短时 + 刷新；登录限流。
- **上传**：校验 MIME 白名单（html/js/css/png/jpg/svg/webp/wasm/mp4…），大小上限，防路径穿越。
- **内容**：公共社区需过滤不当作品；支持报告与人工下架。
- **传输**：全程 HTTPS；本地↔云端走 TLS。
- **数据**：作者拥有自己的作品；删除请求支持。

---

## 10. 与现有代码衔接

- `server.cjs`：`handlePublish` 扩展为“本地 + 可选云端”；`catalog.json` 增加 `cloud_id` / `synced_at` 字段。
- 官网 `laap-netlify`：DocsPage 新增联网社区章节；DownloadsPage 更新功能介绍。
- 移动端：社区 API base 可在“本地地址 / 云端地址”间切换。
- Remote Bridge 不受影响，继续提供手机控制桌面 LAAP。

---

## 11. 验收标准（Checklist）

- [ ] 手机/任意设备通过公网链接可浏览并游玩云端作品。
- [ ] 用户可注册 / 登录 / 发布作品到云端公共社区。
- [ ] 本地发布后可“一键同步到云端”，生成公网 URL。
- [ ] 云端作品可点赞、播放计数、评论。
- [ ] 断网时本地社区仍可用；联网后同步队列自动补传。
- [ ] 上传有大小/类型限制，存在内容审核与报告机制。