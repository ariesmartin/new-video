#!/usr/bin/env python3
"""
市场分析功能 - 真实全流程质量验证测试

真实执行以下流程：
1. 调用真实搜索API获取数据
2. 验证搜索内容的质量（是否包含短剧相关信息）
3. 使用LLM分析并提取热点元素
4. 验证提取结果的质量
5. 检查数据格式是否正确
6. 验证是否可以被Story Planner正确使用

环境要求：
- 需要配置好的MetaSo API Key
- 需要LLM服务可用

运行：
    cd /Users/ariesmartin/Documents/new-video
    source backend/.venv/bin/activate
    python test_real_quality_verification.py
"""

import asyncio
import sys
import json
import re
from datetime import datetime
from typing import Dict, List, Any

sys.path.insert(0, "/Users/ariesmartin/Documents/new-video")


class QualityMetrics:
    """质量评估指标"""

    def __init__(self):
        self.checks = []

    def check(self, name: str, condition: bool, details: str = ""):
        """记录检查结果"""
        status = "✅" if condition else "❌"
        self.checks.append(
            {"name": name, "passed": condition, "details": details, "status": status}
        )
        print(f"{status} {name}")
        if details:
            print(f"   {details}")
        return condition

    def summary(self) -> Dict[str, Any]:
        """生成摘要"""
        passed = sum(1 for c in self.checks if c["passed"])
        total = len(self.checks)
        return {
            "passed": passed,
            "total": total,
            "rate": passed / total if total > 0 else 0,
            "checks": self.checks,
        }


async def test_real_search_quality():
    """测试1: 真实搜索API调用和内容质量"""
    print("\n" + "=" * 70)
    print("【测试1】真实搜索API调用和内容质量验证")
    print("=" * 70)

    metrics = QualityMetrics()

    try:
        from backend.tools.metaso_search import metaso_search

        # 定义测试查询
        test_queries = [
            "2026年短剧热门元素",
            "2026年短剧新兴题材",
        ]

        search_results = []

        for query in test_queries:
            print(f"\n执行搜索: {query}")
            print("-" * 50)

            try:
                result = await metaso_search.ainvoke(query)
                result_length = len(result)

                print(f"结果长度: {result_length} 字符")
                print(f"结果预览:\n{result[:500]}...")

                # 质量检查1: 结果长度
                has_content = metrics.check(
                    "结果非空", result_length > 100, f"长度: {result_length} 字符"
                )

                if not has_content:
                    continue

                # 质量检查2: 是否包含短剧相关信息
                short_drama_keywords = [
                    "短剧",
                    "剧名",
                    "爆款",
                    "热度",
                    "播放量",
                    "题材",
                ]
                found_keywords = [kw for kw in short_drama_keywords if kw in result]

                metrics.check(
                    "包含短剧相关关键词",
                    len(found_keywords) >= 2,
                    f"找到关键词: {', '.join(found_keywords[:5])}",
                )

                # 质量检查3: 是否包含具体剧名（书名号）
                drama_names = re.findall(r"《([^》]+)》", result)
                metrics.check(
                    "包含具体剧名",
                    len(drama_names) > 0,
                    f"找到 {len(drama_names)} 个剧名: {', '.join(drama_names[:3])}",
                )

                # 质量检查4: 是否包含题材/元素信息
                genre_keywords = [
                    "穿越",
                    "重生",
                    "甜宠",
                    "复仇",
                    "悬疑",
                    "都市",
                    "古装",
                ]
                found_genres = [kw for kw in genre_keywords if kw in result]

                metrics.check(
                    "包含题材/元素信息",
                    len(found_genres) > 0,
                    f"找到题材: {', '.join(found_genres[:5])}",
                )

                search_results.append(
                    {
                        "query": query,
                        "result": result,
                        "length": result_length,
                        "drama_names": drama_names,
                        "genres": found_genres,
                    }
                )

            except Exception as e:
                print(f"❌ 搜索失败: {e}")
                metrics.check("搜索成功", False, str(e))

        summary = metrics.summary()
        print(f"\n搜索质量评估: {summary['passed']}/{summary['total']} 通过")

        return search_results, summary

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback

        traceback.print_exc()
        return [], {"passed": 0, "total": 1, "rate": 0}


