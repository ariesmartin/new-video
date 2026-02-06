import asyncio
import aiohttp
import json
import os
from datetime import datetime
from pathlib import Path
import structlog
from langchain_core.tools import tool

logger = structlog.get_logger(__name__)

METASO_API_KEY = "mk-1A501C0CB1D1A440B8BB85719299CF78"
METASO_API_URL = "https://metaso.cn/api/open/search"
CACHE_FILE = Path(__file__).parent.parent / "data" / "search_cache.json"

def _load_cache():
    if CACHE_FILE.exists():
        try:
            return json.loads(CACHE_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}

def _save_cache(cache_data):
    try:
        # 自动清理：只保留今天的数据
        today = datetime.now().strftime("%Y-%m-%d")
        cleaned_cache = {k: v for k, v in cache_data.items() if k.startswith(today)}
        
        CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        CACHE_FILE.write_text(json.dumps(cleaned_cache, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as e:
        logger.warning("Failed to save search cache", error=str(e))

def get_cached_search(query: str) -> str | None:
    """尝试获取对应 query 的今日缓存"""
    today = datetime.now().strftime("%Y-%m-%d")
    cache_key = f"{today}:{query}"
    cache = _load_cache()
    return cache.get(cache_key)

@tool
async def metaso_search(query: str) -> str:
    """
    使用 MetaSo 进行深度网络搜索（含每日缓存）。
    
    Args:
        query: 搜索关键词
        
    Returns:
        搜索结果摘要
    """
    today = datetime.now().strftime("%Y-%m-%d")
    cache_key = f"{today}:{query}"
    
    # Check Cache
    cache_data = _load_cache()
    if cache_key in cache_data:
        logger.info("MetaSo search cache hit", query=query, date=today)
        return cache_data[cache_key]

    logger.info("MetaSo search started (No cache)", query=query)
    
    headers = {
        "Authorization": f"Bearer {METASO_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "question": query,
        "stream": False,
        "model": "concise"
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(METASO_API_URL, json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status == 200:
                    data = await response.json()
                    inner_data = data.get("data", {})
                    
                    # 解析优先级: text (AI摘要) > content > references
                    result = ""
                    source_type = ""
                    
                    # 1. 优先使用 text 字段 (AI 生成的高质量摘要)
                    if isinstance(inner_data, dict) and inner_data.get("text"):
                        result = inner_data["text"]
                        source_type = "AI摘要"
                        logger.info("MetaSo: using 'text' field (AI summary)", length=len(result))
                    
                    # 2. 次选 content 字段
                    elif isinstance(inner_data, dict) and inner_data.get("content"):
                        result = inner_data["content"]
                        source_type = "内容摘要"
                        logger.info("MetaSo: using 'content' field", length=len(result))
                    
                    # 3. 如果以上都没有，使用 references 生成摘要
                    elif isinstance(inner_data, dict) and inner_data.get("references"):
                        references = inner_data["references"]
                        formatted_refs = []
                        for i, ref in enumerate(references[:10], 1):
                            title = ref.get("title", "未知标题")
                            date = ref.get("date", "")
                            article_type = ref.get("article_type", "")
                            link = ref.get("link", "")
                            
                            ref_text = f"{i}. 【{title}】"
                            if date:
                                ref_text += f" ({date})"
                            if article_type:
                                ref_text += f" - {article_type}"
                            if link:
                                ref_text += f"\n   来源: {link}"
                            formatted_refs.append(ref_text)
                        
                        result = "\n\n".join(formatted_refs)
                        source_type = f"引用列表({len(references)}条)"
                        logger.info("MetaSo: using 'references' field", count=len(references))
                    
                    # 4. 如果 data 本身是字符串
                    elif isinstance(inner_data, str) and inner_data:
                        result = inner_data
                        source_type = "原始数据"

                    if not result:
                        available_keys = list(inner_data.keys()) if isinstance(inner_data, dict) else "N/A"
                        logger.warning("MetaSo response empty", available_keys=available_keys)
                        return f"搜索完成，但未找到相关结果。可用字段: {available_keys}"

                    # 记录 API 余额
                    balance = inner_data.get("balance") if isinstance(inner_data, dict) else None
                    if balance is not None:
                        logger.info("MetaSo API balance", remaining=balance)

                    # Save to Cache
                    formatted_result = f"【MetaSo 搜索结果 (日期: {today}, 类型: {source_type})】\n\n{result}"
                    cache_data[cache_key] = formatted_result
                    _save_cache(cache_data)
                    
                    logger.info("MetaSo search completed", source_type=source_type, length=len(result))
                    return formatted_result
                else:
                    error_text = await response.text()
                    logger.error("MetaSo search failed", status=response.status, error=error_text)
                    return f"MetaSo Error: {response.status} - {error_text}"
                    
    except asyncio.TimeoutError:
        logger.error("MetaSo search timeout", query=query)
        return f"搜索请求超时（30秒），请稍后重试。"
    except Exception as e:
        logger.error("MetaSo search exception", error=str(e), type=type(e).__name__)
        return f"搜索服务异常 ({type(e).__name__})，请稍后重试。"

