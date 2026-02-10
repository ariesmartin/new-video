# 故事策划系统优化方案文档

## 文档信息
- **版本**: v1.0
- **日期**: 2026-02-10
- **状态**: 待实施
- **优先级**: P0（高优先级）

---

## 一、问题总结

### 1.1 核心问题清单

| 序号 | 问题类别 | 具体问题 | 影响程度 | 文件位置 |
|------|---------|---------|---------|---------|
| 1 | 主题限制 | 硬编码仅5个主题 | ⭐⭐⭐⭐⭐ | story_planner.py:103 |
| 2 | Prompt设计 | 固定示例过于详细 | ⭐⭐⭐⭐⭐ | 2_Story_Planner.md:82-106 |
| 3 | 数据污染 | "太奶奶"案例过度引用 | ⭐⭐⭐⭐ | seed_examples_final.json等 |
| 4 | 随机性不足 | 伪随机，缺乏多样性 | ⭐⭐⭐⭐ | story_planner.py:145 |
| 5 | 主题库静态 | 仅5个基础主题 | ⭐⭐⭐⭐ | seed_themes_final.json |
| 6 | 市场分析缺陷 | 搜索范围窄、缓存过长 | ⭐⭐⭐⭐ | market_analysis.py |
| 7 | 数据截断 | 搜索结果仅保留500字符 | ⭐⭐⭐ | market_analysis.py:93 |
| 8 | 硬编码覆盖 | get_hot_genres返回固定数据 | ⭐⭐⭐⭐ | market_analysis/__init__.py:73 |
| 9 | 缺乏强制规则 | Prompt未要求必须使用市场数据 | ⭐⭐⭐⭐ | 2_Story_Planner.md |
| 10 | 去重机制缺失 | 无历史方案比对 | ⭐⭐⭐ | story_planner.py |

---

## 二、优化方案总览

### 2.1 优化目标

1. **主题多样性**: 从5个扩展到15+主题
2. **创意独特性**: 减少重复率到<20%
3. **市场敏感度**: 实时捕捉热点，24小时内更新
4. **用户满意度**: 降低"重新生成"点击率

### 2.2 实施阶段

```
Phase 1（第1-2周）: 基础设施
├── 扩展主题库
├── 修复硬编码问题
└── 优化Prompt设计

Phase 2（第3-4周）: 市场分析增强
├── 扩大搜索范围
├── 热点元素提取
└── 缩短缓存周期

Phase 3（第5-6周）: 智能去重
├── 历史方案追踪
├── 重复检测算法
└── 用户偏好学习

Phase 4（第7-8周）: 效果验证
├── A/B测试
├── 数据分析
└── 持续优化
```

---

## 三、详细优化方案

### 3.1 扩展主题库（Phase 1）

#### 3.1.1 新增主题定义

在 `data_extraction/seed_themes_final.json` 中新增以下主题：

