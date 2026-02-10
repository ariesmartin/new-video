# Skeleton Builder 改革方案 - 完整实现文档

## 版本信息
- 版本：v2.0
- 日期：2026-02-09
- 状态：待实施

---

## 一、当前问题诊断

### 1.1 Token限制问题（严重）
**现状**：
- 默认 `max_tokens = 4096`（backend/services/model_router.py:188）
- Prompt文件 638 行，约 15,000-20,000 tokens
- 生成完整小说大纲需要 50+ 章节 × 每章500字 = 25,000+ tokens

**问题**：
- 4096 tokens 只能生成约 8-10 章内容，无法生成完整大纲
- 会导致输出被截断，JSON不完整

**解决方案**：
1. 增加 SKELETON_BUILDER 的 max_tokens 到 8192-16384
2. 实现分批次生成逻辑
3. 使用流式输出 + 拼接

### 1.2 缺少章节映射计算（严重）
**现状**：
- skeleton_builder_graph.py 中没有计算 chapter_map 的逻辑
- validate_input_node 只检查 ending_type，没有计算章节映射
- Prompt中提到的 `{chapter_map}`、`{total_chapters}` 等变量**从未被注入**

**问题**：
- Prompt中的变量都是空的
- 无法正确映射章节到短剧集数

**解决方案**：
1. 在 validate_input_node 中实现章节映射算法
2. 将计算结果注入到 prompt 中
3. 修改 skeleton_builder_node 传递计算参数

### 1.3 输出格式不匹配（中等）
**现状**：
- Prompt要求输出 8 个部分的详细内容
- 包括 50+ 章节的详细大纲
- 但当前实现期望输出 Ep.01-Ep.80 的分集大纲

**问题**：
- 输出解析器可能无法正确处理新格式
- UI交互JSON格式变更

**解决方案**：
1. 重写 output_formatter_node
2. 更新 UI 交互格式
3. 增加章节大纲解析逻辑

### 1.4 题材库工具使用（需验证）
**现状**：
- skeleton_builder.py:103-108 注册了4个题材库工具
- Tool使用原则要求"必须先调用 load_genre_context"
- 但无法验证Agent是否正确调用了Tools

**问题**：
- Agent可能不调用Tools直接生成
- 生成内容不符合题材规范

**解决方案**：
1. 在Prompt中添加强制调用指令
2. 在输出中要求标注使用的题材元素
3. 在Editor审阅时验证题材合规性

### 1.5 审阅流程适配（中等）
**现状**：
- Quality Control Graph 使用 Editor → Refiner 闭环
- Editor使用6大分类审阅标准
- 但审阅标准是基于短剧分集的

**问题**：
- 审阅标准可能不适用于章节大纲
- 需要验证Editor能否正确审阅章节格式

**解决方案**：
1. 更新 Editor Prompt 支持章节大纲审阅
2. 在审阅要点中增加"章节结构合理性"
3. 验证 Refiner 能否正确修改章节大纲

---

## 二、详细修改方案

### 2.1 文件修改清单

| 文件 | 修改类型 | 优先级 | 说明 |
|------|----------|--------|------|
| backend/services/model_config.py | 修改 | 高 | 增加 SKELETON_BUILDER 的默认max_tokens |
| backend/graph/workflows/skeleton_builder_graph.py | 大幅修改 | 高 | 添加章节映射计算，重写输出格式 |
| backend/agents/skeleton_builder.py | 修改 | 高 | 注入章节映射变量到prompt |
| backend/graph/workflows/quality_control_graph.py | 验证 | 中 | 确保Editor/Refiner支持章节格式 |
| prompts/3_Skeleton_Builder.md | 已修改 | 高 | 已修改为章节大纲格式 |
| prompts/7_Editor_Reviewer.md | 修改 | 中 | 更新审阅标准支持章节 |

### 2.2 修改详情

#### 修改1：增加Token限制（backend/services/model_config.py）

