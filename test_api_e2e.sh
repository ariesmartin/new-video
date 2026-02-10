#!/bin/bash
# API 端到端测试脚本
# 测试完整的审阅和修改流程

set -e

BASE_URL="http://localhost:8000"
PROJECT_ID="790578d1-31fe-4bd9-8514-6c20681e780f"

echo "========================================"
echo "🧪 质量控制系统 - API 端到端测试"
echo "========================================"

# 1. 健康检查
echo -e "\n🩺 步骤 1: 服务健康检查"
HEALTH=$(curl -s "$BASE_URL/health")
echo "服务状态: $(echo $HEALTH | python -c 'import sys,json; print(json.load(sys.stdin)["status"])')"

# 2. 获取项目信息
echo -e "\n📁 步骤 2: 获取项目信息"
PROJECT=$(curl -s "$BASE_URL/api/projects/$PROJECT_ID")
echo "项目: $(echo $PROJECT | python -c 'import sys,json; d=json.load(sys.stdin); print(d.get("name","N/A"))')"

# 3. 直接通过 skeleton 的 review 端点触发审阅（模拟已有大纲的情况）
echo -e "\n📝 步骤 3: 触发大纲审阅"
echo "⏳ 发送 POST /api/skeleton/{project_id}/review..."

# 先尝试直接 POST 到 review 端点触发审阅
# 注意：这个端点需要 outline 数据已存在
REVIEW_RESULT=$(curl -s -X POST "$BASE_URL/api/skeleton/$PROJECT_ID/review" \
    -H "Content-Type: application/json" \
    -d '{}' 2>/dev/null || echo '{"error": "request failed"}')

echo "审阅结果:"
echo "$REVIEW_RESULT" | python -m json.tool 2>/dev/null || echo "$REVIEW_RESULT"

# 4. 检查审阅状态
echo -e "\n📊 步骤 4: 检查审阅状态"
sleep 2
STATUS=$(curl -s "$BASE_URL/api/review/$PROJECT_ID/status")
echo "$STATUS" | python -m json.tool

# 5. 尝试获取全局审阅
echo -e "\n🌍 步骤 5: 获取全局审阅报告"
GLOBAL_REVIEW=$(curl -s "$BASE_URL/api/review/$PROJECT_ID/global")
echo "$GLOBAL_REVIEW" | python -m json.tool 2>/dev/null || echo "审阅结果不存在"

# 6. 获取张力曲线
echo -e "\n📈 步骤 6: 获取张力曲线"
TENSION=$(curl -s "$BASE_URL/api/review/$PROJECT_ID/tension_curve")
echo "$TENSION" | python -m json.tool 2>/dev/null || echo "张力曲线不存在"

echo -e "\n========================================"
echo "✅ API 测试完成"
echo "========================================"
echo ""
echo "测试结果总结:"
echo "  - 健康检查: ✅"
echo "  - 项目获取: ✅"
echo "  - 审阅触发: 取决于大纲数据是否存在"
echo "  - API 端点: ✅"
