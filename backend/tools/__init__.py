"""
LangGraph Tools Package (Production - Self-Contained)

Agent 工具定义。提供 LangGraph Agent 可调用的真实工具集。

设计原则:
1. **零外部依赖**: 所有功能内置，无需启动额外服务
2. **真实可用**: 每个工具都经过验证，返回真实数据
3. **一键启动**: 用户只需启动 Backend 即可

工具清单 (符合 System Architecture 4.2):
- duckduckgo_search: 网络搜索 (兜底搜索)
- video_search: 视频搜索 (yt-dlp, 支持多平台)
- browser_scrape: 网页抓取 (playwright)
- browser_screenshot: 网页截图 (playwright)
"""

import os
import sys
import json
import asyncio
import tempfile
import subprocess
import structlog
import httpx
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.tools import tool
from backend.tools.metaso_search import metaso_search

logger = structlog.get_logger(__name__)


# ===== 1. Web Search Tool (DuckDuckGo) =====


@tool
def duckduckgo_search(query: str) -> str:
    """
    DuckDuckGo 网络搜索

    轻量级搜索引擎，无需 API Key，适合通用查询。

    注意: 这是同步工具函数，在异步环境中使用 asyncio.to_thread() 包装

    Args:
        query: 搜索关键词

    Returns:
        搜索结果文本
    """
    try:
        search = DuckDuckGoSearchRun()
        result = search.invoke(query)
        logger.info("DuckDuckGo search completed", query=query)
        return str(result)
    except Exception as e:
        logger.error("DuckDuckGo search failed", error=str(e))
        return f"搜索失败: {str(e)}"


async def duckduckgo_search_async(query: str) -> str:
    """
    DuckDuckGo 网络搜索 - 异步版本

    使用 asyncio.to_thread() 避免阻塞事件循环
    """
    import asyncio

    try:
        return await asyncio.to_thread(duckduckgo_search, query)
    except Exception as e:
        logger.error("Async search failed", error=str(e))
        return f"搜索失败: {str(e)}"


# ===== 2. Video Search Tool (yt-dlp) =====


@tool
def video_search(keyword: str, count: int = 5, platform: str = "youtube") -> str:
    """
    多平台视频搜索

    使用 yt-dlp 搜索视频，支持 YouTube 等多个平台。
    返回视频标题、URL、播放量等信息。

    Args:
        keyword: 搜索关键词 (如 "霸总短剧", "甜宠逆袭")
        count: 返回视频数量 (默认 5)
        platform: 搜索平台 (youtube, bilibili 等)

    Returns:
        JSON 格式的视频列表
    """
    logger.info("Video search started", keyword=keyword, count=count, platform=platform)

    try:
        # 构建搜索命令
        if platform == "bilibili":
            search_query = f"bilisearch{count}:{keyword}"
        else:
            search_query = f"ytsearch{count}:{keyword}"

        cmd = [
            sys.executable,
            "-m",
            "yt_dlp",
            search_query,
            "--dump-json",
            "--flat-playlist",
            "--no-warnings",
            "--quiet",
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

        if result.returncode == 0 and result.stdout.strip():
            videos = []
            for line in result.stdout.strip().split("\n"):
                if line:
                    try:
                        video = json.loads(line)
                        videos.append(
                            {
                                "title": video.get("title", ""),
                                "url": video.get("url")
                                or video.get("webpage_url")
                                or f"https://youtube.com/watch?v={video.get('id', '')}",
                                "uploader": video.get("uploader") or video.get("channel", ""),
                                "view_count": video.get("view_count", 0),
                                "duration": video.get("duration", 0),
                                "platform": platform,
                            }
                        )
                    except json.JSONDecodeError:
                        continue

            if videos:
                logger.info("Video search completed", count=len(videos))
                return json.dumps(videos, ensure_ascii=False, indent=2)

        return json.dumps({"error": "未找到视频", "keyword": keyword}, ensure_ascii=False)

    except subprocess.TimeoutExpired:
        return json.dumps({"error": "搜索超时，请稍后重试"}, ensure_ascii=False)
    except Exception as e:
        logger.error("Video search failed", error=str(e))
        return json.dumps({"error": f"搜索失败: {str(e)}"}, ensure_ascii=False)


async def video_search_async(keyword: str, count: int = 5, platform: str = "youtube") -> str:
    """
    多平台视频搜索 - 异步版本

    使用 asyncio.create_subprocess_exec 避免阻塞事件循环
    """
    import asyncio

    logger.info("Video search async started", keyword=keyword, count=count, platform=platform)

    try:
        if platform == "bilibili":
            search_query = f"bilisearch{count}:{keyword}"
        else:
            search_query = f"ytsearch{count}:{keyword}"

        cmd = [
            sys.executable,
            "-m",
            "yt_dlp",
            search_query,
            "--dump-json",
            "--flat-playlist",
            "--no-warnings",
            "--quiet",
        ]

        # 使用异步子进程
        proc = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )

        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=60)
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            return json.dumps({"error": "搜索超时，请稍后重试"}, ensure_ascii=False)

        if proc.returncode == 0 and stdout:
            videos = []
            for line in stdout.decode().strip().split("\n"):
                if line:
                    try:
                        video = json.loads(line)
                        videos.append(
                            {
                                "title": video.get("title", ""),
                                "url": video.get("url")
                                or video.get("webpage_url")
                                or f"https://youtube.com/watch?v={video.get('id', '')}",
                                "uploader": video.get("uploader") or video.get("channel", ""),
                                "view_count": video.get("view_count", 0),
                                "duration": video.get("duration", 0),
                                "platform": platform,
                            }
                        )
                    except json.JSONDecodeError:
                        continue

            if videos:
                logger.info("Video search async completed", count=len(videos))
                return json.dumps(videos, ensure_ascii=False, indent=2)

        return json.dumps({"error": "未找到视频", "keyword": keyword}, ensure_ascii=False)

    except Exception as e:
        logger.error("Video search async failed", error=str(e))
        return json.dumps({"error": f"搜索失败: {str(e)}"}, ensure_ascii=False)


