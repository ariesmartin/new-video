# 方案到大纲数据流失问题跟踪文档

**创建时间**: 2026-02-11
**问题描述**: 用户选择的方案（九洲死线）与生成的大纲（万劫成凰）完全不匹配
**状态**: 🔴 紧急修复中

---

## 📊 问题汇总

| 编号 | 问题 | 优先级 | 状态 | 位置 |
|------|------|--------|------|------|
| P0-1 | 方案内容未保存到数据库 | P0 | 🔴 待修复 | main_graph.py |
| P0-2 | 正则提取方案内容失败 | P0 | 🔴 待修复 | main_graph.py:74-146 |
| P0-3 | 验证节点缺少数据库回退 | P0 | 🔴 待修复 | skeleton_builder_graph.py:382 |
| P0-4 | Skeleton Builder Node 无硬检查 | P0 | 🔴 待修复 | skeleton_builder.py:243 |
| P1-1 | State 字段缺少 Reducer | P1 | 🟡 待修复 | agent_state.py:241-242 |
| P1-2 | Prompt 未强化方案引用 | P1 | 🟡 待修复 | skeleton_builder.py:305-404 |
| P2-1 | 分批指令无方案约束 | P2 | 🟢 待修复 | skeleton_builder.py:307 |

---

## 🔴 P0-1: 方案内容未保存到数据库

### 问题描述
数据库验证发现 `story_plans` 表为空（0条记录），说明方案数据根本没有保存到数据库。

### 验证结果
```sql
-- 查询结果
story_plans: 0 条记录 ❌
generated_plans_history: 0 条记录 ❌
projects: 2 条记录 ✅
```

### 根本原因
1. 保存操作使用 `db._client.patch/post` 直接调用 REST API
2. 如果失败只记录 warning 日志，不会阻止流程继续
3. 可能的原因：
   - API 端点不正确
   - 权限问题（RLS 策略）
   - 表结构不匹配
   - 网络连接问题

### 修复方案

**文件**: `backend/graph/main_graph.py`

```python
async def _save_selected_plan_to_db(project_id, user_id, selected_plan, user_config):
    """保存方案到数据库，带完整错误处理和验证"""
    try:
        from backend.services.database import get_db_service
        import httpx
        
        db = get_db_service()
        plan_id = selected_plan.get("id")
        plan_title = selected_plan.get("title")
        plan_content = selected_plan.get("content", "")
        
        # 验证内容不为空
        if not plan_content or len(plan_content) < 100:
            logger.error(
                "Attempting to save plan with empty or too short content",
                plan_id=plan_id,
                content_length=len(plan_content) if plan_content else 0,
            )
            return False, "方案内容为空或太短"
        
        plan_data_json = {
            "content": plan_content,
            "title": plan_title,
            "label": selected_plan.get("label", ""),
            "plan_id": plan_id,
        }
        
        # 检查是否已存在
        existing = await db.get_plan(plan_id)
        
        if existing:
            # 更新现有方案
            response = await db._client.patch(
                f"{db._rest_url}/story_plans",
                params={"plan_id": f"eq.{existing['plan_id']}"},
                json={
                    "is_selected": True,
                    "plan_data": plan_data_json,
                    "updated_at": "now()",
                },
            )
            response.raise_for_status()
            logger.info("Updated existing plan in database", plan_id=plan_id)
        else:
            # 创建新方案
            response = await db._client.post(
                f"{db._rest_url}/story_plans",
                json={
                    "project_id": project_id,
                    "user_id": user_id,
                    "title": plan_title,
                    "description": selected_plan.get("label", ""),
                    "genre": user_config.get("genre"),
                    "is_selected": True,
                    "status": "active",
                    "plan_data": plan_data_json,
                },
            )
            response.raise_for_status()
            logger.info("Created new plan in database", plan_id=plan_id)
        
        # 验证保存成功
        saved = await db.get_selected_plan(project_id)
        if saved and saved.get("plan_data", {}).get("content"):
            saved_content_length = len(saved["plan_data"]["content"])
            if saved_content_length >= len(plan_content) * 0.9:  # 允许10%的差异
                logger.info(
                    "✅ Plan saved and verified in database",
                    plan_id=plan_id,
                    content_length=saved_content_length,
                )
                return True, None
            else:
                logger.error(
                    "Plan saved but content length mismatch",
                    expected=len(plan_content),
                    actual=saved_content_length,
                )
                return False, "方案保存后内容长度不匹配"
        else:
            logger.error("Plan saved but content not found in database")
            return False, "方案保存后数据库中找不到内容"
            
    except httpx.HTTPStatusError as e:
        logger.error(
            "Failed to save plan - HTTP error",
            status_code=e.response.status_code,
            response=e.response.text,
            error=str(e),
        )
        return False, f"HTTP错误 {e.response.status_code}: {e.response.text}"
    except Exception as e:
        logger.error("Failed to save plan", error=str(e), exc_info=True)
        return False, f"保存失败: {str(e)}"
```

