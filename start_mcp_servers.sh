#!/bin/bash

# ============================================================
# MCP Servers Launcher
# ============================================================
# 启动 Douyin MCP (Port 8000) 和 Browser MCP (Port 8001)
# ============================================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}============================================================${NC}"
echo -e "${BLUE}  MCP Servers Launcher${NC}"
echo -e "${BLUE}============================================================${NC}"

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# ===== 启动 Douyin MCP Server (Port 8000) =====
start_douyin_server() {
    echo -e "\n${YELLOW}[1/2] Starting Douyin MCP Server...${NC}"
    cd "$SCRIPT_DIR/servers/douyin-specialist"
    
    # 创建虚拟环境（如果不存在）
    if [ ! -d "venv" ]; then
        echo -e "${YELLOW}  Creating Python virtual environment...${NC}"
        python3 -m venv venv
    fi
    
    # 激活虚拟环境并安装依赖
    source venv/bin/activate
    
    # 检查依赖是否需要安装
    if ! python3 -c "import fastapi, uvicorn, sse_starlette" 2>/dev/null; then
        echo -e "${YELLOW}  Installing Python dependencies...${NC}"
        pip install -q -r requirements.txt
    fi
    
    # 启动服务器
    echo -e "${GREEN}  Starting Douyin MCP on port 8000...${NC}"
    python3 main.py &
    DOUYIN_PID=$!
    
    deactivate 2>/dev/null || true
    cd "$SCRIPT_DIR"
    
    # 等待服务启动
    sleep 2
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}  ✅ Douyin MCP Server is running (PID: $DOUYIN_PID)${NC}"
    else
        echo -e "${YELLOW}  ⚠️ Douyin MCP Server started but health check pending...${NC}"
    fi
}

# ===== 启动 Browser MCP Server (Port 8001) =====
start_browser_server() {
    echo -e "\n${YELLOW}[2/2] Starting Browser Automation MCP Server...${NC}"
    cd "$SCRIPT_DIR/servers/browser-automation"
    
    # 检查 Node.js
    if ! command -v node &> /dev/null; then
        echo -e "${RED}  ❌ Node.js not found! Please install Node.js 18+${NC}"
        return 1
    fi
    
    # 安装依赖（如果需要）
    if [ ! -d "node_modules" ]; then
        echo -e "${YELLOW}  Installing Node.js dependencies...${NC}"
        npm install --silent
    fi
    
    # 构建 TypeScript
    echo -e "${YELLOW}  Building TypeScript...${NC}"
    npm run build --silent 2>/dev/null || npm run build
    
    # 启动服务器
    echo -e "${GREEN}  Starting Browser MCP on port 8001...${NC}"
    npm start &
    BROWSER_PID=$!
    
    cd "$SCRIPT_DIR"
    
    # 等待服务启动
    sleep 3
    if curl -s http://localhost:8001/health > /dev/null 2>&1; then
        echo -e "${GREEN}  ✅ Browser MCP Server is running (PID: $BROWSER_PID)${NC}"
    else
        echo -e "${YELLOW}  ⚠️ Browser MCP Server started but health check pending...${NC}"
    fi
}

# ===== 主流程 =====

# 检查是否有旧进程
if lsof -i:8000 > /dev/null 2>&1; then
    echo -e "${YELLOW}Port 8000 is in use. Killing existing process...${NC}"
    kill $(lsof -t -i:8000) 2>/dev/null || true
    sleep 1
fi

if lsof -i:8001 > /dev/null 2>&1; then
    echo -e "${YELLOW}Port 8001 is in use. Killing existing process...${NC}"
    kill $(lsof -t -i:8001) 2>/dev/null || true
    sleep 1
fi

# 启动服务器
start_douyin_server
start_browser_server

echo -e "\n${BLUE}============================================================${NC}"
echo -e "${GREEN}  MCP Servers Started Successfully!${NC}"
echo -e "${BLUE}============================================================${NC}"
echo -e "  Douyin MCP:  ${GREEN}http://localhost:8000${NC}"
echo -e "    - SSE:     http://localhost:8000/sse"
echo -e "    - Health:  http://localhost:8000/health"
echo -e ""
echo -e "  Browser MCP: ${GREEN}http://localhost:8001${NC}"
echo -e "    - SSE:     http://localhost:8001/sse"
echo -e "    - Health:  http://localhost:8001/health"
echo -e "${BLUE}============================================================${NC}"
echo -e "${YELLOW}  Press Ctrl+C to stop all servers${NC}"
echo -e "${BLUE}============================================================${NC}"

# 保存 PID 到文件以便后续管理
echo "$DOUYIN_PID $BROWSER_PID" > "$SCRIPT_DIR/.mcp_pids"

# 设置退出处理
cleanup() {
    echo -e "\n${YELLOW}Stopping MCP Servers...${NC}"
    kill $DOUYIN_PID 2>/dev/null || true
    kill $BROWSER_PID 2>/dev/null || true
    rm -f "$SCRIPT_DIR/.mcp_pids"
    echo -e "${GREEN}All servers stopped.${NC}"
    exit 0
}

trap cleanup SIGINT SIGTERM

# 等待进程
wait