```json
{
  "themes": [
    // ... 现有5个主题 ...
    
    {
      "slug": "infinite_flow",
      "name": "无限流",
      "name_en": "Infinite Flow",
      "category": "fantasy",
      "description": "主角被卷入神秘的无限空间，需要在各种副本中求生并寻找真相",
      "summary": "从迷茫恐惧到适应生存，从独自挣扎到团队协作，最终揭开无限空间真相的情绪曲线",
      "core_formula": {
        "setup": {
          "description": "主角被神秘力量选中，进入无限空间，面临生死考验"
        },
        "rising": {
          "description": "主角在副本中求生，逐渐掌握规则，结识同伴，能力提升"
        },
        "climax": {
          "description": "主角发现无限空间的真相，面对最终Boss或艰难抉择"
        },
        "resolution": {
          "description": "主角逃离或掌控无限空间，获得自由或成为新秩序的建立者"
        }
      },
      "keywords": {
        "writing": ["副本", "求生", "规则", "团队", "智斗", "恐惧", "成长", "真相"],
        "visual": ["密闭空间", "诡异氛围", "紧张场景", "团队协作", "危机时刻", "未知空间"]
      },
      "audience_analysis": {
        "age_range": "18-30",
        "gender": "男女均有",
        "psychographics": "喜欢烧脑剧情、团队协作、对未知世界充满好奇"
      },
      "market_score": 88.0,
      "success_rate": 82.0
    },
    
    {
      "slug": "apocalypse",
      "name": "末世求生",
      "name_en": "Apocalypse Survival",
      "category": "scifi",
      "description": "在末日后的世界中挣扎求生，重建文明或寻找救赎",
      "summary": "从绝望崩溃到顽强求生，从独自挣扎到建立新秩序的情绪曲线",
      "core_formula": {
        "setup": {
          "description": "末日降临，主角失去一切，在废墟中求生"
        },
        "rising": {
          "description": "主角收集资源、建立避难所、结识幸存者、对抗威胁"
        },
        "climax": {
          "description": "面对最大危机（尸潮/资源枯竭/人性考验），主角做出艰难抉择"
        },
        "resolution": {
          "description": "主角建立新秩序或找到救赎，世界迎来新的希望"
        }
      },
      "keywords": {
        "writing": ["求生", "资源", "丧尸", "变异", "基地", "人性", "重建", "希望"],
        "visual": ["废墟", "荒凉", "战斗", "避难所", "装备", "幸存者", "危机"]
      },
      "audience_analysis": {
        "age_range": "20-35",
        "gender": "男性为主",
        "psychographics": "喜欢紧张刺激、生存挑战、对人性和社会秩序有深度思考"
      },
      "market_score": 85.0,
      "success_rate": 80.0
    },
    
    {
      "slug": "rules_horror",
      "name": "规则怪谈",
      "name_en": "Rules Horror",
      "category": "horror",
      "description": "在充满诡异规则的恐怖空间中解密生存",
      "summary": "从困惑不解到逐步理解规则，从恐惧逃避到主动破解的情绪曲线",
      "core_formula": {
        "setup": {
          "description": "主角进入诡异空间，发现必须遵守莫名其妙的规则才能生存"
        },
        "rising": {
          "description": "主角收集规则线索，发现规则矛盾，利用规则漏洞求生"
        },
        "climax": {
          "description": "主角面对核心规则谜题，必须做出违背常理的选择"
        },
        "resolution": {
          "description": "主角破解规则真相，逃离或掌控诡异空间"
        }
      },
      "keywords": {
        "writing": ["规则", "诡异", "解密", "恐惧", "逻辑", "悖论", "真相", "逃生"],
        "visual": ["诡异场景", "恐怖氛围", "细节特写", "紧张表情", "规则纸条", "诡异符号"]
      },
      "audience_analysis": {
        "age_range": "18-30",
        "gender": "男女均有",
        "psychographics": "喜欢逻辑推理、恐怖氛围、对超自然现象有兴趣"
      },
      "market_score": 87.0,
      "success_rate": 83.0
    },
    
    {
      "slug": "cyberpunk",
      "name": "赛博朋克",
      "name_en": "Cyberpunk",
      "category": "scifi",
      "description": "高科技低生活的反乌托邦世界中的冒险",
      "summary": "从底层挣扎到觉醒反抗，从个人生存到改变世界的情绪曲线",
      "core_formula": {
        "setup": {
          "description": "主角生活在高科技垄断的底层社会，为生存挣扎"
        },
        "rising": {
          "description": "主角获得特殊能力/技术，逐渐揭露公司/系统的黑暗面"
        },
        "climax": {
          "description": "主角面对系统核心，必须做出牺牲个人还是拯救世界的抉择"
        },
        "resolution": {
          "description": "主角改变或推翻旧秩序，建立新的平衡"
        }
      },
      "keywords": {
        "writing": ["黑客", "义体", "公司", "反抗", "霓虹", "底层", "觉醒", "未来"],
        "visual": ["霓虹灯", "雨夜", "高科技", "贫民窟", "义体改造", "全息投影", "机械"]
      },
      "audience_analysis": {
        "age_range": "18-35",
        "gender": "男性为主",
        "psychographics": "喜欢科技、对未来社会有思考、欣赏视觉美学"
      },
      "market_score": 82.0,
      "success_rate": 78.0
    },
    
    {
      "slug": "business_war",
      "name": "职场商战",
      "name_en": "Business War",
      "category": "drama",
      "description": "商业世界中的权谋斗争和智力较量",
      "summary": "从职场新人到商业精英，从被动挨打到主动反击的情绪曲线",
      "core_formula": {
        "setup": {
          "description": "主角进入商业世界，遭遇职场打压或商业阴谋"
        },
        "rising": {
          "description": "主角展现商业才能，逐步掌握资源，与对手展开博弈"
        },
        "climax": {
          "description": "在商业对决的关键时刻，主角以智慧或勇气战胜对手"
        },
        "resolution": {
          "description": "主角成为商业巨头或建立新的商业秩序"
        }
      },
      "keywords": {
        "writing": ["商战", "并购", "股市", "谈判", "策略", "职场", "权谋", "成功"],
        "visual": ["写字楼", "会议室", "豪华办公室", "商业宴会", "城市夜景", "豪车"]
      },
      "audience_analysis": {
        "age_range": "25-40",
        "gender": "男女均有",
        "psychographics": "关注商业、职场成长，对成功有强烈渴望"
      },
      "market_score": 80.0,
      "success_rate": 75.0
    },
    
    {
      "slug": "medical_drama",
      "name": "医疗剧",
      "name_en": "Medical Drama",
      "category": "drama",
      "description": "医院背景下的生命故事和人性考验",
      "summary": "从医学理想主义到面对现实，从个人成长到团队协作的情绪曲线",
      "core_formula": {
        "setup": {
          "description": "主角作为医护人员进入医院，面对生死和人性考验"
        },
        "rising": {
          "description": "主角处理复杂病例，面对医疗伦理困境，与同事建立关系"
        },
        "climax": {
          "description": "在重大疫情或医疗事故中，主角必须做出关键抉择"
        },
        "resolution": {
          "description": "主角成长为优秀的医者，找到医学与人性的平衡"
        }
      },
      "keywords": {
        "writing": ["生命", "手术", "医患", "伦理", "成长", "团队", "救治", "希望"],
        "visual": ["手术室", "病房", "急救", "医疗器械", "白大褂", "医院走廊", "生命监护"]
      },
      "audience_analysis": {
        "age_range": "20-45",
        "gender": "女性为主",
        "psychographics": "关注生命价值、医疗行业，对人性有深度思考"
      },
      "market_score": 78.0,
      "success_rate": 75.0
    },
    
    {
      "slug": "sports",
      "name": "体育竞技",
      "name_en": "Sports Drama",
      "category": "drama",
      "description": "体育赛场上的热血奋斗和青春成长",
      "summary": "从默默无闻到崭露头角，从个人奋斗到团队协作的情绪曲线",
      "core_formula": {
        "setup": {
          "description": "主角怀揣体育梦想，面临天赋不足或资源匮乏的困境"
        },
        "rising": {
          "description": "主角刻苦训练，克服伤病和心理障碍，逐步崭露头角"
        },
        "climax": {
          "description": "在关键比赛中，主角面对强大对手和巨大压力"
        },
        "resolution": {
          "description": "主角战胜对手或自我，实现梦想或找到新的目标"
        }
      },
      "keywords": {
        "writing": ["梦想", "训练", "比赛", "团队", "热血", "成长", "胜利", "坚持"],
        "visual": ["赛场", "训练", "汗水", "奖杯", "团队庆祝", "紧张比赛", "起跑线"]
      },
      "audience_analysis": {
        "age_range": "16-30",
        "gender": "男性为主",
        "psychographics": "喜欢热血青春、团队友情、对体育有热情"
      },
      "market_score": 75.0,
      "success_rate": 72.0
    },
    
    {
      "slug": "food_culture",
      "name": "美食文化",
      "name_en": "Food Culture",
      "category": "romance",
      "description": "以美食为媒介的温暖治愈故事",
      "summary": "从味觉记忆到情感连接，从个人孤独到温暖陪伴的情绪曲线",
      "core_formula": {
        "setup": {
          "description": "主角与美食有特殊连接，或因美食而处于人生低谷"
        },
        "rising": {
          "description": "主角通过美食治愈他人，建立人际关系，面对商业或情感挑战"
        },
        "climax": {
          "description": "在美食大赛或重要宴会中，主角面临最大挑战"
        },
        "resolution": {
          "description": "主角通过美食获得事业成功和情感圆满"
        }
      },
      "keywords": {
        "writing": ["美食", "治愈", "温暖", "味道", "回忆", "传承", "爱情", "文化"],
        "visual": ["精美菜肴", "厨房", "用餐场景", "食材特写", "温馨餐厅", "烹饪过程"]
      },
      "audience_analysis": {
        "age_range": "20-40",
        "gender": "女性为主",
        "psychographics": "喜欢美食、温暖治愈、对生活品质有追求"
      },
      "market_score": 76.0,
      "success_rate": 74.0
    }
  ]
}
```