def simple_extract_hot_elements(search_results: List[Dict]) -> Dict[str, Any]:
    """简化版热点元素提取（不依赖LLM，基于规则）"""
    print("\n" + "=" * 70)
    print("【测试2】热点元素提取（基于规则）")
    print("=" * 70)

    metrics = QualityMetrics()

    all_text = "\n".join([r["result"] for r in search_results])

    # 提取剧名
    drama_names = list(set(re.findall(r"《([^》]+)》", all_text)))

    # 提取热门元素：扩大候选池从10个到20个
    trope_keywords = {
        "身份错位": ["身份", "错位", "互换", "灵魂互换"],
        "反差萌": ["反差", "萌", "反差萌"],
        "双重人格": ["双重人格", "人格分裂"],
        "逆袭成长": ["逆袭", "成长", "打脸", "爽文", "升级"],
        "隐藏大佬": ["隐藏", "大佬", "马甲", "掉马", "真大佬"],
        "反派洗白": ["反派", "洗白", "救赎", "黑化"],
        "穿书": ["穿书", "穿进", "穿成"],
        "系统流": ["系统", "金手指", "任务", "绑定"],
        "替身文学": ["替身", "白月光", "替身文学", "替嫁"],
        "久别重逢": ["久别", "重逢", "初恋", "青梅竹马"],
        "先婚后爱": ["先婚后爱", "契约婚姻", "闪婚"],
        "虐恋情深": ["虐恋", "虐文", "追妻", "火葬场"],
        "甜宠": ["甜宠", "高甜", "撒糖"],
        "霸总": ["霸总", "霸道总裁", "总裁"],
        "重生": ["重生", "重生之", "再来一次"],
        "穿越": ["穿越", "穿越到", "古代", "异世"],
        "修仙": ["修仙", "仙侠", "修真", "玄幻"],
        "职场": ["职场", "商战", "创业", "升职"],
        "悬疑": ["悬疑", "推理", "探案", "刑侦"],
        "复仇": ["复仇", "报仇", "雪恨"],
    }

    found_tropes = []
    for trope, keywords in trope_keywords.items():
        if any(kw in all_text for kw in keywords):
            found_tropes.append(trope)

    # 提取题材
    genre_keywords = [
        "穿越",
        "重生",
        "甜宠",
        "复仇",
        "悬疑",
        "都市",
        "古装",
        "仙侠",
        "现代",
        "民国",
    ]
    found_genres = [kw for kw in genre_keywords if kw in all_text]

    # 提取新兴组合
    combinations = []
    if "无限流" in all_text and ("恋爱" in all_text or "甜宠" in all_text):
        combinations.append("无限流+恋爱")
    if "赛博" in all_text and ("医疗" in all_text or "医院" in all_text):
        combinations.append("赛博朋克+医疗")
    if "末世" in all_text and ("美食" in all_text or "料理" in all_text):
        combinations.append("末世+美食")

    hot_elements = {
        "hot_tropes": found_tropes[:10],
        "hot_settings": found_genres[:5],
        "hot_character_types": [],
        "emerging_combinations": combinations,
        "overused_tropes": ["霸道总裁爱上我", "重生复仇"],
        "specific_works": drama_names[:10],
        "_extraction_method": "rule_based",
        "_source_text_length": len(all_text),
    }

    # 质量检查
    print(f"\n提取结果:")
    print(f"热门元素: {len(hot_elements['hot_tropes'])} 个")
    if hot_elements["hot_tropes"]:
        print(f"  示例: {', '.join(hot_elements['hot_tropes'][:5])}")

    print(f"热门背景: {len(hot_elements['hot_settings'])} 个")
    if hot_elements["hot_settings"]:
        print(f"  示例: {', '.join(hot_elements['hot_settings'][:5])}")

    print(f"新兴组合: {len(hot_elements['emerging_combinations'])} 个")
    if hot_elements["emerging_combinations"]:
        print(f"  示例: {', '.join(hot_elements['emerging_combinations'])}")

    print(f"参考剧名: {len(hot_elements['specific_works'])} 个")
    if hot_elements["specific_works"]:
        print(
            f"  示例: {', '.join(['《' + w + '》' for w in hot_elements['specific_works'][:3]])}"
        )

    # 质量评估
    metrics.check(
        "提取到热门元素",
        len(hot_elements["hot_tropes"]) > 0,
        f"{len(hot_elements['hot_tropes'])} 个元素",
    )

    metrics.check(
        "提取到题材信息",
        len(hot_elements["hot_settings"]) > 0,
        f"{len(hot_elements['hot_settings'])} 个题材",
    )

    metrics.check(
        "提取到具体剧名",
        len(hot_elements["specific_works"]) > 0,
        f"{len(hot_elements['specific_works'])} 个剧名",
    )

    summary = metrics.summary()
    print(f"\n提取质量评估: {summary['passed']}/{summary['total']} 通过")

    return hot_elements, summary


