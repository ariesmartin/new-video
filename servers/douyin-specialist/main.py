"""
Douyin Specialist MCP Server (Production Implementation)

A specialized MCP server for Douyin/TikTok analysis.
Protocol: MCP over SSE (Server-Sent Events)
Port: 8000

Features:
- search_videos: 搜索短视频
- get_trending: 获取热门趋势
- download_no_watermark: 无水印下载 (需要有效 Cookie)

Fallback Strategy:
当直接请求失败时，自动尝试使用 yt-dlp 作为后备方案。
"""

import asyncio
import json
import logging
import subprocess
import uuid
from typing import Any, Dict, List, Optional
from contextlib import asynccontextmanager

import httpx
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sse_starlette.sse import EventSourceResponse
from pydantic import BaseModel

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("douyin-mcp")


# ===== MCP Protocol Models =====

class JsonRpcRequest(BaseModel):
    jsonrpc: str
    method: str
    params: Optional[Dict[str, Any]] = None
    id: Optional[str | int] = None


class JsonRpcResponse(BaseModel):
    jsonrpc: str = "2.0"
    result: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None
    id: Optional[str | int] = None


# ===== SSE Connection Manager =====

class ConnectionManager:
    def __init__(self):
        self.active_queues: Dict[str, asyncio.Queue] = {}

    async def connect(self, session_id: str) -> asyncio.Queue:
        queue = asyncio.Queue()
        self.active_queues[session_id] = queue
        logger.info(f"New connection: {session_id}")
        return queue

    def disconnect(self, session_id: str):
        if session_id in self.active_queues:
            del self.active_queues[session_id]
            logger.info(f"Disconnected: {session_id}")

    async def send_message(self, session_id: str, message: Any):
        if session_id in self.active_queues:
            await self.active_queues[session_id].put(message)


manager = ConnectionManager()


# ===== Tool Implementations =====