@tool
def video_info(url: str) -> str:
    """
    获取视频详细信息

    获取单个视频的详细信息，包括标题、描述、时长等。
    支持平台: YouTube, Bilibili, 抖音, TikTok, 小红书等。

    注意: 抖音等平台可能需要配置 cookies 以获取完整信息。

    Args:
        url: 视频 URL (支持多平台)

    Returns:
        JSON 格式的视频信息
    """
    logger.info("Getting video info", url=url)

    try:
        # 基础命令
        cmd = [
            sys.executable,
            "-m",
            "yt_dlp",
            url,
            "--dump-json",
            "--no-download",
            "--no-warnings",
            "--quiet",
            "--no-check-certificates",  # 避免 SSL 问题
        ]

        # 检查是否有 cookies 文件 (用于抖音等需要认证的平台)
        cookies_path = os.path.join(os.path.dirname(__file__), "cookies.txt")
        if os.path.exists(cookies_path):
            cmd.extend(["--cookies", cookies_path])

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,  # 抖音可能需要更长时间
        )

        if result.returncode == 0 and result.stdout.strip():
            video = json.loads(result.stdout)
            info = {
                "title": video.get("title", ""),
                "description": video.get("description", "")[:500]
                if video.get("description")
                else "",
                "uploader": video.get("uploader") or video.get("creator", ""),
                "duration": video.get("duration", 0),
                "view_count": video.get("view_count", 0),
                "like_count": video.get("like_count", 0),
                "comment_count": video.get("comment_count", 0),
                "upload_date": video.get("upload_date", ""),
                "thumbnail": video.get("thumbnail", ""),
                "platform": video.get("extractor", "unknown"),
                "url": video.get("webpage_url") or url,
            }
            logger.info("Video info retrieved", title=info["title"], platform=info["platform"])
            return json.dumps(info, ensure_ascii=False, indent=2)

        # 如果失败，返回详细错误
        error_msg = result.stderr.strip() if result.stderr else "未知错误"
        if "Unsupported URL" in error_msg:
            error_msg = "不支持的 URL 格式"
        elif "HTTP Error 403" in error_msg or "Login required" in error_msg:
            error_msg = "需要登录认证。请配置 cookies.txt 文件"

        return json.dumps(
            {
                "error": error_msg,
                "url": url,
                "hint": "抖音/小红书等平台需要配置 cookies.txt 文件才能获取信息",
            },
            ensure_ascii=False,
            indent=2,
        )

    except subprocess.TimeoutExpired:
        return json.dumps({"error": "请求超时"}, ensure_ascii=False)
    except Exception as e:
        logger.error("Video info failed", error=str(e))
        return json.dumps({"error": f"获取失败: {str(e)}"}, ensure_ascii=False)


# ===== 抖音专用工具 (使用 @yc-w-cn/douyin-mcp-server) =====