#### 3.1.2 修改 Story Planner 动态加载主题

修改 `backend/agents/story_planner.py`：

```python
# 删除硬编码列表（第103行）
# all_theme_slugs = ["revenge", "romance", "suspense", "transmigration", "family_urban"]

# 新增动态加载函数
async def _get_all_theme_slugs() -> List[str]:
    """从数据库动态获取所有可用主题"""
    try:
        from backend.services.database import get_db_service
        db = get_db_service()
        themes = await db.get_all_themes()
        return [theme["slug"] for theme in themes]
    except Exception as e:
        logger.warning("Failed to load themes from DB, using fallback", error=str(e))
        # 回退方案：返回所有已知主题
        return [
            "revenge", "romance", "suspense", "transmigration", "family_urban",
            "infinite_flow", "apocalypse", "rules_horror", "cyberpunk",
            "business_war", "medical_drama", "sports", "food_culture"
        ]

# 在 _load_story_planner_prompt 中使用
async def _load_story_planner_prompt(
    market_report: Optional[dict] = None,
    episode_count: int = 80,
    episode_duration: float = 1.5,
    genre: str = "现代都市",
    setting: str = "modern",
) -> str:
    # ... 现有代码 ...
    
    # ✅ 注入主题库数据 - 动态加载所有主题
    all_theme_slugs = await _get_all_theme_slugs()
    
    try:
        # ✅ 加载所有题材的完整数据
        all_themes_context = []
        # 随机选择5-8个主题（而非固定5个）
        num_themes = random.randint(5, min(8, len(all_theme_slugs)))
        selected_slugs = random.sample(all_theme_slugs, k=num_themes)
        
        for slug in selected_slugs:
            try:
                theme_context = await load_genre_context.ainvoke({"genre_id": slug})
                all_themes_context.append(f"\n{'=' * 50}\n{theme_context}\n{'=' * 50}")
            except Exception as e:
                logger.warning(f"Failed to load theme {slug}", error=str(e))
                continue
        
        # ... 剩余代码 ...
```

---

### 3.2 重构Prompt设计（Phase 1）

#### 3.2.1 修改 2_Story_Planner.md

**删除或修改的部分**：

```markdown
## ❌ 删除这部分（第82-106行）
### 热门融合公式（必须参考）
1. **【复仇逆袭 + 甜宠恋爱】= "复仇甜宠"**
   ...

## ✅ 替换为：
### 🎨 跨题材融合创新指南

#### 创新原则
1. **反差张力**: 寻找两个题材间的冲突点
   - 示例：复仇（冷酷）+ 甜宠（温暖）= 在复仇过程中产生情感羁绊
   - 示例：悬疑（理性）+ 穿越（幻想）= 用科学方法破解超自然现象

2. **元素借用**: 从题材A借用核心元素，放入题材B的背景
   - 示例：将"无限流"的副本机制 + "甜宠"的情感线 = 在副本中谈恋爱
   - 示例：将"赛博朋克"的高科技 + "古装"的背景 = 古代科幻

3. **视角转换**: 从非传统视角讲述传统题材
   - 示例：从"反派"视角讲述复仇故事
   - 示例：从"AI"视角讲述人类情感

#### 🚫 禁止使用的组合（已过度使用）
以下组合在市场上已出现超过50次，请避免直接使用：
- ❌ 银发/太奶奶 + 穿越
- ❌ 霸总 + 甜宠（纯甜无冲突）
- ❌ 重生 + 复仇（无新意）
- ❌ 豪门 + 身份互换

如果你必须使用以上元素，请确保：
- 加入至少2个创新元素
- 从完全不同的角度切入
- 创造至少1个市场未见过的设定

#### ✅ 鼓励尝试的组合（创新方向）
- 🆕 无限流 + 职场 = 在公司副本中求生
- 🆕 末世 + 美食 = 在末日寻找和传承美食文化
- 🆕 赛博朋克 + 医疗 = 高科技医疗伦理困境
- 🆕 规则怪谈 + 校园 = 学校里的诡异规则
- 🆕 体育 + 悬疑 = 体育赛事中的谋杀案
```

**新增强制创新规则（在第160行前）**：