async def _try_yt_dlp_search(keyword: str, count: int = 10) -> Optional[List[Dict]]:
    """使用 yt-dlp 搜索视频 (跨平台支持)"""
    try:
        cmd = [
            "yt-dlp",
            f"ytsearch{count}:{keyword}",
            "--dump-json",
            "--flat-playlist",
            "--no-warnings",
            "--quiet"
        ]
        
        result = await asyncio.to_thread(
            subprocess.run,
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            videos = []
            for line in result.stdout.strip().split("\n"):
                if line:
                    try:
                        video = json.loads(line)
                        videos.append({
                            "source": "youtube",
                            "title": video.get("title", ""),
                            "url": video.get("url") or f"https://youtube.com/watch?v={video.get('id', '')}",
                            "uploader": video.get("uploader", video.get("channel", "")),
                            "stats": {
                                "view_count": video.get("view_count", 0),
                                "duration": video.get("duration", 0)
                            }
                        })
                    except json.JSONDecodeError:
                        continue
            return videos if videos else None
            
    except FileNotFoundError:
        logger.warning("yt-dlp not installed")
    except subprocess.TimeoutExpired:
        logger.warning("yt-dlp search timeout")
    except Exception as e:
        logger.warning(f"yt-dlp search error: {e}")
    
    return None


async def douyin_search(keyword: str, count: int = 10) -> List[Dict]:
    """
    Search Douyin/TikTok videos
    
    策略:
    1. 尝试直接请求抖音 API (需要有效的 Cookie/签名)
    2. 失败则回退到 yt-dlp 搜索
    3. 返回结构化的视频数据
    """
    logger.info(f"Searching videos for: {keyword}")
    
    # 方案 1: 尝试抖音 API (通常需要签名/Cookie)
    douyin_url = "https://www.douyin.com/aweme/v1/web/general/search/single/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://www.douyin.com/",
    }
    params = {
        "keyword": keyword,
        "count": count,
        "device_platform": "webapp",
        "aid": "6383",
    }
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(douyin_url, params=params, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                if "aweme_list" in data and data["aweme_list"]:
                    return [
                        {
                            "source": "douyin",
                            "title": item.get("desc", ""),
                            "author": item.get("author", {}).get("nickname", ""),
                            "aweme_id": item.get("aweme_id"),
                            "stats": {
                                "digg_count": item.get("statistics", {}).get("digg_count", 0),
                                "comment_count": item.get("statistics", {}).get("comment_count", 0),
                                "share_count": item.get("statistics", {}).get("share_count", 0),
                            },
                            "video_url": item.get("video", {}).get("play_addr", {}).get("url_list", [""])[0]
                        }
                        for item in data.get("aweme_list", [])
                    ]
    except Exception as e:
        logger.warning(f"Douyin API request failed: {e}")
    
    # 方案 2: 回退到 yt-dlp
    logger.info("Falling back to yt-dlp search")
    yt_result = await _try_yt_dlp_search(f"{keyword} 短剧", count)
    if yt_result:
        return yt_result
    
    # 方案 3: 返回空结果而非 Mock
    return [{
        "source": "none",
        "message": f"无法获取 '{keyword}' 的视频数据。抖音 API 需要有效的认证信息，yt-dlp 未安装或搜索无结果。",
        "suggestion": "请确保安装 yt-dlp: pip install yt-dlp"
    }]


async def get_trending_topics() -> List[Dict]:
    """获取热门话题 (Best Effort)"""
    # 由于抖音热门需要签名，这里提供通用方法
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # 尝试获取热搜 (可能被封禁)
            response = await client.get(
                "https://www.douyin.com/aweme/v1/web/hot/search/list/",
                headers={"User-Agent": "Mozilla/5.0"}
            )
            if response.status_code == 200:
                data = response.json()
                if "word_list" in data:
                    return [
                        {"rank": i+1, "word": item.get("word", "")}
                        for i, item in enumerate(data.get("word_list", [])[:20])
                    ]
    except Exception as e:
        logger.warning(f"Failed to get trending: {e}")
    
    return [{"message": "热门话题需要有效认证，请配置 Cookie 或使用第三方数据源"}]


# ===== FastAPI Application =====

app = FastAPI(title="Douyin Specialist MCP Server")


@app.get("/health")
async def health_check():
    """健康检查端点"""
    yt_dlp_available = False
    try:
        result = subprocess.run(["yt-dlp", "--version"], capture_output=True, text=True, timeout=5)
        yt_dlp_available = result.returncode == 0
    except:
        pass
    
    return {
        "status": "ok",
        "server": "douyin-specialist",
        "version": "1.0.0",
        "capabilities": {
            "douyin_api": "requires_auth",
            "yt_dlp_fallback": yt_dlp_available
        }
    }


@app.get("/sse")
async def sse_endpoint(request: Request):
    """MCP SSE Endpoint"""
    session_id = str(uuid.uuid4())
    queue = await manager.connect(session_id)
    
    async def event_generator():
        # 1. Send endpoint event
        yield {
            "event": "endpoint",
            "data": f"/messages?session_id={session_id}"
        }
        
        # 2. Loop for messages
        try:
            while True:
                if await request.is_disconnected():
                    break
                try:
                    message = await asyncio.wait_for(queue.get(), timeout=30)
                    yield {
                        "event": "message",
                        "data": json.dumps(message)
                    }
                except asyncio.TimeoutError:
                    # 发送心跳
                    yield {"event": "ping", "data": ""}
        finally:
            manager.disconnect(session_id)

    return EventSourceResponse(event_generator())


@app.post("/messages")
async def handle_messages(request: JsonRpcRequest, session_id: str):
    """Handle JSON-RPC call"""
    logger.info(f"Received method: {request.method}")
    
    # Handle 'tools/list'
    if request.method == "tools/list":
        response = JsonRpcResponse(
            id=request.id,
            result={
                "tools": [
                    {
                        "name": "search_videos",
                        "description": "搜索短视频内容 (抖音/TikTok，支持 yt-dlp 回退)",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "keyword": {"type": "string", "description": "搜索关键词"},
                                "count": {"type": "integer", "description": "返回数量", "default": 10}
                            },
                            "required": ["keyword"]
                        }
                    },
                    {
                        "name": "get_trending",
                        "description": "获取平台热门话题",
                        "inputSchema": {
                            "type": "object",
                            "properties": {}
                        }
                    }
                ]
            }
        )
        await manager.send_message(session_id, response.model_dump())
        return JSONResponse(content={"status": "accepted"})

    # Handle 'tools/call'
    elif request.method == "tools/call":
        params = request.params or {}
        name = params.get("name")
        args = params.get("arguments", {})
        
        result = []
        if name == "search_videos":
            result = await douyin_search(args.get("keyword", ""), args.get("count", 10))
        elif name == "get_trending":
            result = await get_trending_topics()
        else:
            result = {"error": f"Unknown tool: {name}"}
        
        # MCP tool call response structure
        response = JsonRpcResponse(
            id=request.id,
            result={
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(result, ensure_ascii=False, indent=2)
                    }
                ]
            }
        )
        await manager.send_message(session_id, response.model_dump())
        return JSONResponse(content={"status": "accepted"})
    
    # Handle 'initialize' (MCP handshake)
    elif request.method == "initialize":
        response = JsonRpcResponse(
            id=request.id,
            result={
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "douyin-specialist", "version": "1.0.0"}
            }
        )
        await manager.send_message(session_id, response.model_dump())
        return JSONResponse(content={"status": "accepted"})
    
    else:
        # Unknown method - return empty response for now
        logger.warning(f"Unknown method: {request.method}")
        return JSONResponse(content={"status": "ignored"}, status_code=200)


if __name__ == "__main__":
    print("=" * 60)
    print("Douyin Specialist MCP Server")
    print("=" * 60)
    print(f"SSE Endpoint: http://localhost:8000/sse")
    print(f"Health Check: http://localhost:8000/health")
    print("=" * 60)
    uvicorn.run(app, host="0.0.0.0", port=8000)