当前配置（约228行）：
```python
"parameters": {"temperature": 0.8, "max_tokens": 8192},  # skeleton_builder
```

建议修改为：
```python
"parameters": {"temperature": 0.88, "max_tokens": 16384},  # skeleton_builder - 需要生成长文本
```

**注意**：需要确认所使用的模型支持16384 tokens（如GPT-4 Turbo、Claude 3等）

#### 修改2：添加章节映射计算（backend/graph/workflows/skeleton_builder_graph.py）

在 validate_input_node 中添加计算逻辑：

```python
async def validate_input_node(state: AgentState) -> Dict[str, Any]:
    """
    输入验证 Node - 增强版：自动计算章节映射
    """
    user_config = state.get("user_config", {})
    selected_plan = state.get("selected_plan", {})
    
    # ... 原有验证逻辑 ...
    
    # ===== 新增：章节映射计算 =====
    total_episodes = user_config.get("total_episodes", 80)
    episode_duration = user_config.get("episode_duration", 2)
    paywall_design = selected_plan.get("paywall_design", {})
    paywall_episodes = parse_paywall_range(paywall_design.get("episode_range", "10-12"))
    
    # 计算小说总字数
    total_drama_minutes = total_episodes * episode_duration
    estimated_words = total_drama_minutes * 4000  # 1分钟短剧 ≈ 4000字
    
    # 计算章节映射
    chapter_map = calculate_chapter_episode_map(total_episodes, paywall_episodes)
    total_chapters = len(chapter_map)
    
    # 找到付费卡点章节
    paywall_chapter = None
    for i, ch in enumerate(chapter_map):
        if ch["episode_start"] <= paywall_episodes[0] <= ch["episode_end"]:
            paywall_chapter = i + 1
            break
    
    # 计算关键节点章节
    opening_end = max(3, int(total_chapters * 0.05))
    development_start = opening_end + 1
    development_end = int(total_chapters * 0.75)
    midpoint_chapter = int(total_chapters * 0.50)
    climax_chapter = int(total_chapters * 0.875)
    
    inferred_config = {
        "total_episodes": total_episodes,
        "total_drama_minutes": total_drama_minutes,
        "estimated_words": estimated_words,
        "total_chapters": total_chapters,
        "chapter_map": chapter_map,
        "paywall_chapter": paywall_chapter,
        "paywall_episodes": paywall_episodes,
        "opening_end": opening_end,
        "development_start": development_start,
        "development_end": development_end,
        "midpoint_chapter": midpoint_chapter,
        "climax_chapter": climax_chapter,
        "adaptation_ratio": round(total_episodes / total_chapters, 2),
    }
    
    return {
        "validation_status": "complete",
        "inferred_config": inferred_config,
        "current_stage": StageType.LEVEL_3,
        "last_successful_node": "validate_input",
    }


def calculate_chapter_episode_map(total_episodes: int, paywall_episodes: List[int]) -> List[Dict]:
    """
    计算章节到短剧的映射
    
    规则：
    - 开篇阶段（0-15%）：1章 ≈ 1-1.5集
    - 发展阶段（15-75%）：1章 ≈ 2集
    - 付费卡点章节：1章 ≈ 3集（确保有足够铺垫和爆发）
    - 高潮阶段（75-90%）：1章 ≈ 1集
    - 结局阶段（90-100%）：1章 ≈ 1-2集
    """
    chapter_map = []
    current_episode = 1
    
    # 开篇阶段（15%的集数）
    opening_episodes = max(3, int(total_episodes * 0.15))
    for i in range(opening_episodes):
        eps = 1.5 if i < 3 else 1
        chapter_map.append({
            "chapter_num": len(chapter_map) + 1,
            "episode_start": current_episode,
            "episode_end": min(int(current_episode + eps - 1), total_episodes),
            "word_count": 9000 if eps <= 1 else 8000,
            "stage": "opening",
            "is_paywall": False,
        })
        current_episode += eps
    
    # 发展阶段（到付费卡点前）
    while current_episode < paywall_episodes[0] - 2:
        chapter_map.append({
            "chapter_num": len(chapter_map) + 1,
            "episode_start": int(current_episode),
            "episode_end": min(int(current_episode + 1), total_episodes),
            "word_count": 10000,
            "stage": "development",
            "is_paywall": False,
        })
        current_episode += 2
    
    # 付费卡点章节（覆盖付费集数）
    paywall_end = paywall_episodes[-1]
    chapter_map.append({
        "chapter_num": len(chapter_map) + 1,
        "episode_start": int(current_episode),
        "episode_end": paywall_end,
        "word_count": 12000,  # 加长章节
        "stage": "paywall",
        "is_paywall": True,
        "paywall_hook": "付费卡点钩子事件",
    })
    current_episode = paywall_end + 1
    
    # 发展阶段（付费卡点后到75%）
    development_end_ep = int(total_episodes * 0.75)
    while current_episode < development_end_ep:
        chapter_map.append({
            "chapter_num": len(chapter_map) + 1,
            "episode_start": int(current_episode),
            "episode_end": min(int(current_episode + 1), total_episodes),
            "word_count": 10000,
            "stage": "development",
            "is_paywall": False,
        })
        current_episode += 2
    
    # 高潮阶段（75-90%）
    climax_end_ep = int(total_episodes * 0.90)
    while current_episode < climax_end_ep:
        chapter_map.append({
            "chapter_num": len(chapter_map) + 1,
            "episode_start": int(current_episode),
            "episode_end": int(current_episode),
            "word_count": 8000,
            "stage": "climax",
            "is_paywall": False,
        })
        current_episode += 1
    
    # 结局阶段（90-100%）
    while current_episode <= total_episodes:
        remaining = total_episodes - current_episode + 1
        eps = min(remaining, 2)
        chapter_map.append({
            "chapter_num": len(chapter_map) + 1,
            "episode_start": int(current_episode),
            "episode_end": min(int(current_episode + eps - 1), total_episodes),
            "word_count": 8000 if eps == 1 else 10000,
            "stage": "ending",
            "is_paywall": False,
        })
        current_episode += eps
    
    return chapter_map


def parse_paywall_range(range_str: str) -> List[int]:
    """解析付费卡点范围字符串"10-12" -> [10, 11, 12]"""
    if "-" in range_str:
        start, end = range_str.split("-")
        return list(range(int(start), int(end) + 1))
    else:
        return [int(range_str)]
```