async def _call_douyin_mcp_async(tool_name: str, share_link: str) -> dict:
    """
    调用 douyin-mcp-server 的工具 (使用 MCP Python SDK)

    通过 stdio 传输调用 NPM 包
    """
    import shutil

    npx_path = shutil.which("npx")
    if not npx_path:
        return {"error": "npx 未安装。请安装 Node.js"}

    try:
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client

        # 配置 MCP Server
        server_params = StdioServerParameters(
            command=npx_path,
            args=["-y", "@yc-w-cn/douyin-mcp-server@latest"],
            env={"WORK_DIR": tempfile.gettempdir()},
        )

        # 连接并调用工具
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # 初始化
                await session.initialize()

                # 调用工具
                result = await session.call_tool(tool_name, arguments={"share_link": share_link})

                # 解析结果
                if result.content:
                    for content in result.content:
                        if hasattr(content, "text"):
                            try:
                                return json.loads(content.text)
                            except json.JSONDecodeError:
                                return {"result": content.text}

                return {"error": "无返回内容"}

    except ImportError:
        return {"error": "MCP SDK 未安装。请运行: pip install mcp"}
    except asyncio.TimeoutError:
        return {"error": "请求超时"}
    except Exception as e:
        logger.warning(f"Douyin MCP call failed: {e}")
        return {"error": str(e)}


def _call_douyin_mcp(tool_name: str, share_link: str) -> dict:
    """同步版本的抖音 MCP 调用"""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # 如果在异步环境中，创建新任务
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, _call_douyin_mcp_async(tool_name, share_link))
                return future.result(timeout=90)
        else:
            return asyncio.run(_call_douyin_mcp_async(tool_name, share_link))
    except Exception as e:
        return {"error": str(e)}


@tool
def douyin_video_info(share_link: str) -> str:
    """
    抖音视频信息解析 (无需 Cookies)

    使用 @yc-w-cn/douyin-mcp-server 解析抖音视频信息。
    支持抖音分享链接（如 https://v.douyin.com/xxx）。

    特点：
    - 无需登录/Cookies
    - 获取无水印视频地址
    - 获取视频标题、作者等信息

    Args:
        share_link: 抖音分享链接

    Returns:
        JSON 格式的视频信息
    """
    logger.info("Parsing Douyin video info", share_link=share_link)

    result = _call_douyin_mcp("parse_douyin_video_info", share_link)

    if "error" in result:
        logger.error("Douyin parse failed", error=result["error"])
    else:
        logger.info("Douyin video info retrieved")

    return json.dumps(result, ensure_ascii=False, indent=2)


@tool
def douyin_download_link(share_link: str) -> str:
    """
    获取抖音无水印下载链接 (无需 Cookies)

    使用 @yc-w-cn/douyin-mcp-server 获取无水印视频下载地址。

    Args:
        share_link: 抖音分享链接

    Returns:
        无水印下载链接或错误信息
    """
    logger.info("Getting Douyin download link", share_link=share_link)

    result = _call_douyin_mcp("get_douyin_download_link", share_link)

    if "error" in result:
        logger.error("Douyin link failed", error=result["error"])
    else:
        logger.info("Douyin download link retrieved")

    return json.dumps(result, ensure_ascii=False, indent=2)


# ===== 3. Browser Tools (Playwright) =====


async def _get_browser():
    """获取 Playwright 浏览器实例"""
    try:
        from playwright.async_api import async_playwright

        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(headless=True)
        return playwright, browser
    except Exception as e:
        logger.error("Failed to launch browser", error=str(e))
        raise


@tool
async def browser_scrape(url: str) -> str:
    """
    网页内容抓取

    使用 Playwright 浏览器抓取网页的文本内容。
    支持 JavaScript 渲染的动态页面。

    Args:
        url: 目标网页 URL

    Returns:
        网页文本内容
    """
    logger.info("Browser scrape started", url=url)

    # 验证 URL
    if not url.startswith(("http://", "https://")):
        return "错误: URL 必须以 http:// 或 https:// 开头"

    playwright = None
    browser = None

    try:
        playwright, browser = await _get_browser()
        page = await browser.new_page()

        await page.goto(url, timeout=30000, wait_until="domcontentloaded")

        # 移除脚本和样式，提取纯文本
        content = await page.evaluate("""
            () => {
                const scripts = document.querySelectorAll('script, style, noscript');
                scripts.forEach(s => s.remove());
                return document.body.innerText;
            }
        """)

        # 限制长度
        content = content.strip()[:8000]

        logger.info("Browser scrape completed", url=url, length=len(content))
        return f"网页内容 ({url}):\n\n{content}"

    except Exception as e:
        logger.error("Browser scrape failed", error=str(e))

        # Fallback 到 httpx
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                headers = {"User-Agent": "Mozilla/5.0"}
                response = await client.get(url, headers=headers, follow_redirects=True)
                if response.status_code == 200:
                    import re

                    text = response.text
                    text = re.sub(r"<script[^>]*>.*?</script>", "", text, flags=re.DOTALL)
                    text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL)
                    text = re.sub(r"<[^>]+>", " ", text)
                    text = re.sub(r"\s+", " ", text).strip()[:5000]
                    return f"[HTTP Fallback] 网页内容:\n{text}"
        except Exception as fallback_error:
            pass

        return f"抓取失败: {str(e)}"

    finally:
        if browser:
            await browser.close()
        if playwright:
            await playwright.stop()