```markdown
## 🎯 强制创新协议

### 步骤1：主题选择（必须遵循）
从系统提供的主题库中，使用以下策略选择2-3个主题：
1. **主主题**（必须）：从热门主题中选择1个
2. **创新主题**（必须）：从冷门或新兴主题中选择1个
3. **跨界元素**（可选）：从完全不相关的领域选择1个元素

### 步骤2：组合创新检查清单
生成方案前，必须回答以下问题：
- [ ] 这个组合是否在最近3个月内出现过？
- [ ] 是否包含至少1个非传统元素？
- [ ] 是否有明确的冲突张力？
- [ ] 是否能用一句话吸引观众？
- [ ] 是否与"已过度使用组合"重复率<30%？

### 步骤3：差异化验证
对于每个生成的方案，提供以下信息：
```
创新点：____（本方案最核心的创新之处）
市场差异化：____（与市场上现有作品的区别）
风险等级：低/中/高（创新的激进程度）
```

如果不通过检查清单，请重新选择主题组合。

### 步骤4：实时热点融合
从市场热点数据中选择至少1个元素融入方案：
- 热门人设：____
- 热门背景：____
- 热门冲突：____
```

---

### 3.3 优化市场分析功能（Phase 2）

#### 3.3.1 扩大搜索范围

修改 `backend/services/market_analysis.py`：

```python
# 第55-59行替换为：
async def _get_search_queries() -> List[str]:
    """动态生成搜索查询，包含基础查询+随机查询"""
    
    # 基础查询（每日必搜）
    base_queries = [
        "2026年短剧热度榜 抖音快手 日榜",
        "2026年短剧播放量排行 微信视频号",
        "2026年短剧爆款 小红书推荐",
    ]
    
    # 题材趋势查询（轮换）
    genre_queries = [
        "2026年短剧新兴题材 无限流 规则怪谈",
        "2026年短剧创新元素 银发 穿越 重生",
        "2026年短剧热门人设 反差萌 身份错位",
        "2026年短剧热门背景 赛博朋克 末世 仙侠",
        "2026年短剧创新案例 爆款分析",
    ]
    
    # 社会热点查询（轮换）
    social_queries = [
        "2026年热门话题 短剧改编",
        "2026年网络流行语 短剧",
        "2026年社会事件 短剧创作",
        "2026年抖音热门挑战 短剧",
    ]
    
    # 竞品分析查询（轮换）
    competitor_queries = [
        "2026年短剧爆款剧名 播放量",
        "2026年短剧热门剧 商业模式",
        "2026年短剧创新案例 获奖作品",
    ]
    
    # 随机选择，确保多样性
    import random
    selected_genre = random.sample(genre_queries, k=2)
    selected_social = random.sample(social_queries, k=1)
    selected_competitor = random.sample(competitor_queries, k=1)
    
    return base_queries + selected_genre + selected_social + selected_competitor

# 在 run_daily_analysis 中使用
search_queries = await _get_search_queries()
```

#### 3.3.2 增加热点元素提取

在 `backend/services/market_analysis.py` 中新增：

```python
async def _extract_hot_elements(self, search_results: list) -> dict:
    """使用LLM从搜索结果中提取具体的热点元素"""
    from langchain_core.messages import HumanMessage, SystemMessage
    
    # 构建完整搜索上下文（不截断）
    context = "\n\n".join(
        [f"搜索: {r['query']}\n结果: {r['result']}" for r in search_results]
    )
    
    # 提取提示词
    extract_prompt = """你是一个专业的短剧市场分析师。从以下搜索结果中提取2026年短剧市场的具体热点元素。

搜索结果：
{context}

请提取以下信息（JSON格式）：
{{
    "hot_tropes": ["元素1", "元素2", ...],  // 提取10个当前最热门的元素（每个4-8字）
    "hot_settings": ["背景1", "背景2", ...],  // 提取5个热门背景设定
    "hot_character_types": ["人设1", "人设2", ...],  // 提取8个热门人设类型
    "emerging_combinations": ["组合1", "组合2", ...],  // 提取5个新兴题材组合
    "overused_tropes": ["套路1", "套路2", ...],  // 提取5个已过度使用的套路
    "specific_works": ["剧名1", "剧名2", ...]  // 提取10个具体的爆款剧名
}}

要求：
1. 必须是具体的、可操作的元素，而非抽象概念
2. 每个元素不超过10个字
3. 优先提取创新元素，而非传统套路
4. 确保信息来自搜索结果，而非编造
5. overused_tropes 必须是已经出现多次、观众审美疲劳的套路

只返回JSON，不要其他解释。"""

    messages = [
        SystemMessage(content="你是一个专业的短剧市场数据提取助手。"),
        HumanMessage(content=extract_prompt.format(context=context[:8000]))  # 限制长度但比500多
    ]
    
    model = await self.router.get_model(
        user_id="system",
        task_type=TaskType.MARKET_ANALYST,
        project_id=None,
    )
    
    response = await model.ainvoke(messages)
    
    # 解析JSON
    try:
        import json
        content = response.content
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        return json.loads(content)
    except Exception as e:
        logger.error("Failed to extract hot elements", error=str(e))
        return {
            "hot_tropes": ["身份错位", "银发逆袭", "双重人格"],
            "hot_settings": ["现代职场", "古代宫廷", "末世废墟"],
            "hot_character_types": ["霸总", "太奶奶", "实习生"],
            "emerging_combinations": ["无限流+恋爱", "赛博朋克+医疗"],
            "overused_tropes": ["霸道总裁", "重生复仇", "豪门恩怨"],
            "specific_works": []
        }

# 在 run_daily_analysis 中调用
async def run_daily_analysis(self) -> dict[str, Any]:
    logger.info("Starting daily market analysis")
    
    try:
        # 1. 搜索市场数据
        search_queries = await self._get_search_queries()
        search_results = []
        for query in search_queries:
            try:
                result = await metaso_search(query)
                search_results.append({"query": query, "result": result})
                logger.info("Search completed", query=query)
            except Exception as e:
                logger.error("Search failed", query=query, error=str(e))
        
        # 2. ✅ 新增：提取热点元素
        hot_elements = await self._extract_hot_elements(search_results)
        
        # 3. LLM 分析
        analysis = await self._analyze_with_llm(search_results, hot_elements)
        
        # 4. 保存到数据库（包含热点元素）
        await self._save_analysis(analysis, hot_elements)
        
        logger.info(
            "Daily market analysis completed",
            genre_count=len(analysis.get("genres", [])),
            hot_tropes_count=len(hot_elements.get("hot_tropes", []))
        )
        
        return analysis
        
    except Exception as e:
        logger.error("Daily market analysis failed", error=str(e))
        raise
```

