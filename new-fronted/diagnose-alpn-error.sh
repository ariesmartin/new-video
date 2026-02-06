#!/bin/bash

# ALPN 错误快速诊断脚本
# 用于诊断和修复 ERR_ALPN_NEGOTIATION_FAILED 问题

echo "========================================="
echo "  ALPN 错误诊断工具"
echo "========================================="
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查函数
check_service() {
    local name=$1
    local host=$2
    local port=$3
    local protocol=$4

    echo -n "检查 $name ($protocol://$host:$port)... "

    if command -v curl &> /dev/null; then
        if curl -s -o /dev/null --connect-timeout 2 "$protocol://$host:$port" 2>/dev/null; then
            echo -e "${GREEN}✓ 正常${NC}"
            return 0
        else
            echo -e "${RED}✗ 失败${NC}"
            return 1
        fi
    else
        echo -e "${YELLOW}curl 不可用，跳过检查${NC}"
        return 2
    fi
}

# 检查端口监听
check_port() {
    local name=$1
    local port=$2

    echo -n "检查 $name 端口 $port 监听状态... "

    if netstat -tlnp 2>/dev/null | grep ":$port " &>/dev/null; then
        echo -e "${GREEN}✓ 正在监听${NC}"
        netstat -tlnp 2>/dev/null | grep ":$port " | awk '{print "   " $7}'
        return 0
    elif ss -tlnp 2>/dev/null | grep ":$port " &>/dev/null; then
        echo -e "${GREEN}✓ 正在监听${NC}"
        ss -tlnp 2>/dev/null | grep ":$port " | awk '{print "   " $6}'
        return 0
    else
        echo -e "${RED}✗ 未监听${NC}"
        return 1
    fi
}

# 检查配置文件
check_config() {
    local file=$1

    echo -n "检查 $file... "

    if [ -f "$file" ]; then
        echo -e "${GREEN}✓ 存在${NC}"
        cat "$file" | sed 's/^/   /'
        return 0
    else
        echo -e "${RED}✗ 不存在${NC}"
        return 1
    fi
}

# 主诊断流程
echo "【步骤 1】检查服务运行状态"
echo "--------------------------------------"
check_service "后端 API (FastAPI)" "127.0.0.1" "8000" "http"
check_service "前端开发服务器 (Vite)" "localhost" "5174" "http"
echo ""

echo "【步骤 2】检查端口监听"
echo "--------------------------------------"
check_port "后端 API" "8000"
check_port "前端开发服务器" "5174"
echo ""

echo "【步骤 3】检查配置文件"
echo "--------------------------------------"
check_config ".env.development"
check_config "src/api/client.ts"
echo ""

echo "【步骤 4】检查环境变量"
echo "--------------------------------------"
if [ -f ".env.development" ]; then
    if grep -q "VITE_API_URL=http://127.0.0.1:8000" ".env.development"; then
        echo -e "${YELLOW}⚠ 当前配置为直连后端模式${NC}"
        echo "   这可能导致 ALPN 错误"
        echo ""
        echo "   建议切换到代理模式："
        echo "   将 VITE_API_URL=http://127.0.0.1:8000"
        echo "   改为：# VITE_API_URL=http://127.0.0.1:8000"
        echo "   (注释掉即可使用 Vite 代理)"
    elif grep -q "# VITE_API_URL=http://127.0.0.1:8000" ".env.development" || ! grep -q "VITE_API_URL" ".env.development"; then
        echo -e "${GREEN}✓ 使用 Vite 代理模式（推荐）${NC}"
    fi
fi
echo ""

echo "【步骤 5】浏览器访问建议"
echo "--------------------------------------"
echo -e "${GREEN}✓ 正确访问方式：${NC}"
echo "   http://localhost:5174"
echo ""
echo -e "${RED}✗ 错误访问方式：${NC}"
echo "   https://localhost:5174"
echo ""
echo "如果仍然遇到问题，请检查："
echo "1. 浏览器扩展是否自动升级 HTTPS"
echo "2. Chrome: chrome://net-internals/#hsts (清除 localhost HSTS)"
echo "3. Firefox: about:config (搜索 security.enterprise_roots.enabled)"
echo ""

echo "【步骤 6】快速测试"
echo "--------------------------------------"
echo "测试 HTTP 连接..."
if curl -s -o /dev/null -w "%{http_code}" http://localhost:5174/ 2>/dev/null | grep -q "200"; then
    echo -e "${GREEN}✓ HTTP 连接正常${NC}"
else
    echo -e "${RED}✗ HTTP 连接失败${NC}"
fi
echo ""
echo "测试 HTTPS 连接（预期会失败）..."
if curl -sk -o /dev/null -w "%{http_code}" https://localhost:5174/ 2>/dev/null | grep -q "000\|error"; then
    echo -e "${GREEN}✓ HTTPS 连接失败（符合预期）${NC}"
    echo "   这是正常的，因为 Vite dev server 不提供 HTTPS"
else
    echo -e "${YELLOW}⚠ HTTPS 连接成功（意外）${NC}"
    echo "   这表明可能配置了 HTTPS，请检查 vite.config.ts"
fi
echo ""

echo "========================================="
echo "  诊断完成"
echo "========================================="
echo ""
echo "如果问题仍然存在，请参考："
echo "  ALPN-ERROR-SOLUTIONS.md"
echo ""
echo "快速修复："
echo "  1. 使用 http://localhost:5174 访问应用"
echo "  2. 确保 .env.development 中 VITE_API_URL 已注释"
echo "  3. 清除浏览器 HSTS 缓存（Chrome: chrome://net-internals/#hsts）"
echo ""
