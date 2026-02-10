#!/bin/bash
# 模拟前端 API 调用测试

BASE_URL="http://localhost:3000"  # 前端代理地址
PROJECT_ID="790578d1-31fe-4bd9-8514-6c20681e780f"

echo "========================================"
echo "🧪 模拟前端 API 调用测试"
echo "========================================"

# 测试 1: 通过前端代理访问后端
echo -e "\n1️⃣ 测试通过前端代理 (port 3000) 访问后端:"
echo "   GET $BASE_URL/api/skeleton/$PROJECT_ID/review"
curl -s "http://localhost:3000/api/skeleton/$PROJECT_ID/review" | python -m json.tool 2>/dev/null || echo "   ❌ 前端服务未启动或代理失败"

# 测试 2: 直接访问后端
echo -e "\n2️⃣ 测试直接访问后端 (port 8000):"
echo "   GET http://localhost:8000/api/skeleton/$PROJECT_ID/review"
curl -s "http://localhost:8000/api/skeleton/$PROJECT_ID/review" | python -m json.tool

# 测试 3: 检查前端是否运行
echo -e "\n3️⃣ 检查前端服务状态:"
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 2>/dev/null | grep -q "200" && echo "   ✅ 前端服务运行中 (port 3000)" || echo "   ⚠️ 前端服务未运行或无法访问"

echo -e "\n========================================"
echo "📋 诊断建议"
echo "========================================"
echo "如果测试 1 失败但测试 2 成功:"
echo "  → 前端代理配置可能有问题"
echo "  → 检查 vite.config.ts 中的 proxy 配置"
echo ""
echo "如果都失败:"
echo "  → 后端服务可能未正确启动"
echo "  → 检查路由注册情况"