#### 3.3.3 缩短缓存周期

```python
# backend/services/market_analysis.py:173
# 修改缓存时间

# ❌ 旧代码：7天
valid_until = datetime.now(timezone.utc) + timedelta(days=7)

# ✅ 新代码：1天（对于热点数据）
valid_until = datetime.now(timezone.utc) + timedelta(days=1)
```

#### 3.3.4 修复硬编码的get_hot_genres

修改 `backend/skills/market_analysis/__init__.py`：

```python
# 删除或修改第73-79行的硬编码数据
# ❌ 删除
# hot_genres_data = [
#     {"name": "现代都市", "score": 95, "trend": "up"},
#     ...
# ]

# ✅ 新实现
@tool
def get_hot_genres(limit: int = 5) -> str:
    """
    Skill: 获取当前热门的短剧题材
    
    Args:
        limit: 返回数量，默认5个
    
    Returns:
        热门题材列表（基于实时搜索）
    """
    # 先尝试获取缓存的市场报告
    try:
        import asyncio
        from backend.services.market_analysis import get_market_analysis_service
        
        service = get_market_analysis_service()
        report = asyncio.run(service.get_latest_analysis())
        
        if report and report.get("genres"):
            genres = report["genres"][:limit]
            lines = [f"## 🔥 热门短剧题材 TOP {limit}\n"]
            for i, genre in enumerate(genres, 1):
                trend = genre.get("trend", "stable")
                trend_icon = {"hot": "🔥", "up": "📈", "stable": "➡️", "down": "📉"}.get(trend, "•")
                lines.append(f"{i}. **{genre.get('name', 'N/A')}** {trend_icon}")
                lines.append(f"   {genre.get('description', '')}")
            return "\n".join(lines)
    except Exception as e:
        logger.warning("Failed to get cached hot genres, falling back to search", error=str(e))
    
    # 回退：实时搜索
    search_result = duckduckgo_search("2026 短剧 热门题材 排行榜")
    return f"## 🔥 热门短剧题材\n\n基于实时搜索：\n{search_result[:800]}"
```

---

### 3.4 强制使用市场数据（Phase 2）

#### 3.4.1 修改 Story Planner 的Prompt注入

```python
# backend/agents/story_planner.py

def _format_market_report(report: dict) -> str:
    """格式化市场分析报告为 Prompt 可用的字符串（增强版）"""
    lines = ["## 📊 最新市场分析报告（必须使用）"]
    
    # 添加热点元素（新增）
    hot_elements = report.get("hot_elements", {})
    if hot_elements:
        lines.append("\n### 🔥 当前市场热点元素（选择至少2个融入方案）")
        
        hot_tropes = hot_elements.get("hot_tropes", [])
        if hot_tropes:
            lines.append("\n**热门元素**（当前最受关注）：")
            for i, trope in enumerate(hot_tropes[:8], 1):
                lines.append(f"{i}. {trope}")
        
        emerging = hot_elements.get("emerging_combinations", [])
        if emerging:
            lines.append("\n**🆕 新兴组合**（创新方向）：")
            for combo in emerging[:5]:
                lines.append(f"- {combo}")
        
        overused = hot_elements.get("overused_tropes", [])
        if overused:
            lines.append("\n**🚫 已过度使用**（避免）：")
            for trope in overused[:5]:
                lines.append(f"- ❌ {trope}")
        
        specific_works = hot_elements.get("specific_works", [])
        if specific_works:
            lines.append("\n**🎬 参考爆款剧**（了解市场）：")
            for work in specific_works[:5]:
                lines.append(f"- 《{work}》")
    
    # 原有 genres 和 tones 处理
    genres = report.get("genres", [])
    if genres:
        lines.append("\n### 热门题材趋势")
        for g in genres:
            trend_emoji = {"hot": "🔥", "up": "📈", "stable": "➡️", "down": "📉"}.get(
                g.get("trend"), "•"
            )
            lines.append(f"{trend_emoji} {g.get('name', 'N/A')}: {g.get('description', '')}")
    
    tones = report.get("tones", [])
    if tones:
        lines.append(f"\n### 推荐调性\n{', '.join(tones)}")
    
    insights = report.get("insights", "")
    if insights:
        lines.append(f"\n### 市场洞察\n{insights}")
    
    audience = report.get("audience", "")
    if audience:
        lines.append(f"\n### 目标受众\n{audience}")
    
    # 添加强制使用说明
    lines.append("\n" + "="*50)
    lines.append("⚠️ **强制使用规则**：")
    lines.append("1. 必须从【热门元素】中选择至少2个融入方案")
    lines.append("2. 必须从【新兴组合】中选择至少1个尝试")
    lines.append("3. 严禁使用【已过度使用】中的元素作为主要卖点")
    lines.append("4. 如果生成的方案与【参考爆款剧】相似度>50%，必须重新生成")
    lines.append("="*50)
    
    return "\n".join(lines)
```

---

### 3.5 智能去重机制（Phase 3）

#### 3.5.1 数据库表设计

在 `backend/supabase/migrations/` 创建新迁移文件：

