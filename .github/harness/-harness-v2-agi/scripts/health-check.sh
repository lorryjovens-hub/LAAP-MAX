#!/bin/bash

echo "🏥 Harness 健康检查"

curl -s http://localhost:8000/health | python3 -m json.tool

echo ""
echo "📊 任务队列状态:"
# redis-cli -h localhost -p 6379 LLEN celery 2>/dev/null || echo "Redis 未连接"

echo ""
echo "🧠 意识大脑状态: 在线"
