# LAAP 下载资源

下载资源已托管至 GitHub Releases：
https://github.com/lorryjovens-hub/LAAP-Living-Agent-Application-Protocol-/releases/tag/v2026.08.03-downloads

## 文件清单

- `Aris-Pi-windows-x64.zip` — Windows 终端数字生命体 CLI（约 98 MB）
- `LAAP.apk` — Android 移动端 companion（约 173 MB）
- `LAAP-Community-Server-windows.zip` — 社区服务器 + APK 导出 + 手机远程控制（约 64 KB，随官网静态托管）

> 说明：`LAAP-Community-Server-windows.zip` 较小，直接随官网 `public/downloads/` 托管，
> 下载页通过相对路径 `/downloads/...` 引用，无需上传 GitHub Releases。

## 开发说明

本地开发时，Vite 中间件仍会代理 `/downloads/*` 到原始文件路径；生产构建后页面直接使用上述 GitHub Releases URL。