### 在 _story_planner_node 中使用

```python
# 在构建 selected_plan 后，返回前
# 尝试保存到数据库
save_success, error_msg = await _save_selected_plan_to_db(
    project_id, user_id, selected_plan, user_config
)

if not save_success:
    # 保存失败，返回错误而不是继续
    logger.error("Failed to save plan, returning error to user", error=error_msg)
    return {
        "messages": [
            AIMessage(
                content=f"❌ 保存方案失败：{error_msg}\n\n请检查数据库连接或联系管理员。"
            )
        ],
        "error": f"Failed to save plan to database: {error_msg}",
        "last_successful_node": "story_planner_save_failed",
    }
```

### 验证方法
1. 重新运行故事策划流程
2. 检查数据库中是否有新记录
3. 验证 plan_data->>'content' 不为空

---

## 🔴 P0-2: 正则提取方案内容失败

### 问题描述
`_extract_plan_content()` 函数使用正则表达式从 markdown 中提取方案内容，但 LLM 生成的格式可能不匹配，导致提取失败返回空字符串。

### 当前代码
```python
# backend/graph/main_graph.py:104-110
plan_pattern = rf"###\s*方案\s*{re.escape(plan_id)}\s*[:：]"
match = re.search(plan_pattern, story_plans_markdown)

if not match:
    # 备选：尝试不带冒号的匹配
    plan_pattern_alt = rf"###\s*方案\s*{re.escape(plan_id)}\b"
    match = re.search(plan_pattern_alt, story_plans_markdown)

if not match:
    return ""  # ❌ 返回空字符串
```

### 修复方案

**文件**: `backend/graph/main_graph.py`

```python
def _extract_plan_content(story_plans_markdown: str, plan_id: str) -> str:
    """增强版方案内容提取 - 支持多种格式变体"""
    if not story_plans_markdown or not plan_id:
        logger.warning(
            "Cannot extract plan content: missing data",
            has_markdown=bool(story_plans_markdown),
            plan_id=plan_id,
        )
        return ""

    # 统一为字符串
    if not isinstance(story_plans_markdown, str):
        story_plans_markdown = _content_to_string(story_plans_markdown)

    # 多种匹配模式（从严格到宽松）
    patterns = [
        # 标准格式
        (rf"###\s*方案\s*{re.escape(plan_id)}\s*[:：]", "strict"),
        (rf"###\s*方案\s*{re.escape(plan_id)}\b", "no_colon"),
        # 二级标题
        (rf"##\s*方案\s*{re.escape(plan_id)}\s*[:：]", "h2_colon"),
        (rf"##\s*方案\s*{re.escape(plan_id)}\b", "h2_no_colon"),
        (rf"##\s*方案{re.escape(plan_id)}\s*[:：]", "h2_nospace"),
        # 粗体格式
        (rf"\*\*方案\s*{re.escape(plan_id)}[:：]", "bold"),
        (rf"\*\*{re.escape(plan_id)}[:：]", "bold_id_only"),
        # 无标记格式
        (rf"方案\s*{re.escape(plan_id)}[:：]", "no_markdown"),
        # 英文格式
        (rf"Plan\s*{re.escape(plan_id)}[:：]", "english"),
        (rf"Option\s*{re.escape(plan_id)}[:：]", "option"),
    ]
    
    match = None
    matched_pattern_name = None
    
    for pattern, name in patterns:
        match = re.search(pattern, story_plans_markdown, re.IGNORECASE)
        if match:
            matched_pattern_name = name
            logger.info(
                "Matched plan pattern",
                plan_id=plan_id,
                pattern=name,
                pattern_regex=pattern[:50],
            )
            break
    
    if not match:
        logger.error(
            "Plan content extraction failed - no pattern matched",
            plan_id=plan_id,
            markdown_preview=story_plans_markdown[:1000],
            available_patterns=[name for _, name in patterns],
        )
        # 降级策略：尝试找到任何包含 plan_id 的段落
        return _extract_plan_content_fallback(story_plans_markdown, plan_id)

    start = match.start()
    remaining = story_plans_markdown[match.end():]
    
    # 查找结束标记
    end_patterns = [
        r"###\s*方案\s*[A-Za-z]",  # 下一个方案
        r"##\s*方案\s*[A-Za-z]",   # 下一个方案（h2）
        r"📊\s*方案对比",          # 方案对比表
        r"```json",                 # JSON 数据块
        r"---\s*\n\s*###",         # 分隔线后的新标题
    ]
    
    end_offset = len(remaining)
    for pattern in end_patterns:
        end_match = re.search(pattern, remaining)
        if end_match and end_match.start() < end_offset:
            end_offset = end_match.start()

    # 提取内容
    content = story_plans_markdown[start:match.end() + end_offset]
    content = re.sub(r"\n---\s*$", "", content.rstrip())
    
    # 验证提取结果
    if len(content) < 200:
        logger.warning(
            "Extracted content suspiciously short",
            plan_id=plan_id,
            pattern=matched_pattern_name,
            content_length=len(content),
            content_preview=content[:200],
        )
        # 尝试降级提取
        fallback_content = _extract_plan_content_fallback(story_plans_markdown, plan_id)
        if len(fallback_content) > len(content):
            return fallback_content
    else:
        logger.info(
            "✅ Successfully extracted plan content",
            plan_id=plan_id,
            pattern=matched_pattern_name,
            content_length=len(content),
        )
    
    return content


