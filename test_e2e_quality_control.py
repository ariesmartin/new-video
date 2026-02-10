#!/usr/bin/env python3
"""
端到端测试：质量控制系统完整流程验证
测试内容：
1. 创建测试项目
2. 生成大纲（自动触发全局审阅）
3. 验证全局审阅结果
4. 测试章节审阅
5. 验证张力曲线
6. 验证数据库数据
"""

import asyncio
import json
import httpx
from datetime import datetime

BASE_URL = "http://localhost:8000"
TEST_PROJECT_ID = None


async def test_health():
    """测试服务健康状态"""
    print("\n" + "=" * 60)
    print("🩺 步骤 1: 健康检查")
    print("=" * 60)
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{BASE_URL}/health")
        data = resp.json()
        print(f"✅ 服务状态: {data['status']}")
        print(f"✅ API 版本: {data['version']}")
        return True


async def test_create_project():
    """创建测试项目"""
    global TEST_PROJECT_ID
    print("\n" + "=" * 60)
    print("📁 步骤 2: 创建测试项目")
    print("=" * 60)

    async with httpx.AsyncClient() as client:
        # 先检查是否有现有项目
        resp = await client.get(f"{BASE_URL}/api/projects")
        projects = resp.json()

        if projects and len(projects) > 0:
            TEST_PROJECT_ID = projects[0]["id"]
            print(f"✅ 使用现有项目: {TEST_PROJECT_ID}")
            print(f"   项目名称: {projects[0].get('name', 'N/A')}")
        else:
            # 创建新项目
            resp = await client.post(
                f"{BASE_URL}/api/projects",
                json={
                    "name": f"测试项目_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    "description": "质量控制系统端到端测试项目",
                },
            )
            project = resp.json()
            TEST_PROJECT_ID = project["id"]
            print(f"✅ 创建新项目: {TEST_PROJECT_ID}")
            print(f"   项目名称: {project['name']}")

        return TEST_PROJECT_ID


async def test_generate_outline():
    """测试大纲生成（自动触发全局审阅）"""
    print("\n" + "=" * 60)
    print("📝 步骤 3: 生成大纲（自动触发全局审阅）")
    print("=" * 60)

    async with httpx.AsyncClient(timeout=120.0) as client:
        # 创建大纲数据
        outline_data = {
            "title": "重生之我在异世界开餐馆",
            "logline": "顶级厨师意外穿越到魔法世界，用美食征服异世界，却卷入王国权力斗争",
            "episodes": [
                {
                    "id": "ep_001",
                    "title": "第1集：穿越与第一道菜",
                    "content": "主角李明在车祸中穿越到异世界，醒来发现自己在一个破旧的小餐馆里。他决定用现代烹饪技术做出第一道菜——红烧肉。这道菜香气四溢，吸引了路过的冒险者。",
                    "characters": ["李明", "冒险者队长"],
                    "scenes": ["破旧餐馆", "厨房"],
                    "key_points": ["穿越", "展示厨艺", "遇到第一个顾客"],
                },
                {
                    "id": "ep_002",
                    "title": "第2集：冒险者的订单",
                    "content": "冒险者队长被红烧肉征服，决定带全队来吃饭。李明面临食材不足的困境，必须想办法解决。",
                    "characters": ["李明", "冒险者队长", "女法师"],
                    "scenes": ["餐馆", "市场"],
                    "key_points": ["获得稳定客源", "食材危机", "解决问题"],
                },
                {
                    "id": "ep_003",
                    "title": "第3集：贵族的试探",
                    "content": "当地贵族听说这家餐馆的美味，派管家前来试探。李明必须应对贵族的挑剔口味。",
                    "characters": ["李明", "贵族管家", "神秘女子"],
                    "scenes": ["餐馆", "贵族庄园"],
                    "key_points": ["贵族关注", "政治阴谋初现", "神秘人物登场"],
                },
                {
                    "id": "ep_004",
                    "title": "第4集：魔法食材的秘密",
                    "content": "李明发现这个世界的食材含有魔法元素，可以做出具有特殊效果的料理。他开始研究如何将魔法融入烹饪。",
                    "characters": ["李明", "女法师", "魔法商人"],
                    "scenes": ["魔法市场", "实验室"],
                    "key_points": ["发现魔法食材", "研究新菜式", "能力升级"],
                },
                {
                    "id": "ep_005",
                    "title": "第5集：厨神大赛的邀请",
                    "content": "王国举办厨神大赛，李明的餐馆收到邀请。他必须在大赛中证明自己的实力，但竞争对手暗中使绊子。",
                    "characters": ["李明", "竞争对手", "评委"],
                    "scenes": ["大赛场地", "后台"],
                    "key_points": ["厨神大赛", "公平竞争", "实力展现"],
                },
            ],
        }

        print(f"⏳ 正在生成大纲并触发审阅...")
        print(f"   项目ID: {TEST_PROJECT_ID}")
        print(f"   集数: {len(outline_data['episodes'])}")

        try:
            resp = await client.post(
                f"{BASE_URL}/api/skeleton/outline?project_id={TEST_PROJECT_ID}",
                json=outline_data,
            )

            if resp.status_code == 200:
                result = resp.json()
                print(f"✅ 大纲生成成功")
                print(f"   大纲ID: {result.get('outline_id', 'N/A')}")
                print(f"   审阅状态: {result.get('review_status', 'N/A')}")
                return True
            else:
                print(f"❌ 大纲生成失败: {resp.status_code}")
                print(f"   错误: {resp.text[:500]}")
                return False
        except Exception as e:
            print(f"❌ 请求异常: {e}")
            return False