```sql
-- 007_generated_plans_history.sql
-- 记录生成的方案历史，用于去重

CREATE TABLE IF NOT EXISTS generated_plans_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) NOT NULL,
    project_id UUID REFERENCES projects(id),
    
    -- 方案内容指纹
    plan_title TEXT NOT NULL,  -- 方案标题
    plan_summary TEXT,  -- 一句话梗概
    core_tropes JSONB DEFAULT '[]',  -- 核心元素列表
    genre_combination JSONB DEFAULT '[]',  -- 题材组合
    
    -- 生成参数
    background_setting TEXT,  -- 背景设定
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- 用户反馈
    user_selected BOOLEAN DEFAULT FALSE,  -- 用户是否选择
    user_regenerated BOOLEAN DEFAULT FALSE,  -- 用户是否重新生成
    
    -- 相似度分析（可选）
    embedding VECTOR(1536),  -- 用于语义相似度计算
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 索引
CREATE INDEX idx_gen_plans_user ON generated_plans_history(user_id);
CREATE INDEX idx_gen_plans_project ON generated_plans_history(project_id);
CREATE INDEX idx_gen_plans_time ON generated_plans_history(generated_at DESC);
CREATE INDEX idx_gen_plans_tropes ON generated_plans_history USING GIN(core_tropes);

-- 注释
COMMENT ON TABLE generated_plans_history IS '记录用户生成的方案历史，用于去重和偏好学习';
COMMENT ON COLUMN generated_plans_history.core_tropes IS '方案使用的核心元素，用于相似度比对';
COMMENT ON COLUMN generated_plans_history.embedding IS '语义向量，用于计算方案相似度';
```

#### 3.5.2 去重服务实现

创建 `backend/services/plan_deduplication.py`：

```python
"""
方案去重服务

检测新生成的方案是否与历史方案重复
"""

import json
from typing import List, Dict, Any
from datetime import datetime, timedelta
import structlog

logger = structlog.get_logger(__name__)


class PlanDeduplicationService:
    """方案去重服务"""
    
    def __init__(self, db_service=None):
        from backend.services.database import get_db_service
        self.db = db_service or get_db_service()
    
    async def check_similarity(
        self,
        user_id: str,
        new_plan: Dict[str, Any],
        threshold: float = 0.7
    ) -> Dict[str, Any]:
        """
        检查新方案与历史方案的相似度
        
        Args:
            user_id: 用户ID
            new_plan: 新方案数据
            threshold: 相似度阈值（超过则认为重复）
        
        Returns:
            {
                "is_duplicate": bool,
                "similarity_score": float,
                "similar_plans": List[Dict],
                "suggestions": List[str]  # 去重建议
            }
        """
        # 1. 获取用户最近生成的方案（30天内）
        recent_plans = await self._get_recent_plans(user_id, days=30)
        
        if not recent_plans:
            return {
                "is_duplicate": False,
                "similarity_score": 0.0,
                "similar_plans": [],
                "suggestions": []
            }
        
        # 2. 计算相似度
        similarities = []
        for plan in recent_plans:
            score = self._calculate_similarity(new_plan, plan)
            similarities.append({
                "plan": plan,
                "score": score
            })
        
        # 3. 找出最相似的
        similarities.sort(key=lambda x: x["score"], reverse=True)
        max_similarity = similarities[0]["score"] if similarities else 0
        
        # 4. 判断是否重复
        is_duplicate = max_similarity >= threshold
        
        # 5. 生成建议
        suggestions = []
        if is_duplicate:
            similar = similarities[0]["plan"]
            suggestions = self._generate_dedup_suggestions(new_plan, similar)
        
        return {
            "is_duplicate": is_duplicate,
            "similarity_score": max_similarity,
            "similar_plans": [s["plan"] for s in similarities[:3]],
            "suggestions": suggestions
        }
    
    def _calculate_similarity(
        self,
        plan1: Dict[str, Any],
        plan2: Dict[str, Any]
    ) -> float:
        """计算两个方案的相似度（0-1）"""
        scores = []
        
        # 1. 标题相似度（简单字符串匹配）
        title1 = plan1.get("title", "").lower()
        title2 = plan2.get("title", "").lower()
        if title1 and title2:
            # Jaccard相似度
            set1 = set(title1)
            set2 = set(title2)
            jaccard = len(set1 & set2) / len(set1 | set2) if set1 | set2 else 0
            scores.append(jaccard * 0.2)  # 权重20%
        
        # 2. 核心元素重叠度
        tropes1 = set(plan1.get("core_tropes", []))
        tropes2 = set(plan2.get("core_tropes", []))
        if tropes1 and tropes2:
            overlap = len(tropes1 & tropes2) / len(tropes1 | tropes2) if tropes1 | tropes2 else 0
            scores.append(overlap * 0.4)  # 权重40%
        
        # 3. 题材组合相似度
        genres1 = set(plan1.get("genre_combination", []))
        genres2 = set(plan2.get("genre_combination", []))
        if genres1 and genres2:
            genre_overlap = len(genres1 & genres2) / len(genres1 | genres2) if genres1 | genres2 else 0
            scores.append(genre_overlap * 0.3)  # 权重30%
        
        # 4. 背景设定相似度
        setting1 = plan1.get("background_setting", "").lower()
        setting2 = plan2.get("background_setting", "").lower()
        if setting1 and setting2:
            setting_sim = 1.0 if setting1 == setting2 else 0.0
            scores.append(setting_sim * 0.1)  # 权重10%
        
        return sum(scores) / len(scores) if scores else 0.0
    
    def _generate_dedup_suggestions(
        self,
        new_plan: Dict[str, Any],
        similar_plan: Dict[str, Any]
    ) -> List[str]:
        """生成去重建议"""
        suggestions = []
        
        # 1. 替换核心元素
        new_tropes = set(new_plan.get("core_tropes", []))
        similar_tropes = set(similar_plan.get("core_tropes", []))
        common_tropes = new_tropes & similar_tropes
        
        if common_tropes:
            suggestions.append(
                f"尝试替换这些核心元素：{', '.join(list(common_tropes)[:3])}"
            )
        
        # 2. 改变题材组合
        new_genres = set(new_plan.get("genre_combination", []))
        similar_genres = set(similar_plan.get("genre_combination", []))
        
        if new_genres == similar_genres:
            suggestions.append(
                "尝试完全不同的题材组合，至少更换1个题材"
            )
        
        # 3. 改变背景设定
        if new_plan.get("background_setting") == similar_plan.get("background_setting"):
            suggestions.append(
                f"更换背景设定：从'{new_plan.get('background_setting')}'改为其他"
            )
        
        # 4. 添加创新元素
        suggestions.append(
            "引入1-2个市场上尚未出现的新元素"
        )
        
        return suggestions
    
    async def _get_recent_plans(
        self,
        user_id: str,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """获取用户最近生成的方案"""
        try:
            # 这里需要实现数据库查询
            # 暂时返回空列表
            return []
        except Exception as e:
            logger.error("Failed to get recent plans", error=str(e))
            return []
    
    async def save_plan(
        self,
        user_id: str,
        project_id: str,
        plan_data: Dict[str, Any]
    ):
        """保存生成的方案到历史记录"""
        try:
            # 提取核心元素
            content = plan_data.get("content", "")
            core_tropes = self._extract_tropes_from_content(content)
            
            # 构建记录
            record = {
                "user_id": user_id,
                "project_id": project_id,
                "plan_title": plan_data.get("title", ""),
                "plan_summary": plan_data.get("summary", ""),
                "core_tropes": json.dumps(core_tropes),
                "genre_combination": json.dumps(plan_data.get("genres", [])),
                "background_setting": plan_data.get("setting", ""),
            }
            
            # 保存到数据库
            await self.db.create_plan_history(record)
            
        except Exception as e:
            logger.error("Failed to save plan", error=str(e))
    
    def _extract_tropes_from_content(self, content: str) -> List[str]:
        """从方案内容中提取核心元素"""
        # 简单的关键词提取，可以用更复杂的NLP
        common_tropes = [
            "复仇", "甜宠", "穿越", "重生", "悬疑", "推理",
            "霸总", "太奶奶", "逆袭", "打脸", "身份互换",
            "契约婚姻", "失忆", "误会", "守护", "暗恋"
        ]
        
        found = []
        content_lower = content.lower()
        for trope in common_tropes:
            if trope in content_lower:
                found.append(trope)
        
        return found[:10]  # 最多返回10个


# 全局实例
_dedup_service = None


def get_dedup_service() -> PlanDeduplicationService:
    """获取去重服务实例"""
    global _dedup_service
    if _dedup_service is None:
        _dedup_service = PlanDeduplicationService()
    return _dedup_service
```