def _extract_plan_content_fallback(story_plans_markdown: str, plan_id: str) -> str:
    """降级提取策略：使用更宽松的方法"""
    # 查找包含 plan_id 的大段落
    paragraphs = story_plans_markdown.split('\n\n')
    
    for i, para in enumerate(paragraphs):
        if plan_id in para and len(para) > 100:
            # 找到匹配的段落，收集后续段落直到遇到明显的分隔
            content_parts = [para]
            for j in range(i + 1, len(paragraphs)):
                next_para = paragraphs[j]
                # 如果遇到新方案或明显分隔，停止
                if re.match(r"^(#{1,3}\s*|\*\*|方案\s+[A-Z]|Plan\s+[A-Z])", next_para):
                    break
                content_parts.append(next_para)
            
            content = '\n\n'.join(content_parts)
            logger.info(
                "Fallback extraction successful",
                plan_id=plan_id,
                content_length=len(content),
            )
            return content
    
    logger.error("Fallback extraction also failed", plan_id=plan_id)
    return ""
```

### 验证方法
1. 使用测试数据验证正则匹配
2. 添加单元测试覆盖各种格式变体
3. 在开发环境模拟 LLM 不同输出格式

---

## 🔴 P0-3: 验证节点缺少数据库回退

### 问题描述
`validate_input_node()` 只从 state 读取 `selected_plan`，如果 checkpoint 没有恢复成功，不会尝试从数据库加载。

### 当前代码
```python
# backend/graph/workflows/skeleton_builder_graph.py:382-420
async def validate_input_node(state: AgentState) -> Dict[str, Any]:
    selected_plan = state.get("selected_plan", {})  # ❌ 只从 state 读取
    
    if not selected_plan:
        missing_fields.append("selected_plan")  # ❌ 没有 DB 回退