async def test_global_review():
    """测试全局审阅结果"""
    print("\n" + "=" * 60)
    print("🌍 步骤 4: 验证全局审阅结果")
    print("=" * 60)

    async with httpx.AsyncClient(timeout=60.0) as client:
        # 等待一下让审阅完成
        print("⏳ 等待审阅完成...")
        await asyncio.sleep(3)

        resp = await client.get(f"{BASE_URL}/api/review/{TEST_PROJECT_ID}/global")

        if resp.status_code == 404:
            print("⚠️ 审阅结果尚未生成，稍后重试...")
            await asyncio.sleep(5)
            resp = await client.get(f"{BASE_URL}/api/review/{TEST_PROJECT_ID}/global")

        if resp.status_code == 200:
            review = resp.json()
            print(f"✅ 全局审阅结果获取成功")
            print(f"\n📊 评分概览:")
            print(f"   综合评分: {review.get('overallScore', 'N/A')}/100")

            # 分类评分
            categories = review.get("categories", {})
            if categories:
                print(f"\n📋 分类评分:")
                for cat_name, cat_data in categories.items():
                    score = cat_data.get("score", "N/A")
                    weight = cat_data.get("weight", "N/A")
                    print(f"   • {cat_name}: {score}/100 (权重: {weight})")

            # 张力曲线
            tension_curve = review.get("tensionCurve", [])
            print(f"\n📈 张力曲线:")
            print(f"   点数: {len(tension_curve)}")
            if tension_curve:
                print(f"   范围: {min(tension_curve):.2f} - {max(tension_curve):.2f}")
                print(f"   平均值: {sum(tension_curve) / len(tension_curve):.2f}")

            # 章节审阅
            chapter_reviews = review.get("chapterReviews", {})
            print(f"\n📖 章节审阅 ({len(chapter_reviews)} 章):")
            for chap_id, chap_data in chapter_reviews.items():
                score = chap_data.get("score", "N/A")
                status = chap_data.get("status", "N/A")
                print(f"   • {chap_id}: {score}/100 [{status}]")

            # 总结和建议
            summary = review.get("summary", "")
            if summary:
                print(f"\n📝 审阅总结:")
                print(f"   {summary[:200]}...")

            recommendations = review.get("recommendations", [])
            if recommendations:
                print(f"\n💡 改进建议 ({len(recommendations)} 条):")
                for i, rec in enumerate(recommendations[:3], 1):
                    print(f"   {i}. {rec[:100]}...")

            return True
        else:
            print(f"❌ 获取审阅失败: {resp.status_code}")
            print(f"   错误: {resp.text[:500]}")
            return False


async def test_chapter_review():
    """测试单个章节审阅"""
    print("\n" + "=" * 60)
    print("📄 步骤 5: 测试单个章节审阅")
    print("=" * 60)

    async with httpx.AsyncClient(timeout=60.0) as client:
        chapter_id = "ep_001"

        resp = await client.get(
            f"{BASE_URL}/api/review/{TEST_PROJECT_ID}/chapters/{chapter_id}"
        )

        if resp.status_code == 200:
            review = resp.json()
            print(f"✅ 章节审阅获取成功: {chapter_id}")
            print(f"   评分: {review.get('score', 'N/A')}/100")
            print(f"   状态: {review.get('status', 'N/A')}")

            comment = review.get("comment", "")
            if comment:
                print(f"\n   评语: {comment[:200]}...")

            issues = review.get("issues", [])
            if issues:
                print(f"\n   问题数: {len(issues)}")
                for i, issue in enumerate(issues[:3], 1):
                    print(
                        f"   {i}. [{issue.get('severity', 'N/A')}] {issue.get('description', '')[:80]}..."
                    )

            return True
        else:
            print(f"⚠️ 章节审阅未找到: {resp.status_code}")
            return False


async def test_tension_curve():
    """测试张力曲线端点"""
    print("\n" + "=" * 60)
    print("📊 步骤 6: 验证张力曲线端点")
    print("=" * 60)

    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{BASE_URL}/api/review/{TEST_PROJECT_ID}/tension_curve"
        )

        if resp.status_code == 200:
            data = resp.json()
            curve = data.get("tension_curve", [])

            print(f"✅ 张力曲线获取成功")
            print(f"   数据点数: {len(curve)}")

            if curve:
                print(f"   数值范围: {min(curve):.2f} - {max(curve):.2f}")
                print(f"   开头: {curve[0]:.2f}")
                print(f"   结尾: {curve[-1]:.2f}")

                # 验证点数是否基于集数
                # 通常张力曲线点数 = 集数 * 因子
                print(f"\n   📐 动态计算验证:")
                print(f"      集数: 5")
                print(f"      点数: {len(curve)}")
                print(f"      比例: {len(curve) / 5:.1f}x")

            return True
        else:
            print(f"⚠️ 张力曲线获取失败: {resp.status_code}")
            return False