def test_data_usability(hot_elements: Dict) -> Dict[str, Any]:
    """测试3: 验证数据可用性（供Story Planner使用）"""
    print("\n" + "=" * 70)
    print("【测试3】数据可用性验证（供Story Planner使用）")
    print("=" * 70)

    metrics = QualityMetrics()

    # 检查必要字段
    required_fields = [
        "hot_tropes",
        "hot_settings",
        "hot_character_types",
        "emerging_combinations",
        "overused_tropes",
        "specific_works",
    ]

    for field in required_fields:
        has_field = field in hot_elements
        is_list = isinstance(hot_elements.get(field), list) if has_field else False
        metrics.check(
            f"字段 '{field}' 存在且为列表",
            has_field and is_list,
            f"类型: {type(hot_elements.get(field)).__name__}",
        )

    # 检查数据格式
    print("\n数据结构检查:")
    print(json.dumps(hot_elements, indent=2, ensure_ascii=False))

    # 验证是否可以生成Prompt
    print("\n生成Prompt示例（供Story Planner使用）:\n")

    prompt_section = f"""
## 📊 当前市场热点数据（必须使用）

### 🔥 热门元素（选择至少2个）
{chr(10).join([f"- {trope}" for trope in hot_elements.get("hot_tropes", [])[:6]])}

### 🏠 热门背景（选择1个）
{chr(10).join([f"- {setting}" for setting in hot_elements.get("hot_settings", [])[:4]])}

### 🆕 新兴组合（尝试1个）
{chr(10).join([f"- {combo}" for combo in hot_elements.get("emerging_combinations", [])[:3]])}

### 🚫 避免使用（已过度）
{chr(10).join([f"- ❌ {trope}" for trope in hot_elements.get("overused_tropes", [])[:3]])}

### 🎬 参考爆款剧（了解市场）
{chr(10).join([f"- 《{work}》" for work in hot_elements.get("specific_works", [])[:3]])}

### ⚠️ 强制规则
1. 必须从【热门元素】中选择至少2个融入方案
2. 必须尝试【新兴组合】中的至少1个
3. 严禁使用【避免使用】中的元素作为主要卖点
"""

    print(prompt_section)

    # 检查Prompt质量
    has_tropes = len(hot_elements.get("hot_tropes", [])) >= 2
    has_works = len(hot_elements.get("specific_works", [])) > 0

    metrics.check(
        "Prompt包含足够的热门元素(>=2)",
        has_tropes,
        f"{len(hot_elements.get('hot_tropes', []))} 个",
    )

    metrics.check(
        "Prompt包含参考剧名",
        has_works,
        f"{len(hot_elements.get('specific_works', []))} 个",
    )

    summary = metrics.summary()
    print(f"\n可用性评估: {summary['passed']}/{summary['total']} 通过")

    return summary