#### 修改3：注入变量到Prompt（backend/agents/skeleton_builder.py）

修改 _load_skeleton_builder_prompt 函数：

```python
async def _load_skeleton_builder_prompt(
    selected_plan: Dict,
    user_config: Dict,
    market_report: Optional[Dict] = None,
    inferred_config: Optional[Dict] = None,  # 新增参数
) -> str:
    """从文件加载 Skeleton Builder 的 System Prompt - 增强版"""
    prompt_path = Path(__file__).parent.parent.parent / "prompts" / "3_Skeleton_Builder.md"

    try:
        with open(prompt_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 基础变量替换
        content = content.replace("{total_episodes}", str(user_config.get("total_episodes", 80)))
        content = content.replace("{episode_duration}", str(user_config.get("episode_duration", 2)))
        content = content.replace("{genre}", user_config.get("genre", "revenge"))
        content = content.replace("{setting}", user_config.get("setting", "modern"))
        content = content.replace("{ending}", user_config.get("ending", "HE"))
        content = content.replace("{selected_plan}", str(selected_plan))
        content = content.replace("{user_config}", str(user_config))

        # 新增：章节映射变量替换
        if inferred_config:
            content = content.replace("{total_words}", str(inferred_config.get("estimated_words", 800000)))
            content = content.replace("{total_chapters}", str(inferred_config.get("total_chapters", 61)))
            content = content.replace("{paywall_chapter}", str(inferred_config.get("paywall_chapter", 12)))
            content = content.replace("{paywall_episodes}", str(inferred_config.get("paywall_episodes", [12])))
            content = content.replace("{chapter_map}", str(inferred_config.get("chapter_map", [])))
            content = content.replace("{ratio}", str(inferred_config.get("adaptation_ratio", 1.31)))
            content = content.replace("{total_drama_minutes}", str(inferred_config.get("total_drama_minutes", 160)))
            content = content.replace("{opening_end}", str(inferred_config.get("opening_end", 3)))
            content = content.replace("{development_start}", str(inferred_config.get("development_start", 4)))
            content = content.replace("{development_end}", str(inferred_config.get("development_end", 45)))
            content = content.replace("{midpoint_chapter}", str(inferred_config.get("midpoint_chapter", 31)))
            content = content.replace("{climax_chapter}", str(inferred_config.get("climax_chapter", 53)))
            content = content.replace("{final_chapter}", str(inferred_config.get("total_chapters", 61)))
            content = content.replace("{paywall_position}", str(round(inferred_config.get("paywall_chapter", 12) / inferred_config.get("total_chapters", 61) * 100, 1)))
        else:
            # 默认值
            content = content.replace("{total_words}", "800000")
            content = content.replace("{total_chapters}", "61")
            content = content.replace("{paywall_chapter}", "12")
            content = content.replace("{paywall_episodes}", "[12]")
            content = content.replace("{chapter_map}", "[]")
            content = content.replace("{ratio}", "1.31")

        if market_report:
            content = content.replace("{market_report}", str(market_report))
        else:
            content = content.replace("{market_report}", "未提供")

        logger.info("Skeleton Builder Prompt loaded", prompt_length=len(content))
        return content

    except Exception as e:
        logger.error("Failed to load Skeleton Builder prompt", error=str(e))
        return "You are a skeleton builder agent. Generate a story outline based on the input."
```