async def test_review_status():
    """测试审阅状态端点"""
    print("\n" + "=" * 60)
    print("📈 步骤 7: 验证审阅状态")
    print("=" * 60)

    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{BASE_URL}/api/review/{TEST_PROJECT_ID}/status")

        if resp.status_code == 200:
            status = resp.json()
            print(f"✅ 审阅状态获取成功")
            print(f"\n   全局审阅:")
            print(f"      状态: {status.get('global_review', {}).get('status', 'N/A')}")
            print(f"      评分: {status.get('global_review', {}).get('score', 'N/A')}")

            chapters = status.get("chapters", {})
            print(f"\n   章节审阅 ({len(chapters)} 章):")
            for chap_id, chap_status in chapters.items():
                s = chap_status.get("status", "N/A")
                score = chap_status.get("score", "N/A")
                print(f"      • {chap_id}: {score}/100 [{s}]")

            return True
        else:
            print(f"⚠️ 审阅状态获取失败: {resp.status_code}")
            return False


async def test_re_review():
    """测试重新审阅功能"""
    print("\n" + "=" * 60)
    print("🔄 步骤 8: 测试重新审阅")
    print("=" * 60)

    async with httpx.AsyncClient(timeout=120.0) as client:
        print("⏳ 触发重新审阅...")

        resp = await client.post(f"{BASE_URL}/api/review/{TEST_PROJECT_ID}/re_review")

        if resp.status_code == 200:
            result = resp.json()
            print(f"✅ 重新审阅成功")
            print(f"   消息: {result.get('message', 'N/A')}")

            review = result.get("review", {})
            if review:
                print(f"   新评分: {review.get('overallScore', 'N/A')}/100")

            return True
        else:
            print(f"⚠️ 重新审阅失败: {resp.status_code}")
            print(f"   错误: {resp.text[:500]}")
            return False


async def test_database_integration():
    """验证数据库集成"""
    print("\n" + "=" * 60)
    print("🗄️ 步骤 9: 验证数据库集成")
    print("=" * 60)

    # 检查大纲是否保存到数据库
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{BASE_URL}/api/skeleton/outline/{TEST_PROJECT_ID}")

        if resp.status_code == 200:
            outline = resp.json()
            print(f"✅ 大纲从数据库获取成功")
            print(f"   标题: {outline.get('title', 'N/A')}")
            print(f"   集数: {len(outline.get('episodes', []))}")
            return True
        else:
            print(f"⚠️ 大纲获取失败: {resp.status_code}")
            return False


async def run_all_tests():
    """运行所有测试"""
    print("\n" + "🧪" * 30)
    print("   质量控制系统 - 端到端测试")
    print("🧪" * 30)

    results = []

    # 1. 健康检查
    results.append(("健康检查", await test_health()))

    # 2. 创建项目
    results.append(("创建项目", await test_create_project()))

    if not TEST_PROJECT_ID:
        print("\n❌ 无法获取项目ID，终止测试")
        return results

    # 3. 生成大纲（自动触发审阅）
    results.append(("生成大纲", await test_generate_outline()))

    # 4. 验证全局审阅
    results.append(("全局审阅", await test_global_review()))

    # 5. 章节审阅
    results.append(("章节审阅", await test_chapter_review()))

    # 6. 张力曲线
    results.append(("张力曲线", await test_tension_curve()))

    # 7. 审阅状态
    results.append(("审阅状态", await test_review_status()))

    # 8. 重新审阅
    results.append(("重新审阅", await test_re_review()))

    # 9. 数据库集成
    results.append(("数据库集成", await test_database_integration()))

    return results


async def main():
    """主函数"""
    try:
        results = await run_all_tests()

        # 打印测试报告
        print("\n" + "=" * 60)
        print("📊 测试报告")
        print("=" * 60)

        passed = sum(1 for _, result in results if result)
        failed = sum(1 for _, result in results if not result)

        for name, result in results:
            status = "✅ 通过" if result else "❌ 失败"
            print(f"   {status}: {name}")

        print(f"\n总计: {len(results)} 项")
        print(f"   ✅ 通过: {passed}")
        print(f"   ❌ 失败: {failed}")

        if failed == 0:
            print("\n🎉 所有测试通过！质量控制系统工作正常。")
        else:
            print(f"\n⚠️ {failed} 项测试失败，请检查日志。")

        # 保存详细报告
        report = {
            "timestamp": datetime.now().isoformat(),
            "project_id": TEST_PROJECT_ID,
            "results": {name: result for name, result in results},
            "summary": {"total": len(results), "passed": passed, "failed": failed},
        }

        with open("/tmp/e2e_test_report.json", "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        print(f"\n📄 详细报告已保存: /tmp/e2e_test_report.json")

    except Exception as e:
        print(f"\n❌ 测试执行异常: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