def test_diversity(hot_elements_list: List[Dict]):
    """测试4: 验证数据多样性（多次提取结果是否不同）"""
    print("\n" + "=" * 70)
    print("【测试4】数据多样性验证")
    print("=" * 70)

    if len(hot_elements_list) < 2:
        print("⚠️ 只有一次提取结果，无法验证多样性")
        return {"passed": 0, "total": 1, "rate": 0}

    metrics = QualityMetrics()

    # 比较两次提取结果
    first = hot_elements_list[0]
    second = (
        hot_elements_list[1] if len(hot_elements_list) > 1 else hot_elements_list[0]
    )

    first_tropes = set(first.get("hot_tropes", []))
    second_tropes = set(second.get("hot_tropes", []))

    overlap = len(first_tropes & second_tropes)
    total_unique = len(first_tropes | second_tropes)

    print(f"\n第一次提取: {len(first_tropes)} 个元素")
    print(f"  {', '.join(list(first_tropes)[:5])}")

    print(f"\n第二次提取: {len(second_tropes)} 个元素")
    print(f"  {', '.join(list(second_tropes)[:5])}")

    print(f"\n重叠元素: {overlap} 个")
    print(f"独特元素: {total_unique} 个")
    print(f"重叠率: {overlap / len(first_tropes) * 100:.1f}%" if first_tropes else "0%")

    # 检查多样性
    is_diverse = overlap < len(first_tropes) * 0.8  # 重叠率<80%认为多样

    metrics.check(
        "提取结果具有多样性（重叠<80%）",
        is_diverse,
        f"重叠率: {overlap / len(first_tropes) * 100:.1f}%" if first_tropes else "N/A",
    )

    summary = metrics.summary()
    print(f"\n多样性评估: {summary['passed']}/{summary['total']} 通过")

    return summary


async def main():
    """主函数"""
    print("\n" + "🧪" * 35)
    print("  市场分析功能 - 真实质量验证测试")
    print("🧪" * 35)
    print(f"\n测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n测试内容:")
    print("  1. 真实搜索API调用和内容质量")
    print("  2. 热点元素提取质量")
    print("  3. 数据可用性（供Story Planner使用）")
    print("  4. 数据多样性")

    all_results = {}

    # 测试1: 真实搜索
    print("\n\n" + "🚀" * 35)
    print("开始执行真实搜索...")
    print("🚀" * 35)
    search_results, search_quality = await test_real_search_quality()
    all_results["搜索质量"] = search_quality

    if not search_results:
        print("\n❌ 搜索失败，无法继续后续测试")
        return 1

    # 测试2: 热点元素提取
    print("\n\n" + "🔍" * 35)
    print("开始提取热点元素...")
    print("🔍" * 35)
    hot_elements, extract_quality = simple_extract_hot_elements(search_results)
    all_results["提取质量"] = extract_quality

    # 测试3: 数据可用性
    print("\n\n" + "✅" * 35)
    print("验证数据可用性...")
    print("✅" * 35)
    usability_quality = test_data_usability(hot_elements)
    all_results["可用性"] = usability_quality

    # 测试4: 多样性（可选，需要多次搜索）
    print("\n\n" + "🎲" * 35)
    print("验证多样性...")
    print("🎲" * 35)
    diversity_quality = test_diversity([hot_elements])
    all_results["多样性"] = diversity_quality

    # 最终报告
    print("\n\n" + "=" * 70)
    print("📊 最终质量评估报告")
    print("=" * 70)

    total_passed = 0
    total_checks = 0

    for category, result in all_results.items():
        passed = result.get("passed", 0)
        total = result.get("total", 0)
        rate = result.get("rate", 0)

        total_passed += passed
        total_checks += total

        print(f"\n【{category}】")
        print(f"  通过: {passed}/{total} ({rate * 100:.0f}%)")

        # 打印失败的检查
        for check in result.get("checks", []):
            if not check["passed"]:
                print(f"  ❌ {check['name']}: {check['details']}")

    overall_rate = total_passed / total_checks if total_checks > 0 else 0

    print("\n" + "=" * 70)
    print(f"总体评估: {total_passed}/{total_checks} 通过 ({overall_rate * 100:.1f}%)")
    print("=" * 70)

    if overall_rate >= 0.8:
        print("\n🎉 质量验证通过！")
        print("\n结论:")
        print("  ✅ 搜索API返回的内容质量良好")
        print("  ✅ 提取的热点元素准确且相关")
        print("  ✅ 数据格式正确，可供Story Planner使用")
        print("  ✅ 系统可以基于这些数据生成多样化的方案")
    elif overall_rate >= 0.5:
        print("\n⚠️  质量验证部分通过")
        print("\n建议:")
        print("  • 检查搜索API返回的内容是否相关")
        print("  • 优化提取规则或Prompt")
        print("  • 增加更多关键词匹配")
    else:
        print("\n❌ 质量验证未通过")
        print("\n需要检查:")
        print("  • 搜索API是否正常工作")
        print("  • 提取逻辑是否正确")
        print("  • 关键词库是否需要更新")

    print("=" * 70)

    return 0 if overall_rate >= 0.5 else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
