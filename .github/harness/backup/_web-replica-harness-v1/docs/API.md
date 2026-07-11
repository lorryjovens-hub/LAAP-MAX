# API 文档

## 核心接口

### 提交复现任务

```bash
POST /api/v1/replicate
Content-Type: multipart/form-data

Form Fields:
  - image: File (PNG/JPG/WebP)
  - video: File (MP4/WebM, optional)
  - config: JSON string

Config Format:
{
  "framework": "react|vue|svelte|next|nuxt",
  "style_system": "tailwind|css-modules|styled-components",
  "animation": "auto|minimal|rich|none",
  "responsive": true,
  "accessibility": true,
  "max_colors": 12,
  "target_lighthouse_score": 90
}
```

### 查询任务状态

```bash
GET /api/v1/tasks/{task_id}/status
```

Response:
```json
{
  "task_id": "uuid",
  "status": "perceiving|reasoning|generating|verifying|revising|completed|failed",
  "progress_percent": 75,
  "current_stage": "视觉回归测试...",
  "logs": ["..."]
}
```

### 获取结果

```bash
GET /api/v1/tasks/{task_id}/result
```

### 下载代码包

```bash
GET /api/v1/tasks/{task_id}/download
```

### 人工修正

```bash
POST /api/v1/tasks/{task_id}/revise?feedback=修改导航栏颜色为蓝色
```