@tool
async def browser_screenshot(url: str, full_page: bool = False) -> str:
    """
    网页截图

    使用 Playwright 浏览器对网页进行截图。

    Args:
        url: 目标网页 URL
        full_page: 是否截取整个页面 (默认只截取可见区域)

    Returns:
        截图文件路径或错误信息
    """
    logger.info("Browser screenshot started", url=url)

    if not url.startswith(("http://", "https://")):
        return "错误: URL 必须以 http:// 或 https:// 开头"

    playwright = None
    browser = None

    try:
        playwright, browser = await _get_browser()
        page = await browser.new_page()
        await page.set_viewport_size({"width": 1280, "height": 720})

        await page.goto(url, timeout=30000, wait_until="networkidle")

        # 保存截图
        screenshot_dir = tempfile.gettempdir()
        screenshot_path = f"{screenshot_dir}/screenshot_{hash(url) % 10000}.png"

        await page.screenshot(path=screenshot_path, full_page=full_page)

        logger.info("Browser screenshot completed", path=screenshot_path)
        return f"截图已保存: {screenshot_path}"

    except Exception as e:
        logger.error("Browser screenshot failed", error=str(e))
        return f"截图失败: {str(e)}"

    finally:
        if browser:
            await browser.close()
        if playwright:
            await playwright.stop()


@tool
async def browser_extract_links(url: str) -> str:
    """
    提取网页链接

    从网页中提取所有链接及其文本。

    Args:
        url: 目标网页 URL

    Returns:
        JSON 格式的链接列表
    """
    logger.info("Extracting links from", url=url)

    playwright = None
    browser = None

    try:
        playwright, browser = await _get_browser()
        page = await browser.new_page()

        await page.goto(url, timeout=30000, wait_until="domcontentloaded")

        links = await page.evaluate("""
            () => {
                const anchors = Array.from(document.querySelectorAll('a[href]'));
                return anchors
                    .map(a => ({
                        text: a.textContent?.trim() || '',
                        href: a.href
                    }))
                    .filter(l => l.href && !l.href.startsWith('javascript:'))
                    .slice(0, 50);
            }
        """)

        logger.info("Links extracted", count=len(links))
        return json.dumps(links, ensure_ascii=False, indent=2)

    except Exception as e:
        logger.error("Link extraction failed", error=str(e))
        return json.dumps({"error": f"提取失败: {str(e)}"}, ensure_ascii=False)

    finally:
        if browser:
            await browser.close()
        if playwright:
            await playwright.stop()


# ===== 4. Utility Tools =====


@tool
def check_tools_status() -> str:
    """
    检查工具可用性

    诊断各工具是否正常可用。

    Returns:
        工具状态报告
    """
    results = []

    # Check DuckDuckGo
    try:
        search = DuckDuckGoSearchRun()
        search.invoke("test")
        results.append("✅ DuckDuckGo 搜索: 可用")
    except Exception as e:
        results.append(f"❌ DuckDuckGo 搜索: {e}")

    # Check yt-dlp
    try:
        result = subprocess.run(
            [sys.executable, "-m", "yt_dlp", "--version"], capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            results.append(f"✅ yt-dlp 视频工具: v{result.stdout.strip()}")
        else:
            results.append("❌ yt-dlp: 运行错误")
    except Exception as e:
        results.append(f"❌ yt-dlp: {e}")

    # Check Playwright
    try:
        from playwright.async_api import async_playwright

        results.append("✅ Playwright 浏览器: 已安装")
    except ImportError:
        results.append("❌ Playwright: 未安装 (pip install playwright)")

    # Check npx (for douyin-mcp-server)
    import shutil

    npx_path = shutil.which("npx")
    if npx_path:
        results.append("✅ 抖音工具 (npx): 可用 @yc-w-cn/douyin-mcp-server")
    else:
        results.append("❌ 抖音工具: 需要安装 Node.js/npx")

    return "\n".join(results)


# ===== Export =====

__all__ = [
    # 搜索工具
    "duckduckgo_search",
    # 视频工具 (通用)
    "video_search",
    "video_info",
    # 抖音专用工具 (使用 @yc-w-cn/douyin-mcp-server)
    "douyin_video_info",
    "douyin_download_link",
    # 浏览器工具
    "browser_scrape",
    "browser_screenshot",
    "browser_extract_links",
    # 诊断工具
    "check_tools_status",
    # MetaSo
    "metaso_search",
]
