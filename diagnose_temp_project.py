#!/usr/bin/env python3
"""
诊断脚本：测试临时项目创建 API
"""

import asyncio
import json

import aiohttp


async def test_temp_project_creation():
    """测试临时项目创建"""
    base_url = "http://localhost:8000"

    print("=" * 70)
    print("临时项目创建 API 诊断")
    print("=" * 70)
    print()

    # 测试 1: 健康检查
    print("🧪 测试 1: 后端健康检查")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{base_url}/api/health") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    print(f"✅ 后端健康: {data.get('status', 'unknown')}")
                else:
                    print(f"❌ 健康检查失败: HTTP {resp.status}")
                    return
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        print(
            "   请确保后端服务已启动: cd backend && python -m uvicorn main:app --reload"
        )
        return

    print()

    # 测试 2: 创建临时项目
    print("🧪 测试 2: 创建临时项目")
    print("-" * 70)

    try:
        async with aiohttp.ClientSession() as session:
            # 注意：这个端点需要认证，我们测试看看返回什么错误
            async with session.post(
                f"{base_url}/api/projects/temp",
                headers={"Content-Type": "application/json"},
            ) as resp:
                print(f"状态码: {resp.status}")

                if resp.status == 401:
                    print("⚠️  需要认证（这是正常的）")
                    print("   前端应该提供 user_id 或 token")
                elif resp.status == 500:
                    text = await resp.text()
                    print(f"❌ 服务器内部错误")
                    print(f"   响应: {text[:500]}")
                elif resp.status == 201 or resp.status == 200:
                    data = await resp.json()
                    print(f"✅ 临时项目创建成功")
                    print(f"   项目ID: {data.get('data', {}).get('id')}")
                else:
                    text = await resp.text()
                    print(f"⚠️  意外状态码: {resp.status}")
                    print(f"   响应: {text[:500]}")

    except Exception as e:
        print(f"❌ 请求失败: {e}")
        import traceback

        traceback.print_exc()

    print()
    print("=" * 70)
    print("诊断建议:")
    print("=" * 70)
    print()
    print("如果看到 500 错误，请检查:")
    print("  1. 后端日志: tail -f backend/server.log")
    print("  2. 数据库连接是否正常")
    print("  3. Supabase/PostgreSQL 是否可访问")
    print()
    print("如果看到 401 错误，这是正常的，说明端点存在但需要认证")


if __name__ == "__main__":
    asyncio.run(test_temp_project_creation())