#### 3.5.3 在Story Planner中集成去重

```python
# backend/agents/story_planner.py

async def create_story_planner_agent(
    user_id: str,
    project_id: Optional[str] = None,
    episode_count: int = 80,
    episode_duration: float = 1.5,
    genre: str = "现代都市",
    setting: str = "modern",
    is_regenerate: bool = False,
    variation_seed: Optional[int] = None,
):
    """创建 Story Planner Agent（增强版）"""
    
    # ... 现有代码：获取市场报告 ...
    
    # ✅ 新增：如果是重新生成，检查去重
    if is_regenerate:
        from backend.services.plan_deduplication import get_dedup_service
        dedup_service = get_dedup_service()
        
        # 获取用户历史方案
        recent_plans = await dedup_service._get_recent_plans(user_id, days=7)
        
        if recent_plans:
            # 提取已使用的元素
            used_tropes = set()
            used_combinations = []
            for plan in recent_plans:
                used_tropes.update(plan.get("core_tropes", []))
                used_combinations.append(plan.get("genre_combination", []))
            
            # 注入去重提示
            dedup_context = f"""
## 🚫 去重提醒（重新生成时必须遵循）

根据你最近生成的方案，以下元素已经被使用过：
- 已使用元素：{', '.join(list(used_tropes)[:15])}
- 已使用组合：{len(used_combinations)} 种

### 强制去重规则：
1. **严禁**使用与最近3个方案相同的核心元素组合
2. **必须**尝试至少1个全新的题材
3. **必须**从市场热点数据中选择未使用过的元素
4. 如果无法生成不重复的方案，请明确告知用户

### 创新建议：
- 尝试完全不同的题材组合（如之前用了复仇+甜宠，这次尝试悬疑+美食）
- 更换主角设定（如之前是太奶奶，这次尝试AI机器人）
- 改变故事背景（如之前是现代都市，这次尝试赛博朋克）
"""
            # 将去重上下文注入prompt
            # 注意：需要在 _load_story_planner_prompt 中处理
    
    # ... 继续现有代码 ...
```

---

### 3.6 清理数据污染（Phase 1-2）

#### 3.6.1 减少"太奶奶"案例的权重

在 `data_extraction/seed_examples_final.json` 中：

```json
{
  "theme_examples": [
    // ... 其他案例 ...
    {
      "title": "十八岁太奶奶驾到",
      "description": "科学院院士灵魂重生到18岁重孙女身上",
      "why_it_works": "高概念+双降维的人设逻辑，反差萌强烈",
      "market_score": 92,
      // ✅ 添加标签，标记为高频案例
      "tags": ["silver_hair", "transmigration", "viral_2024"],
      "usage_frequency": "high",  // 标记高频使用
      "recommendation": "caution"  // 谨慎推荐
    },
    // ... 增加更多多样化案例 ...
  ]
}
```