```

### 修复方案

**文件**: `backend/graph/workflows/skeleton_builder_graph.py`

```python
async def validate_input_node(state: AgentState) -> Dict[str, Any]:
    """
    输入验证 Node - 增强版（带数据库回退）
    """
    user_config = state.get("user_config", {})
    selected_plan = state.get("selected_plan", {})
    project_id = state.get("project_id")
    
    # ===== 新增：从数据库回退加载 =====
    if not selected_plan and project_id:
        logger.warning(
            "selected_plan not in state, attempting to load from database",
            project_id=project_id,
        )
        try:
            from backend.services.database import get_db_service
            import json
            
            db = get_db_service()
            saved_plan = await db.get_selected_plan(project_id)
            
            if saved_plan:
                # 解析 plan_data
                plan_data = saved_plan.get("plan_data", {})
                if isinstance(plan_data, str):
                    try:
                        plan_data = json.loads(plan_data)
                    except json.JSONDecodeError:
                        plan_data = {}
                
                selected_plan = {
                    "id": saved_plan.get("plan_id"),
                    "title": saved_plan.get("title"),
                    "label": plan_data.get("label", ""),
                    "content": plan_data.get("content", ""),
                }
                
                # 更新 state 供后续节点使用
                state["selected_plan"] = selected_plan
                
                logger.info(
                    "✅ Successfully loaded selected_plan from database",
                    plan_id=saved_plan.get("plan_id"),
                    title=saved_plan.get("title"),
                    has_content=bool(selected_plan.get("content")),
                )
            else:
                logger.error(
                    "No selected plan found in database",
                    project_id=project_id,
                )
        except Exception as e:
            logger.error(
                "Failed to load selected_plan from database",
                project_id=project_id,
                error=str(e),
            )
    
    # 检查必要字段（包括 content）
    missing_fields = []
    validation_errors = []
    
    if not selected_plan:
        missing_fields.append("selected_plan")
        validation_errors.append("未找到选中的方案")
    else:
        # 检查 content 是否为空
        content = selected_plan.get("content", "")
        if not content:
            missing_fields.append("selected_plan.content")
            validation_errors.append("选中方案的内容为空")
        elif len(content) < 100:
            missing_fields.append("selected_plan.content_too_short")
            validation_errors.append(f"选中方案的内容太短（{len(content)}字符）")
    
    # 检查 ending_type
    ending_type = user_config.get("ending_type") if isinstance(user_config, dict) else None
    if not ending_type:
        missing_fields.append("ending_type")
        validation_errors.append("未选择结局类型（HE/BE/OE）")
    
    if missing_fields:
        error_msg = "; ".join(validation_errors)
        logger.error(
            "Input validation failed",
            project_id=project_id,
            missing_fields=missing_fields,
            errors=validation_errors,
        )
        return {
            "validation_status": "incomplete",
            "missing_fields": missing_fields,
            "error": error_msg,
            "last_successful_node": "validate_input_failed",
            "messages": [HumanMessage(content=f"❌ 验证失败：{error_msg}")],
        }
    
    # 验证通过，继续原有逻辑...
    # [原有代码保持不变]
```

### 验证方法
1. 删除 checkpoint 记录后重新运行
2. 验证是否能从数据库恢复
3. 检查空 content 是否被正确拦截

---

## 🔴 P0-4: Skeleton Builder Node 无硬检查

### 问题描述
`skeleton_builder_node()` 接受空字典 `{}` 继续执行，没有任何断言或检查。

### 当前代码
```python
# backend/agents/skeleton_builder.py:243-260
async def skeleton_builder_node(state: Dict) -> Dict:
    selected_plan = state.get("selected_plan") or {}  # ❌ 接受空字典
    # 没有任何检查，继续执行...
```

### 修复方案

**文件**: `backend/agents/skeleton_builder.py`

```python
async def skeleton_builder_node(state: Dict) -> Dict:
    """
    Skeleton Builder Node 包装器 - 分批生成版（带硬检查）
    """
    from backend.schemas.agent_state import AgentState
    from langchain_core.messages import HumanMessage, AIMessage
    
    user_id = state.get("user_id")
    project_id = state.get("project_id")
    selected_plan = state.get("selected_plan") or {}
    user_config = state.get("user_config") or {}
    
    # ===== 硬检查：验证 selected_plan 有效性 =====
    validation_errors = []
    
    if not selected_plan:
        validation_errors.append("未找到选中的方案（selected_plan 为空）")
    else:
        plan_id = selected_plan.get("id")
        plan_title = selected_plan.get("title", "未知")
        plan_content = selected_plan.get("content", "")
        
        if not plan_id:
            validation_errors.append("方案 ID 为空")
        
        if not plan_content:
            validation_errors.append(f"方案 '{plan_title}' 的内容为空")
        elif len(plan_content) < 200:
            validation_errors.append(
                f"方案 '{plan_title}' 的内容太短（{len(plan_content)}字符，需要至少200字符）"
            )
        
        # 记录方案信息用于调试
        logger.info(
            "Skeleton builder received plan",
            plan_id=plan_id,
            plan_title=plan_title,
            content_length=len(plan_content) if plan_content else 0,
        )
    
    if validation_errors:
        error_msg = "; ".join(validation_errors)
        logger.error(
            "Skeleton builder validation failed - cannot generate outline",
            project_id=project_id,
            errors=validation_errors,
        )
        return {
            "error": f"无法生成大纲：{error_msg}",
            "last_successful_node": "skeleton_builder_validation_failed",
            "messages": [
                AIMessage(
                    content=f"❌ **无法生成大纲**\n\n{error_msg}\n\n"
                    f"请先完成故事策划并选择有效的方案。"
                )
            ],
            # 阻止继续生成
            "skeleton_content": None,
            "validation_status": "failed",
        }
    
    # 验证通过，继续原有逻辑...
    # [原有代码保持不变]