#### 修改4：修改 skeleton_builder_node 调用（backend/agents/skeleton_builder.py）

```python
async def skeleton_builder_node(state: Dict) -> Dict:
    """
    Skeleton Builder Node 包装器 - 增强版
    """
    from backend.schemas.agent_state import AgentState

    user_id = state.get("user_id")
    project_id = state.get("project_id")
    selected_plan = state.get("selected_plan", {})
    user_config = state.get("user_config", {})
    market_report = state.get("market_report")
    messages = state.get("messages", [])
    
    # 获取计算的章节映射配置
    inferred_config = state.get("inferred_config", {})

    logger.info(
        "Executing Skeleton Builder Node",
        user_id=user_id,
        message_count=len(messages),
        total_chapters=inferred_config.get("total_chapters"),
    )

    try:
        # 创建 Agent - 传递 inferred_config
        agent = await create_skeleton_builder_agent(
            user_id=user_id,
            project_id=project_id,
            selected_plan=selected_plan,
            user_config=user_config,
            market_report=market_report,
            inferred_config=inferred_config,  # 新增
        )

        # ... 其余代码保持不变 ...

    except Exception as e:
        logger.error("Skeleton Builder Node failed", error=str(e))
        return {
            "error": f"大纲生成失败: {str(e)}",
            "last_successful_node": "skeleton_builder_error",
        }
```

### 2.3 长输出处理方案

由于完整的大纲可能超过 16384 tokens，建议采用以下策略：

#### 方案A：单次长输出（推荐用于支持长上下文的模型）
- 使用支持 32K+ tokens 的模型（GPT-4 Turbo、Claude 3 Opus等）
- 设置 max_tokens = 16384
- 在Prompt中明确要求"详细但简洁，避免冗余描述"

#### 方案B：分批次生成（备用方案）
如果必须使用 4K/8K 模型：
1. 第一批：生成元数据+核心设定+人物体系
2. 第二批：生成情节架构+前20章大纲
3. 第三批：生成中间章节大纲
4. 第四批：生成高潮+结局章节+映射表

