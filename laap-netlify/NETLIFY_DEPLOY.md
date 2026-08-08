# Netlify Git 部署说明

当前版本为**本地优先（Local-First）**：所有对话、性格配置与长期记忆都保存在用户浏览器的 IndexedDB 中，每个浏览器实例相互隔离；LAAP 直接使用用户配置的 LLM API Key 进行对话，无需额外后端即可部署到 Netlify。

## 1. 推送仓库

```bash
cd laap-netlify-git
git init
git add .
git commit -m "init laap netlify site"
git remote add origin https://github.com/YOUR_NAME/laap-netlify.git
git push -u origin main
```

## 2. Netlify 导入项目

1. 登录 [Netlify](https://app.netlify.com/)
2. **Add new site** → **Import an existing project**
3. 选择 GitHub 仓库 `YOUR_NAME/laap-netlify`
4. 构建设置 Netlify 会自动识别 `netlify.toml`：
   - Build command: `pnpm run build`
   - Publish directory: `dist`
5. 点击 **Deploy site**

部署后访问 `/studio` 即可开始对话。首次使用需要在侧边栏配置 LLM API Key（OpenAI 或 DeepSeek）。

## 3. 切回后端模式（可选）

如果你希望使用 FastAPI 后端（例如需要跨设备同步或统一代理 LLM 请求）：

- 进入 Netlify 站点 → **Site configuration** → **Environment variables**
- 删除 `VITE_LOCAL_ONLY`，添加 `VITE_API_BASE_URL=https://你的后端地址`
- 或在 `netlify.toml` 中注释掉 `VITE_LOCAL_ONLY`，取消 `VITE_API_BASE_URL` 注释
- 同时取消 `[[redirects]] /api/*` 注释，把地址改成你的后端

## 注意

- 数据完全保存在当前浏览器的 IndexedDB 中，清除浏览器数据或退出登录会清空该实例。
- 不同浏览器、不同用户、不同设备之间天然隔离，每个 LAAP 实例都有独立的记忆与性格。
- 所有视频、图片都已放在 `public/assets/`，Netlify 会自动随构建发布。
- 如果 LLM 提供商限制浏览器直接请求（CORS），可改用后端模式或在 LLM 配置里使用支持 CORS 的代理地址。
