"""
测试主题库 API 端点
"""
import asyncio
import httpx

BASE_URL = "http://localhost:8000/api"

async def test_themes_api():
    """测试主题库 API"""
    print("🧪 测试主题库 API\n")
    
    async with httpx.AsyncClient() as client:
        # 1. 测试获取所有主题
        print("1️⃣ 测试 GET /themes")
        try:
            response = await client.get(f"{BASE_URL}/themes")
            if response.status_code == 200:
                data = response.json()
                themes = data.get("data", [])
                print(f"   ✅ 成功获取 {len(themes)} 个主题")
                for theme in themes:
                    print(f"      - {theme['name']} ({theme['slug']})")
            else:
                print(f"   ❌ 失败: {response.status_code} - {response.text[:200]}")
        except Exception as e:
            print(f"   ❌ 错误: {e}")
        
        # 2. 测试获取指定主题详情
        print("\n2️⃣ 测试 GET /themes/revenge")
        try:
            response = await client.get(f"{BASE_URL}/themes/revenge")
            if response.status_code == 200:
                data = response.json()
                theme = data.get("data", {})
                print(f"   ✅ 成功获取主题: {theme.get('name')}")
                print(f"      - 元素数: {len(theme.get('elements', []))}")
                print(f"      - 钩子数: {len(theme.get('hooks', []))}")
                print(f"      - 案例数: {len(theme.get('examples', []))}")
            else:
                print(f"   ❌ 失败: {response.status_code} - {response.text[:200]}")
        except Exception as e:
            print(f"   ❌ 错误: {e}")
        
        # 3. 测试获取主题元素
        print("\n3️⃣ 测试 GET /themes/revenge/elements")
        try:
            response = await client.get(f"{BASE_URL}/themes/revenge/elements")
            if response.status_code == 200:
                data = response.json()
                elements = data.get("data", [])
                total = data.get("total", 0)
                print(f"   ✅ 成功获取 {len(elements)}/{total} 个元素")
                if elements:
                    print(f"      示例: {elements[0]['name']} (评分: {elements[0].get('effectiveness_score')})")
            else:
                print(f"   ❌ 失败: {response.status_code} - {response.text[:200]}")
        except Exception as e:
            print(f"   ❌ 错误: {e}")
        
        # 4. 测试搜索元素
        print("\n4️⃣ 测试 GET /themes/search/elements?query=打脸")
        try:
            response = await client.get(f"{BASE_URL}/themes/search/elements?query=打脸")
            if response.status_code == 200:
                data = response.json()
                elements = data.get("data", [])
                print(f"   ✅ 搜索到 {len(elements)} 个相关元素")
                if elements:
                    for elem in elements[:3]:
                        print(f"      - {elem['name']}")
            else:
                print(f"   ❌ 失败: {response.status_code} - {response.text[:200]}")
        except Exception as e:
            print(f"   ❌ 错误: {e}")
        
        # 5. 测试获取钩子模板
        print("\n5️⃣ 测试 GET /themes/hooks/templates")
        try:
            response = await client.get(f"{BASE_URL}/themes/hooks/templates")
            if response.status_code == 200:
                data = response.json()
                hooks = data.get("data", [])
                total = data.get("total", 0)
                print(f"   ✅ 成功获取 {len(hooks)}/{total} 个钩子模板")
                if hooks:
                    types = set(h.get('hook_type') for h in hooks)
                    print(f"      类型分布: {', '.join(types)}")
            else:
                print(f"   ❌ 失败: {response.status_code} - {response.text[:200]}")
        except Exception as e:
            print(f"   ❌ 错误: {e}")
        
        # 6. 测试获取推荐
        print("\n6️⃣ 测试 POST /themes/revenge/recommend?target_episode=15")
        try:
            response = await client.post(f"{BASE_URL}/themes/revenge/recommend?target_episode=15")
            if response.status_code == 200:
                data = response.json()
                recommendations = data.get("data", {})
                elements = recommendations.get("recommended_elements", [])
                hooks = recommendations.get("recommended_hooks", [])
                print(f"   ✅ 成功生成推荐")
                print(f"      - 推荐元素: {len(elements)} 个")
                print(f"      - 推荐钩子: {len(hooks)} 个")
            else:
                print(f"   ❌ 失败: {response.status_code} - {response.text[:200]}")
        except Exception as e:
            print(f"   ❌ 错误: {e}")
        
        # 7. 测试获取主题案例
        print("\n7️⃣ 测试 GET /themes/revenge/examples")
        try:
            response = await client.get(f"{BASE_URL}/themes/revenge/examples")
            if response.status_code == 200:
                data = response.json()
                examples = data.get("data", [])
                total = data.get("total", 0)
                print(f"   ✅ 成功获取 {len(examples)}/{total} 个案例")
                if examples:
                    print(f"      示例: 《{examples[0]['title']}》({examples[0].get('release_year')})")
            else:
                print(f"   ❌ 失败: {response.status_code} - {response.text[:200]}")
        except Exception as e:
            print(f"   ❌ 错误: {e}")
    
    print("\n✅ API 测试完成!")

if __name__ == "__main__":
    asyncio.run(test_themes_api())