实现方式：在 skeleton_builder_graph 中增加分批节点

---

## 三、质量保证措施

### 3.1 Prompt质量保证

1. **强制题材库调用**：
   - 在Prompt中添加："你必须先调用 load_genre_context 工具"
   - 在输出中要求："列出本章使用的题材元素"

2. **输出格式验证**：
   - 使用 JSON Schema 验证输出结构
   - 确保所有章节都包含必要字段

3. **一致性检查**：
   - 验证人物弧光在章节间的一致性
   - 验证伏笔都有回收计划

### 3.2 Editor审阅更新

需要更新 prompts/7_Editor_Reviewer.md：
- 增加"章节结构合理性"审阅维度
- 验证章节-短剧映射的准确性
- 检查每章是否都有核心冲突和钩子

### 3.3 错误处理

1. **Token超限**：
   - 捕获 token limit 错误
   - 自动切换到分批生成模式

2. **输出不完整**：
   - 检测 JSON 是否完整
   - 不完整时要求 LLM 继续生成

3. **格式错误**：
   - 使用结构化输出（如 function calling）
   - 添加格式验证和重试逻辑

---

## 四、实施计划

### Phase 1：基础设施（1-2天）
1. [ ] 修改 model_config.py 增加 token 限制
2. [ ] 实现章节映射计算算法
3. [ ] 修改 skeleton_builder.py 支持变量注入

### Phase 2：Prompt优化（1天）
1. [ ] 优化 3_Skeleton_Builder.md（已修改，需验证）
2. [ ] 更新 7_Editor_Reviewer.md 支持章节审阅
3. [ ] 添加强制工具调用指令

### Phase 3：测试验证（2-3天）
1. [ ] 单元测试：章节映射算法
2. [ ] 集成测试：完整大纲生成
3. [ ] 质量测试：Editor审阅章节大纲
4. [ ] Token测试：验证不同模型下的输出完整性

### Phase 4：部署上线（1天）
1. [ ] 配置生产环境模型映射
2. [ ] 监控生成质量和Token使用
3. [ ] 收集反馈迭代优化

---

## 五、风险评估

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|----------|
| Token不足导致输出截断 | 高 | 高 | 增加max_tokens；实现分批生成 |
| 模型不支持长上下文 | 中 | 高 | 使用Claude 3/GPT-4 Turbo；分批生成 |
| 生成内容质量下降 | 中 | 高 | 强化Editor审阅；增加质量门控 |
| 计算逻辑错误 | 低 | 高 | 单元测试；边界条件验证 |
| 性能下降（生成时间变长） | 中 | 中 | 使用checkpoint；流式输出 |

---

## 六、成功标准

1. **功能完整性**：
   - ✅ 能生成包含50+章节的完整小说大纲
   - ✅ 每章都有详细的创作指导
   - ✅ 正确映射到短剧集数
   - ✅ 包含付费卡点专项设计

2. **质量指标**：
   - Editor审阅评分 ≥ 80分
   - 用户满意度 ≥ 4.5/5
   - 生成成功率 ≥ 95%

3. **性能指标**：
   - 单次生成时间 < 120秒
   - Token使用效率 > 70%（不浪费）
   - 支持checkpoint恢复

---

## 七、附录

### A. 参考配置示例

**模型配置（model_config.py）**：
```python
TaskType.SKELETON_BUILDER: {
    "provider": "anthropic",
    "model": "claude-3-opus-20240229",
    "parameters": {
        "temperature": 0.88,
        "max_tokens": 16384
    }
}
```

**测试用例**：
- 80集短剧 → 应生成约61章，80万字
- 付费卡点第12集 → 应映射到第12章
- 每章字数范围：8000-12000字

### B. 监控指标

- 平均生成token数
- 输出截断率
- Editor评分分布
- 用户修改率（大纲确认后修改的频率）

---

**文档编制完成，等待实施。**
