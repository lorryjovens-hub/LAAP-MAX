#!/bin/bash
set -e

echo "🚀 Web Replica Harness 部署脚本"

# 检查环境
if [ -z "$OPENAI_API_KEY" ]; then
    echo "❌ 错误: OPENAI_API_KEY 未设置"
    exit 1
fi

# 创建必要目录
mkdir -p uploads outputs sandbox/screenshots memory

# 启动基础设施
echo "📦 启动 Docker 基础设施..."
docker-compose up -d redis chroma prometheus grafana

# 等待服务就绪
echo "⏳ 等待服务就绪..."
sleep 5

# 构建并启动 Harness
echo "🔨 构建 Harness 服务..."
docker-compose build harness-api harness-worker

echo "🧠 启动 Harness 意识大脑..."
docker-compose up -d harness-api harness-worker

echo "✅ 部署完成！"
echo "📊 API 地址: http://localhost:8000"
echo "📈 Prometheus: http://localhost:9090"
echo "📉 Grafana: http://localhost:3000"
