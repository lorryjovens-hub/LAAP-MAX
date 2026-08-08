# LAAP Community · 云端 API 配置说明（阶段1）

## 1. 初始化数据库

在 **Supabase**（SQL Editor）或 **Neon**（SQL 控制台）执行：

```
db/0001_init.sql
```

创建：`users` / `works` / `comments` / `work_likes` / `sync_cursors` + 枚举 + 触发器。

## 2. 环境变量（在 Netlify → Site → Environment variables 配置）

| 变量 | 说明 |
|---|---|
| `SUPABASE_URL` | Supabase 项目 URL（如 `https://xxx.supabase.co`） |
| `SUPABASE_SERVICE_ROLE_KEY` | service-role key（绕过 RLS，仅云端 Functions 使用，切勿暴露给前端） |
| `JWT_SECRET` | 自定义签名密钥（随机长字符串），未配置时用开发默认值 |

## 3. 本地测试

```bash
# 安装依赖
pnpm install

# 本地起 Netlify 环境（需先安装 netlify-cli）
netlify dev

# 验证
curl http://localhost:8888/.netlify/functions/community-api/health
curl http://localhost:8888/api/health          # 经 /api/* 转发
```

## 4. 部署

```bash
netlify deploy --prod
```

## 5. 路由

`netlify/functions/community-api.mjs` 统一入口，由 `netlify.toml` 把 `/api/*` 转发到该函数：

```
GET  /api/health
POST /api/auth/register { email, password, name }
POST /api/auth/login    { email, password }
GET  /api/me            （Authorization: Bearer <token>）
GET  /api/works?page=&type=&tag=&limit=
POST /api/works         （需登录；{ title, description?, type?, files_ref, tags?, size? }）
GET  /api/works/:id
```

> `like` / `play` / `comments` 为阶段3预留（当前返回 501）。
> 文件上传（作品文件到对象存储）在阶段2实现，`files_ref` 目前由调用方提供。