#### 3.6.2 在Prompt中增加警告

```markdown
### ⚠️ 数据偏见警告

请注意，训练数据中"银发/太奶奶"类案例被过度使用，导致AI可能倾向于生成此类题材。

为保持创新性，请：
1. **降低**银发/穿越/重生类题材的生成概率（除非用户明确要求）
2. **提高**新兴题材（无限流、规则怪谈、赛博朋克等）的生成概率
3. **平衡**推荐，确保3个方案覆盖不同的创新方向
```

---

## 四、实施计划

### 4.1 第一周：Phase 1 基础设施

**Day 1-2：扩展主题库**
- [ ] 创建新的主题定义（13个主题）
- [ ] 更新 `seed_themes_final.json`
- [ ] 执行数据库迁移

**Day 3-4：修复硬编码**
- [ ] 修改 `story_planner.py`，移除硬编码列表
- [ ] 实现动态主题加载
- [ ] 测试动态加载功能

**Day 5-7：重构Prompt**
- [ ] 修改 `2_Story_Planner.md`，移除固定示例
- [ ] 添加强制创新协议
- [ ] 添加数据偏见警告
- [ ] 测试新Prompt效果

### 4.2 第二周：Phase 1 收尾 + Phase 2 开始

**Day 8-10：市场分析优化**
- [ ] 扩大搜索查询范围
- [ ] 实现热点元素提取
- [ ] 缩短缓存周期到1天

**Day 11-14：强制使用市场数据**
- [ ] 修改 `_format_market_report`，增加热点元素
- [ ] 修改Prompt注入逻辑
- [ ] 修复 `get_hot_genres` 硬编码
- [ ] 测试市场数据注入效果

### 4.3 第三周：Phase 3 去重机制

**Day 15-17：数据库设计**
- [ ] 创建迁移文件
- [ ] 实现 `PlanDeduplicationService`
- [ ] 添加数据库查询方法

**Day 18-21：集成去重**
- [ ] 在 `create_story_planner_agent` 中集成
- [ ] 实现相似度计算
- [ ] 生成去重建议
- [ ] 测试去重功能

### 4.4 第四周：测试与优化

**Day 22-28：全面测试**
- [ ] 单元测试
- [ ] 集成测试
- [ ] A/B测试准备
- [ ] 效果验证

---

## 五、效果评估指标

### 5.1 量化指标

| 指标 | 当前值 | 目标值 | 测量方法 |
|------|--------|--------|----------|
| 主题多样性 | 5个 | 15+个 | 统计不同主题的使用频率 |
| 方案重复率 | ~60% | <20% | 用户重新生成点击率 |
| 平均创新度评分 | 3.2/5 | 4.0+/5 | 用户满意度调查 |
| 市场热点响应时间 | 7天 | <24小时 | 从热点出现到系统响应时间 |
| "重新生成"点击率 | ~45% | <25% | 前端埋点统计 |

### 5.2 定性指标

- 用户反馈：方案是否"有新鲜感"
- 编辑审核：方案的市场竞争力评估
- 创意独特性：专家评审创新度

---

## 六、风险与应对

### 6.1 风险识别

| 风险 | 概率 | 影响 | 应对措施 |
|------|------|------|----------|
| 新主题数据质量不佳 | 中 | 中 | 增加人工审核流程 |
| 搜索API限制或失败 | 高 | 中 | 实现多层回退机制 |
| 去重过于严格 | 低 | 高 | 可调节阈值参数 |
| 性能下降 | 中 | 中 | 增加缓存，异步处理 |

### 6.2 回退方案

如果优化效果不佳：
1. 保留新主题库，但降低权重
2. 调整去重阈值
3. 增加人工干预机制

---

## 七、附录

### 7.1 完整主题列表

| 序号 | Slug | 名称 | 类别 | 市场分 |
|------|------|------|------|--------|
| 1 | revenge | 复仇逆袭 | drama | 95.5 |
| 2 | sweet_romance | 甜宠恋爱 | romance | 88.0 |
| 3 | suspense | 悬疑推理 | drama | 80.0 |
| 4 | transmigration | 穿越重生 | fantasy | 90.0 |
| 5 | family | 家庭伦理 | drama | 75.0 |
| 6 | infinite_flow | 无限流 | fantasy | 88.0 |
| 7 | apocalypse | 末世求生 | scifi | 85.0 |
| 8 | rules_horror | 规则怪谈 | horror | 87.0 |
| 9 | cyberpunk | 赛博朋克 | scifi | 82.0 |
| 10 | business_war | 职场商战 | drama | 80.0 |
| 11 | medical_drama | 医疗剧 | drama | 78.0 |
| 12 | sports | 体育竞技 | drama | 75.0 |
| 13 | food_culture | 美食文化 | romance | 76.0 |

### 7.2 修改文件清单

1. `data_extraction/seed_themes_final.json` - 扩展主题库
2. `backend/agents/story_planner.py` - 动态加载、去重集成
3. `prompts/2_Story_Planner.md` - 重构Prompt设计
4. `backend/services/market_analysis.py` - 优化搜索和缓存
5. `backend/skills/market_analysis/__init__.py` - 修复硬编码
6. `backend/services/plan_deduplication.py` - 新增去重服务
7. `backend/supabase/migrations/007_generated_plans_history.sql` - 新增表

### 7.3 测试检查清单

- [ ] 主题库扩展后数据正确加载
- [ ] 动态加载不影响性能
- [ ] 新Prompt生成质量达标
- [ ] 市场数据实时更新
- [ ] 去重机制准确识别重复
- [ ] 系统整体稳定性

---

**文档版本历史**
- v1.0 (2026-02-10): 初始版本，整合所有优化方案

**审批人**
- [ ] 技术负责人
- [ ] 产品经理
- [ ] 测试负责人