```

### 验证方法
1. 传入空 selected_plan 测试是否被拦截
2. 传入 content 为空的方案测试是否报错
3. 验证返回的错误消息是否清晰

---

## 🟡 P1-1: State 字段缺少 Reducer

### 问题描述
`selected_plan` 和 `story_plans` 字段没有定义 Reducer，使用 LangGraph 默认行为，可能被意外覆盖。

### 修复方案

**文件**: `backend/schemas/agent_state.py`

```python
# 添加 Reducer 函数
def merge_selected_plan(
    existing: dict | None, new: dict | None
) -> dict | None:
    """合并 selected_plan - 新值优先，但保留重要字段"""
    if new is None:
        return existing
    if existing is None:
        return new
    
    # 合并两个字典，新值优先
    result = dict(existing)
    result.update(new)
    
    # 特别保护：如果新值没有 content 但旧值有，保留旧值
    if not new.get("content") and existing.get("content"):
        result["content"] = existing["content"]
        logger.warning(
            "Preserving existing plan content during merge",
            existing_content_length=len(existing["content"]),
        )
    
    return result


# 在 AgentState 中使用 Annotated
class AgentState(TypedDict, total=False):
    # ... 其他字段 ...
    
    # Level 2: Story Planning
    story_plans: Annotated[list[StoryPlan], lambda x, y: y if y is not None else x]  # 简单替换策略
    selected_plan: Annotated[dict | None, merge_selected_plan]  # 使用自定义 Reducer
```

---

## 🟡 P1-2: Prompt 未强化方案引用

### 修复方案

**文件**: `backend/agents/skeleton_builder.py`

```python
# 在第一批指令中显式引用方案
if is_first_batch:
    plan_title = selected_plan.get("title", "未指定")
    plan_content = selected_plan.get("content", "")
    
    batch_instruction = f"""【第1批：完整骨架 - 章节清单模式】

⚠️ **重要提醒**：必须严格基于以下用户选中的方案构建大纲

**选中方案标题**：{plan_title}
**方案ID**：{selected_plan.get("id", "未知")}

**方案核心内容**（前1500字）：
```
{plan_content[:1500] if plan_content else "【警告：方案内容为空】"}
```

**约束要求**：
1. 必须严格遵循上述方案的题材、人设、核心冲突
2. 不得偏离方案中的故事主线和世界观设定
3. 人物名称、背景设定必须与方案一致
4. 付费卡点设计必须与方案中的设计一致

---
本次生成任务：构建完整的故事大纲骨架
...
"""
```

---

## 📋 修复实施检查清单

### Phase 1: P0 紧急修复
- [ ] P0-1: 添加方案保存验证和错误处理
- [ ] P0-2: 增强正则提取健壮性
- [ ] P0-3: 添加数据库回退到验证节点
- [ ] P0-4: 添加硬检查到 Skeleton Builder Node

### Phase 2: P1 重要修复
- [ ] P1-1: 为 State 字段添加 Reducer
- [ ] P1-2: 在 Prompt 中强化方案引用

### Phase 3: P2 优化
- [ ] P2-1: 优化分批生成指令

### 验证步骤
- [ ] 验证数据库中有方案记录
- [ ] 验证方案内容不为空
- [ ] 验证大纲生成遵循方案
- [ ] 验证空方案被正确拦截
- [ ] 验证 checkpoint 恢复失败时有 DB 回退

---

## 🚀 下一步行动

1. **立即实施 P0-1**（方案保存验证）- 这是根本问题
2. **然后实施 P0-4**（硬检查）- 防止继续生成错误内容
3. **最后实施 P0-2 和 P0-3**（增强健壮性）

准备好开始修复了吗？
