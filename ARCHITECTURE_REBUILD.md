# AI 短剧台 - LangGraph 后端重构架构文档

## 文档信息

| 项目 | 内容 |
|------|------|
| 文档名称 | Backend Rebuild Architecture (后端重构架构) |
| 版本号 | v4.0.2 |
| 创建日期 | 2026-02-06 |
| 最后更新 | 2026-02-06 |
| 构建状态 | Step 3 完成，Celery + 缓存系统已修复 |
| 目标 | 基于 LangChain Agent Skill 架构重构 |

---

## 重构背景

### 为什么重构？

旧后端存在以下问题，需要从头构建 LangGraph 核心：
1. **架构错误** - 使用传统节点函数而非 Agent 架构，无法发挥 LangChain 能力
2. **Tool 调用混乱** - 手动处理 Tool Calling，容易出错
3. **路由逻辑不清晰** - Master Router 和直接跳转逻辑冲突
4. **消息丢失问题** - UI 按钮在状态转换时丢失
5. **缺乏测试覆盖** - 关键路径未经充分验证

### 重构策略 (v4.0)

- **✅ 保留** - `services/`, `tools/`, `schemas/` - 基础设施已就绪
- **🔄 重建** - `graph/agents/`, `graph/subgraphs/`, `main_graph.py` - Agent 架构
- **🗑️ 删除** - `graph/nodes/` - 旧传统节点实现已删除
- **✅ 逐步验证** - 每个 Agent 都有独立测试

---

## 架构核心：Multi-Agent System

### Agent vs 传统节点函数

```
❌ 旧做法 (已删除):
async def market_analyst_node(state: AgentState) -> dict:
    model = get_model()
    response = await model.ainvoke(messages)  # 单轮调用
    return parse_response(response)           # 手动解析

✅ 新做法 (Agent 架构):
market_analyst_agent = create_react_agent(
    model=ChatOpenAI(model="gpt-4o"),
    tools=[metaso_search, trend_analyzer],     # Agent 自主决定调用
    state_modifier=MARKET_ANALYST_PROMPT,      # System Prompt 定义职责
)
# Agent 自主决定：是否调用 Tool → 调用哪个 → 如何处理结果 → 何时返回
```

### Agent 架构图

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Master Router Agent                             │
│  (意图识别 → 上下文构建 → Agent 路由 → SDUI 生成)                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
           ┌──────────────────────────┼──────────────────────────┐
           │                          │                          │
           ▼                          ▼                          ▼
┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐
│ Market Analyst      │  │ Story Planner       │  │ Skeleton Builder    │
│ Agent               │  │ Agent               │  │ Agent               │
│                     │  │                     │  │                     │
│ Tools:              │  │ Tools:              │  │ Tools:              │
│ - metaso_search     │  │ - genre_matcher     │  │ - character_db      │
│ - trend_analyzer    │  │ - plot_generator    │  │ - beat_planner      │
└──────────┬──────────┘  └──────────┬──────────┘  └──────────┬──────────┘
           │                          │                          │
           └──────────────────────────┼──────────────────────────┘
                                      │
                         ┌────────────▼────────────┐
                         │    Module A Subgraph    │
                         │  ┌─────────────────┐    │
                         │  │ Novel Writer    │    │
                         │  │   Agent         │    │
                         │  └────────┬────────┘    │
                         │           ▼             │
                         │  ┌─────────────────┐    │
                         │  │ Content Editor  │    │
                         │  │   Agent         │    │
                         │  └────────┬────────┘    │
                         │           ▼             │
                         │  ┌─────────────────┐    │
                         │  │ Content Refiner │    │
                         │  │   Agent         │    │
                         │  └─────────────────┘    │
                         └─────────────────────────┘
```

---

## 当前构建状态

### ✅ Step 1: 数据骨架 (已完成)

**文件**:
- `backend/schemas/agent_state.py` - AgentState TypedDict
- `backend/schemas/common.py` - SDUI 协议

**状态**: ✅ 无需修改

---

### ✅ Step 2: 基础设施层 (已完成)

**文件**:
```
backend/graph/
├── checkpointer.py           # ✅ AsyncPostgresSaver + 连接池
└── __init__.py

backend/test_checkpointer.py   # ✅ 4/4 测试通过
```

**实现细节**:
- `AsyncPostgresSaver` 从 `langgraph.checkpoint.postgres.aio`
- 连接池: `min_size=2, max_size=10`
- 测试通过率: 100%

**⚠️ 关键实现要点 - Checkpoint 正确使用**:

在使用 `AsyncPostgresSaver` 保存状态时，`channel_versions` 必须与 `new_versions` 匹配，否则状态恢复会失败。

```python
# ❌ 错误做法 (导致状态无法恢复):
checkpoint = {
    "v": 1,
    "channel_values": {"messages": [...], "ui_interaction": {...}},
    "channel_versions": {},  # 空 dict - 导致 SQL JOIN 失败！
}
new_versions = {"messages": 1, "ui_interaction": 1}
await checkpointer.aput(config, checkpoint, metadata, new_versions)

# ✅ 正确做法 (channel_versions 必须匹配 new_versions):
new_versions = {
    "messages": 1,
    "ui_interaction": 1,
}

checkpoint = {
    "v": 1,
    "ts": datetime.now().isoformat(),
    "id": str(uuid.uuid4()),
    "channel_values": {
        "messages": serializable_messages,  # list 类型
        "ui_interaction": ui_interaction_dict,  # dict 类型
        "is_cold_start": True,  # 基础类型直接存储
    },
    "channel_versions": {k: str(v) for k, v in new_versions.items()},
    # 结果: {"messages": "1", "ui_interaction": "1"}
    "versions_seen": {},
}

await checkpointer.aput(config, checkpoint, metadata, new_versions)
```

**工作原理**:
1. `aput()` 将 list/dict 类型的 channel values 存储到 `checkpoint_blobs` 表
2. `channel_versions` 记录每个 channel 的版本号
3. `aget()` 使用 SQL JOIN 查询：`checkpoints.channel_versions` JOIN `checkpoint_blobs`
4. 如果 `channel_versions` 为空或不匹配，JOIN 返回空结果，导致状态丢失

---

### 🔄 Step 3: Agent 定义层 (进行中)

**⚠️ 关键变更**: 传统节点函数 → `create_react_agent`

**旧结构 (已删除)**:
```
backend/graph/nodes/          ❌ 已删除
├── router.py                 ❌ 传统节点实现
├── market_analyst.py         ❌ 传统节点实现
└── story_planner.py          ❌ 传统节点实现
```

**新结构 (Agent 架构)**:
```
backend/graph/agents/         🔄 创建中
├── __init__.py               # Agent 导出
├── master_router.py          # L0 Agent
├── market_analyst.py         # L1 Agent
├── story_planner.py          # L2 Agent
├── skeleton_builder.py       # L3 Agent
├── novel_writer.py           # Mod A Agent
├── content_editor.py         # Mod A Agent
├── content_refiner.py        # Mod A Agent
├── script_adapter.py         # Mod B Agent
├── storyboard_director.py    # Mod C Agent
├── analysis_lab.py           # Mod A+ Agent
└── asset_inspector.py        # Mod X Agent
```

**Agent 定义示例** (`market_analyst.py`):
```python
"""Market Analyst Agent - Level 1 市场分析

使用 create_react_agent 创建，Prompt 从文件加载
"""

from pathlib import Path
from langgraph.prebuilt import create_react_agent
from backend.services.model_router import get_model_router
from backend.schemas.model_config import TaskType
from backend.tools import duckduckgo_search, metaso_search
import structlog

logger = structlog.get_logger(__name__)


def _load_market_analyst_prompt() -> str:
    """从文件加载 Market Analyst 的 System Prompt"""
    prompt_path = Path(__file__).parent.parent.parent.parent / "prompts" / "1_Market_Analyst.md"
    
    try:
        with open(prompt_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # 提取 Markdown 内容（去掉开头的标题）
        lines = content.split("\n")
        start_idx = 0
        for i, line in enumerate(lines):
            if line.strip() and not line.startswith("#"):
                start_idx = i
                break
        
        prompt = "\n".join(lines[start_idx:]).strip()
        logger.debug("Loaded Market Analyst prompt from file", path=str(prompt_path))
        return prompt
        
    except Exception as e:
        logger.error("Failed to load Market Analyst prompt", error=str(e))
        return """你是短剧市场分析专家。分析市场趋势并返回JSON格式报告。"""


async def create_market_analyst_agent(user_id: str, project_id: str = None):
    """
    创建 Market Analyst Agent
    
    Args:
        user_id: 用户ID
        project_id: 项目ID（可选）
    
    Returns:
        create_react_agent 创建的 Agent
    """
    # 获取配置好的模型
    router = get_model_router()
    model = await router.get_model(
        user_id=user_id,
        task_type=TaskType.MARKET_ANALYST,
        project_id=project_id
    )
    
    # 创建 Agent - 使用 create_react_agent
    agent = create_react_agent(
        model=model,
        tools=[duckduckgo_search, metaso_search],
        state_modifier=_load_market_analyst_prompt(),
    )
    
    return agent


# 导出
__all__ = ["create_market_analyst_agent"]
```

**Prompt 文件位置**: `prompts/1_Market_Analyst.md`

**设计原则**:
1. **Prompt 外置**: 所有 Agent Prompt 存储在 `prompts/` 目录，便于独立维护
2. **动态加载**: 使用 `_load_XXX_prompt()` 函数从文件加载
3. **模型路由**: 通过 `model_router` 动态获取用户配置的模型
4. **Agent Skill**: 使用 `create_react_agent` 创建具备 Tool 调用能力的 Agent

---

### 📋 Step 4: 全局路由架构 (待实施)

**文件**:
```
backend/graph/
├── router.py                 # 路由决策函数
├── main_graph.py            # 主 StateGraph
└── subgraphs/
    ├── __init__.py
    ├── module_a.py          # 小说生成子图
    ├── module_b.py          # 剧本提取子图
    └── module_c.py          # 分镜拆分子图
```

**主图结构** (`main_graph.py`):
```python
"""主 StateGraph - 组装所有 Agents"""

from langgraph.graph import StateGraph, START, END
from backend.graph.agents import (
    master_router_agent,
    market_analyst_agent,
    story_planner_agent,
    skeleton_builder_agent,
)
from backend.graph.subgraphs import create_module_a_subgraph
from backend.graph.router import (
    route_from_start,
    route_after_master_router,
    # ...
)

def create_main_graph(checkpointer=None):
    """创建主图"""
    graph = StateGraph(AgentState)
    
    # 编译子图
    module_a_subgraph = create_module_a_subgraph().compile()
    
    # 添加 Agent 节点
    graph.add_node("master_router", master_router_agent)
    graph.add_node("market_analyst", market_analyst_agent)
    graph.add_node("story_planner", story_planner_agent)
    graph.add_node("skeleton_builder", skeleton_builder_agent)
    graph.add_node("module_a", module_a_subgraph)
    # ... 其他节点
    
    # 入口路由
    graph.add_conditional_edges(
        START,
        route_from_start,
        {
            "master_router": "master_router",
            "market_analyst": "market_analyst",
            "story_planner": "story_planner",
            # ...
        }
    )
    
    # Master Router → Agents
    graph.add_conditional_edges(
        "master_router",
        route_after_master_router,
        {
            "market_analyst": "market_analyst",
            "story_planner": "story_planner",
            # ...
        }
    )
    
    # Level 1 → Level 2 → Level 3
    graph.add_conditional_edges(
        "market_analyst",
        route_after_market_analyst,
        {"wait": "wait_for_input", "next": "story_planner"}
    )
    # ...
    
    return graph.compile(checkpointer=checkpointer)
```

---

## 架构决策记录 (ADR)

### ADR-005: AsyncPostgresSaver Checkpoint 模式 (v4.0)

**决策**: 使用 `AsyncPostgresSaver` 进行状态持久化，但需注意版本匹配

**背景**: 
在测试中发现，Chat 历史记录在页面刷新后无法恢复，总是返回 cold start 状态。

**问题根因**:
```python
# AsyncPostgresSaver 使用 SQL JOIN 查询状态：
SELECT c.thread_id, c.checkpoint_id, c.parent_checkpoint_id, c.type, 
       c.checkpoint->>'ts' as ts, c.checkpoint->>'channel_values' as channel_values,
       cb.channel, cb.type, cb.blob
FROM checkpoints c
LEFT JOIN checkpoint_blobs cb ON ...
WHERE c.thread_id = %s
  AND jsonb_extract_path_text(c.checkpoint, 'channel_versions', cb.channel) IS NOT NULL
  AND jsonb_extract_path_text(c.checkpoint, 'channel_versions', cb.channel) = cb.version::text
```

如果 `channel_versions` 为空 `{}`，则 JOIN 条件永远不满足，导致查询返回空结果。

**正确实现模式**:
1. `new_versions` 必须包含所有 list/dict 类型的 channel keys
2. `channel_versions` 必须与 `new_versions` 完全匹配（key 和 value 都要一致）
3. 基础类型（str, int, bool）直接存储在 `channel_values`，不需要 version

**测试验证**:
- ✅ 修复前：`is_cold_start` 始终为 `true`（状态丢失）
- ✅ 修复后：第二次调用正确返回 `is_cold_start: false`，历史记录恢复

**代码位置**: `backend/api/graph.py` 第 457-488 行

---

### ADR-006: 消息序列化一致性 (JsonPlusSerializer)

**决策**: 所有 Checkpointer 实例必须使用相同的 `JsonPlusSerializer`

**背景**: 
在冷启动后点击 SDUI 按钮时，出现 `MESSAGE_COERCION_FAILURE` 错误：
```
ValueError: Message dict must contain 'role' and 'content' keys, 
got {'type': 'ai', 'data': {'content': '...', 'additional_kwargs': {...}}}
```

**问题根因**:
1. **序列化不一致**: 不同的代码路径使用了不同的 serializer
   - `checkpointer_manager.initialize()` 使用 `JsonPlusSerializer(pickle_fallback=True)`
   - 但 `get_checkpointer()` 和 `get_or_create_checkpointer()` 没有设置 `serde` 参数
   - 导致使用默认 serializer 读取数据

2. **消息格式不匹配**: 
   - `JsonPlusSerializer` 序列化 `AIMessage` → 正确格式（msgpack 编码）
   - 默认 serializer 反序列化 → 返回字典格式 `{'type': 'ai', 'data': {...}}`
   - `add_messages` reducer 只接受 `{'role': 'assistant', 'content': '...'}` 格式
   - 格式不匹配 → 报错

**验证方法**:
```python
# 测试 1: JsonPlusSerializer 工作正常
serde = JsonPlusSerializer(pickle_fallback=True)
ai_msg = AIMessage(content="测试", additional_kwargs={"is_welcome": True})
serialized = serde.dumps_typed(ai_msg)
deserialized = serde.loads_typed(serialized)
assert isinstance(deserialized, AIMessage)  # ✅ 通过

# 测试 2: 从 checkpoint 读取的消息是字典
checkpoint_tuple = await checkpointer.aget_tuple(config)
messages = checkpoint_tuple.checkpoint["channel_values"]["messages"]
assert isinstance(messages[0], dict)  # ❌ 应该是 AIMessage 对象

# 测试 3: add_messages 无法处理 LangChain 序列化格式
from langgraph.graph.message import add_messages
dict_msg = {'type': 'ai', 'data': {'content': '测试'}}
result = add_messages([], [dict_msg])  # ❌ MESSAGE_COERCION_FAILURE
```

**正确实现** (`backend/graph/checkpointer.py`):
```python
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer

class CheckpointerManager:
    async def initialize(self):
        # 初始化时使用 JsonPlusSerializer
        self._checkpointer = AsyncPostgresSaver(
            conn=conn, 
            serde=JsonPlusSerializer(pickle_fallback=True)  # ✅
        )
    
    @asynccontextmanager
    async def get_checkpointer(self):
        async with self._pool.connection() as conn:
            # ✅ 关键：必须使用相同的 serializer
            saver = AsyncPostgresSaver(
                conn=conn, 
                serde=JsonPlusSerializer(pickle_fallback=True)
            )
            yield saver

async def get_or_create_checkpointer():
    conn = await checkpointer_manager._pool.getconn()
    # ✅ 关键：必须使用相同的 serializer
    saver = AsyncPostgresSaver(
        conn=conn, 
        serde=JsonPlusSerializer(pickle_fallback=True)
    )
    return saver, conn
```

**工作原理**:
1. `JsonPlusSerializer` 使用 msgpack 编码 LangChain 消息对象
2. 序列化时保存完整的类型信息（module, class, fields）
3. 反序列化时还原为原始的 `AIMessage`/`HumanMessage` 对象
4. LangGraph 的 `add_messages` reducer 可以直接处理这些对象

**迁移指南**:
如果已有旧的 checkpoint 数据（使用错误格式存储）：
```python
# 清理脚本: clear_checkpoints.py
async with checkpointer_manager._pool.connection() as conn:
    await conn.execute("DELETE FROM checkpoint_blobs")
    await conn.execute("DELETE FROM checkpoint_writes")
    await conn.execute("DELETE FROM checkpoints")
    await conn.commit()
```

**状态**: ✅ 已修复 (2026-02-06)
- 修复文件: `backend/graph/checkpointer.py` 第 120、179 行
- 验证结果: 消息正确序列化/反序列化为 `AIMessage` 对象

---

### ADR-007: SDUI 持久化与恢复机制

**决策**: 优先从消息的 `additional_kwargs` 中恢复 SDUI，而非依赖独立的 `ui_interaction` 字段

**背景**:
消息序列化问题修复后，发现刷新页面后 SDUI 按钮消失，但调试显示 `ui_interaction` 已正确保存在 checkpoint 中。

**问题根因**:
1. **数据已保存**: 
   - ✅ `channel_values.ui_interaction` 存在（`UIInteractionBlock` 对象）
   - ✅ `messages[0].additional_kwargs.ui_interaction` 存在（字典格式）

2. **恢复逻辑错误** (`backend/api/graph.py` 第 373-379 行):
   ```python
   # ❌ 旧实现的问题
   ui_interaction_data = None
   if idx == len(raw_messages) - 1 and saved_ui_interaction:  # 问题 1: 只处理最后一条消息
       ui_interaction_data = UIInteractionBlock(**saved_ui_interaction)  # 问题 2: 假设是字典
   ```
   
   **问题**:
   - 只为**最后一条消息**附加 SDUI，但欢迎消息是**第一条**
   - 假设 `saved_ui_interaction` 是字典，但实际可能是 `UIInteractionBlock` 对象
   - 没有从消息的 `additional_kwargs` 中提取 SDUI

**调试验证** (`debug_ui_interaction.py`):
```python
# 检查 checkpoint 数据
checkpoint = await checkpointer.aget_tuple(config)
channel_values = checkpoint.checkpoint["channel_values"]

# ✅ ui_interaction 字段存在
print(f"ui_interaction: {type(channel_values['ui_interaction'])}")
# 输出: <class 'backend.schemas.common.UIInteractionBlock'>

# ✅ 消息中也有 ui_interaction
msg = channel_values["messages"][0]
print(f"additional_kwargs: {msg.additional_kwargs.keys()}")
# 输出: ['is_welcome', 'ui_interaction']
print(f"block_type: {msg.additional_kwargs['ui_interaction'].get('block_type')}")
# 输出: UIInteractionBlockType.ACTION_GROUP
```

**正确实现** (`backend/api/graph.py`):
```python
# 转换 LangChain 消息为 ChatMessage 格式
for idx, msg in enumerate(raw_messages):
    # 处理 LangChain 消息对象
    if isinstance(msg, (HumanMessage, AIMessage)):
        role = "user" if isinstance(msg, HumanMessage) else "assistant"
        formatted_content = format_message_content(str(msg.content))
        
        # ✅ 优先从消息的 additional_kwargs 中提取 ui_interaction
        msg_ui_interaction = None
        if hasattr(msg, 'additional_kwargs') and msg.additional_kwargs:
            ui_data = msg.additional_kwargs.get('ui_interaction')
            if ui_data:
                try:
                    # ✅ 处理两种格式
                    if isinstance(ui_data, UIInteractionBlock):
                        msg_ui_interaction = ui_data
                    elif isinstance(ui_data, dict):
                        msg_ui_interaction = UIInteractionBlock(**ui_data)
                except Exception as e:
                    logger.warning(f"Failed to parse ui_interaction: {e}")
    
    # 处理 dict 格式消息（旧数据兼容）
    elif isinstance(msg, dict):
        msg_ui_interaction = None
        if "type" in msg and "data" in msg:
            msg_data = msg.get("data", {})
            # ✅ 从 data.additional_kwargs 中提取
            if isinstance(msg_data, dict):
                ui_data = msg_data.get('additional_kwargs', {}).get('ui_interaction')
                if ui_data:
                    # 同样处理两种格式
                    ...
    
    # ✅ 如果消息本身没有 SDUI，尝试使用全局 ui_interaction
    # 但只为第一条欢迎消息附加
    ui_interaction_data = msg_ui_interaction
    if not ui_interaction_data and idx == 0 and role == "assistant" and saved_ui_interaction:
        try:
            if isinstance(saved_ui_interaction, UIInteractionBlock):
                ui_interaction_data = saved_ui_interaction
            elif isinstance(saved_ui_interaction, dict):
                ui_interaction_data = UIInteractionBlock(**saved_ui_interaction)
        except Exception as e:
            logger.warning(f"Failed to parse saved_ui_interaction: {e}")
    
    history_messages.append(
        ChatMessage(
            id=f"msg-{thread_id}-{idx}",
            role=role,
            content=formatted_content,
            timestamp=datetime.now().isoformat(),
            ui_interaction=ui_interaction_data,  # ✅ 正确附加
        )
    )
```

**设计原则**:
1. **数据源优先级**: `msg.additional_kwargs.ui_interaction` > `channel_values.ui_interaction`
2. **格式容错**: 同时处理 `UIInteractionBlock` 对象和字典格式
3. **位置正确**: SDUI 应附加到第一条欢迎消息（`idx == 0 and role == "assistant"`）
4. **向后兼容**: 支持旧的字典格式消息（`{'type': 'ai', 'data': {...}}`）

**状态**: ✅ 已修复 (2026-02-06)
- 修复文件: `backend/api/graph.py` 第 345-425 行
- 验证结果: 刷新页面后 SDUI 按钮正确显示

---

### ADR-004: Agent 架构选型 (v4.0)

**决策**: 使用 `create_react_agent` 而非传统节点函数

**理由**:
1. **标准化** - 符合 LangChain 官方最佳实践
2. **自主性** - Agent 自主决定 Tool 使用和推理路径
3. **可维护性** - 清晰的职责边界 (System Prompt)
4. **扩展性** - 新增 Tool 无需修改 Agent 代码

**对比**:
```python
# ✅ 推荐: Agent 架构
agent = create_react_agent(model, tools, state_modifier=prompt)
result = await agent.ainvoke(input)

# ❌ 不推荐: 传统节点函数 (已删除)
async def node(state):
    model = get_model()
    response = await model.ainvoke(messages)
    return parse_response(response)
```

**状态**: ✅ 已实施 (nodes/ 已删除，agents/ 创建中)

---

## 后续构建计划

### 📋 Step 3: Agent 定义层 (当前)

**目标**: 创建所有 Agent

- [x] 删除旧 `nodes/` 目录
- [ ] 创建 `agents/` 目录结构
- [ ] 创建 `agents/__init__.py` - Agent 导出
- [ ] 创建 `agents/master_router.py` - L0 Agent
- [ ] 创建 `agents/market_analyst.py` - L1 Agent
- [ ] 创建 `agents/story_planner.py` - L2 Agent
- [ ] 编写 Agent 单元测试

### 📋 Step 4: 全局路由架构 (下一步)

- [ ] 创建 `graph/router.py`
- [ ] 创建 `graph/main_graph.py`
- [ ] 创建 `subgraphs/module_a.py`
- [ ] 集成测试

### 📋 Step 5: API 接口层

- [x] 创建 `api/routers/graph.py` - 已有基础实现
- [x] SSE 流式输出 - 已有基础实现
- [x] 历史记录恢复 - ✅ **已修复** (见 ADR-005)
  - 修复文件: `backend/api/graph.py` 第 471 行
  - 修复内容: `channel_versions` 必须与 `new_versions` 匹配
  - 验证结果: 页面刷新后正确恢复历史记录和 UI 按钮

---

## 参考文档

- [REBUILD_PLAN.md](./REBUILD_PLAN.md) - 详细重构计划
- [Product-Spec.md](../Product-Spec.md) - 产品需求文档
- [System-Architecture.md](../System-Architecture.md) - 系统架构文档（已更新为 Agent 架构）
- LangChain Agent 文档: https://python.langchain.com/docs/how_to/agent_executor

---

### ADR-008: Celery + Market Analysis 缓存系统重构

**决策**: 重构 Celery 配置和 Market Analysis 缓存系统，支持自动执行和手动触发

**背景**:
市场分析报告缓存系统存在多个问题：
1. Celery 定时任务未正确加载 `market_analysis_task`
2. `market_reports` 数据库表不存在
3. `DatabaseService` 中的方法缩进错误，导致方法未定义
4. 搜索工具调用失败 (`'StructuredTool' object is not callable`)
5. 没有手动触发缓存生成的 API

**问题修复**:

1. **Celery 配置修复** (`celery_app.py`):
```python
celery_app = Celery(
    "ai_video_engine",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=[
        "backend.tasks.job_processor",
        "backend.tasks.market_analysis_task",  # 添加市场分析任务
    ],
)
```

2. **自动启动 Celery** (`main.py`):
```python
def start_celery():
    """启动 Celery Worker 和 Beat 进程"""
    # 设置 PYTHONPATH 解决导入问题
    env["PYTHONPATH"] = project_root + ":" + env.get("PYTHONPATH", "")
    
    # 启动 Worker 和 Beat
    celery_worker_process = subprocess.Popen(...)
    celery_beat_process = subprocess.Popen(...)
```

3. **数据库表创建**:
```sql
CREATE TABLE public.market_reports (
    id UUID DEFAULT extensions.uuid_generate_v4() PRIMARY KEY,
    report_type VARCHAR(50),
    genres JSONB,
    tones JSONB,
    insights TEXT,
    target_audience TEXT,
    search_queries JSONB,
    raw_search_results TEXT,
    valid_until TIMESTAMPTZ,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT now()
);
```

4. **方法缩进修复** (`database.py`):
```python
# 将 create_market_report 和 get_latest_market_report 
# 从 get_db_service() 函数内部移到 DatabaseService 类内部

async def create_market_report(self, data: dict[str, Any]) -> dict[str, Any]:
    """创建市场分析报告"""
    ...

async def get_latest_market_report(self) -> dict[str, Any] | None:
    """获取最新的有效市场分析报告"""
    ...
```

5. **搜索工具导入修复** (`market_analysis.py`):
```python
# ❌ 错误：从 tools 模块导入被 @tool 装饰的函数
from backend.tools import metaso_search

# ✅ 正确：直接导入原始函数
from backend.tools.metaso_search import metaso_search
```

6. **手动触发 API** (`graph.py`):
```python
@router.post("/market-analysis/trigger")
async def trigger_market_analysis():
    """手动触发市场分析任务"""
    ...

@router.get("/market-analysis/status")
async def get_market_analysis_status():
    """获取市场分析缓存状态"""
    ...
```

**修复清单**:
- ✅ Celery 配置：添加 `market_analysis_task` 到 include
- ✅ main.py：自动启动 Celery Worker 和 Beat
- ✅ 数据库：创建 `market_reports` 表
- ✅ database.py：修复方法缩进错误
- ✅ market_analysis.py：修复搜索工具导入
- ✅ graph.py：添加手动触发和状态查询 API
- ✅ story_planner.py：添加无缓存提示
- ✅ prompts：修复 `market_analyst_daily` → `market_analyst`

**验证结果**:
```bash
# 1. 启动服务，Celery 自动启动
python -m uvicorn main:app --reload

# 2. 手动触发市场分析
curl -X POST http://localhost:8000/api/graph/market-analysis/trigger
# 返回: {"status":"success","genre_count":4,"insights":"..."}

# 3. 检查缓存状态
curl http://localhost:8000/api/graph/market-analysis/status
# 返回: {"has_cache":true,"analyzed_at":"2026-02-06T...","genre_count":4}

# 4. 查询数据库确认
SELECT * FROM market_reports;
# 显示: 1 条记录，valid_until 为 7 天后
```

**架构设计**:

```
┌─────────────────────────────────────────────────────────────────┐
│                    Market Analysis 架构                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. 后台 Service（每7天自动执行）                                 │
│     MarketAnalysisService                                        │
│     ├── run_daily_analysis()  ← Celery Beat 定时触发            │
│     ├── get_latest_analysis() ← Story Planner 读取缓存          │
│     └── save_analysis()       ← 保存到数据库 (7天有效期)        │
│                                                                  │
│  2. 实时 Agent（前端用户触发）                                    │
│     Market Analyst Agent                                         │
│     ├── create_market_analyst_agent()                           │
│     ├── 每次执行实时搜索（不使用缓存）                            │
│     └── 根据用户具体需求分析                                      │
│                                                                  │
│  3. Story Planner（使用缓存）                                     │
│     ├── get_market_analysis_service().get_latest_analysis()     │
│     ├── 注入缓存到 Prompt                                         │
│     └── 如果无缓存，返回提示信息                                  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**状态**: ✅ 已修复 (2026-02-06)
- Celery 自动启动和定时任务执行正常
- 市场分析缓存成功保存到数据库
- Story Planner 正确读取缓存
- 提供手动触发 API 用于即时生成缓存

---

## 变更日志

### v4.0.3 (2026-02-06)
- ✅ **新增**: Celery 自动启动和管理系统
  - main.py 自动启动 Celery Worker 和 Beat
  - 进程绑定和优雅关闭处理
- ✅ **新增**: Market Analysis 缓存系统
  - 创建 market_reports 数据库表
  - 7天有效期自动缓存机制
  - 手动触发和状态查询 API
- 🐛 **修复**: Celery 配置缺失 market_analysis_task
- 🐛 **修复**: DatabaseService 方法缩进错误
- 🐛 **修复**: 搜索工具导入错误 (`StructuredTool not callable`)
- 🐛 **修复**: Prompt 名称错误 (`market_analyst_daily` → `market_analyst`)

### v4.0.2 (2026-02-06)
- 🐛 **修复**: MESSAGE_COERCION_FAILURE 消息序列化错误
  - 根因: `get_checkpointer()` 和 `get_or_create_checkpointer()` 未设置 `JsonPlusSerializer`
  - 导致: 序列化用 JsonPlusSerializer，反序列化用默认 serializer，格式不匹配
  - 修复: 所有 checkpointer 创建点统一使用 `JsonPlusSerializer(pickle_fallback=True)`
  - 验证: 消息正确序列化/反序列化为 `AIMessage` 对象
  - 文件: `backend/graph/checkpointer.py` 第 120、179 行
- 🐛 **修复**: SDUI 按钮在页面刷新后消失
  - 根因: 恢复逻辑未从消息的 `additional_kwargs` 中提取 `ui_interaction`
  - 导致: 虽然数据已保存，但未正确附加到前端消息
  - 修复: 优先从 `msg.additional_kwargs.ui_interaction` 提取，支持对象和字典两种格式
  - 验证: 刷新页面后 SDUI 按钮正确显示
  - 文件: `backend/api/graph.py` 第 345-425 行
- 📝 **新增**: ADR-006 - 消息序列化一致性文档
- 📝 **新增**: ADR-007 - SDUI 持久化与恢复机制文档
- 📝 **新增**: 故障排除指南 - MESSAGE_COERCION_FAILURE 和 SDUI 恢复问题
- 🔧 **工具**: 添加调试脚本 `debug_message_format.py` 和 `debug_ui_interaction.py`
- 🧹 **清理**: 创建 `clear_checkpoints.py` 脚本用于清理旧格式的 checkpoint 数据

### v4.0.1 (2026-02-06)
- 🐛 **修复**: Chat 历史记录无法恢复的问题
  - 根因: `channel_versions` 与 `new_versions` 不匹配导致 SQL JOIN 失败
  - 修复: 确保 `channel_versions = {k: str(v) for k, v in new_versions.items()}`
  - 验证: 页面刷新后正确恢复历史记录和 UI 按钮
- 📝 **新增**: ADR-005 - AsyncPostgresSaver Checkpoint 模式文档
- 📝 **更新**: Step 2 基础设施层添加 Checkpoint 正确使用指南

### v4.0.0 (2026-02-06)
- 🗑️ **删除**: `nodes/` 目录（传统节点函数实现）
- 🔄 **重构**: 迁移到 Agent 架构 (`create_react_agent`)
- 📝 **更新**: System-Architecture.md 以反映 Agent 架构
- 🎯 **下一步**: 创建 `agents/` 目录和所有 Agent 定义

---

## 故障排除指南

### 问题 1: Chat 历史记录在刷新后丢失

**症状**:
- 每次页面刷新都返回 cold start 欢迎消息
- `is_cold_start` 始终为 `true`
- 之前的对话历史和 UI 按钮消失

**排查步骤**:

1. **检查 checkpoint 是否保存成功**:
```python
# 在 aput() 调用后添加日志
await checkpointer.aput(config, checkpoint, metadata, new_versions)
logger.info("Checkpoint saved", 
    thread_id=thread_id,
    channel_versions=checkpoint.get("channel_versions"),
    new_versions=new_versions
)
```

2. **验证 channel_versions 格式**:
```python
# 必须是字符串值的 dict
assert checkpoint["channel_versions"] == {"messages": "1", "ui_interaction": "1"}
# 不是
assert checkpoint["channel_versions"] != {"messages": 1, "ui_interaction": 1}  # ❌ int value
assert checkpoint["channel_versions"] != {}  # ❌ empty dict
```

3. **数据库直接查询验证**:
```sql
-- 检查 checkpoints 表
SELECT thread_id, checkpoint->'channel_versions' as versions
FROM checkpoints 
WHERE thread_id = 'your-thread-id';

-- 结果应该显示: {"messages": "1", "ui_interaction": "1"}
-- 而不是: {}

-- 检查 checkpoint_blobs 表
SELECT thread_id, channel, version
FROM checkpoint_blobs
WHERE thread_id = 'your-thread-id';

-- 应该看到与 channel_versions 匹配的记录
```

**解决方案**:
确保 `channel_versions` 与 `new_versions` 匹配：
```python
new_versions = {
    "messages": 1,
    "ui_interaction": 1,
}

checkpoint = {
    # ... 其他字段
    "channel_versions": {k: str(v) for k, v in new_versions.items()},
    # 结果: {"messages": "1", "ui_interaction": "1"}
}
```

**相关 ADR**: ADR-005

---

### 问题 2: MESSAGE_COERCION_FAILURE 错误

**症状**:
```
ValueError: Message dict must contain 'role' and 'content' keys, 
got {'type': 'ai', 'data': {'content': '...', 'additional_kwargs': {...}}}
```

**排查步骤**:

1. **检查 checkpoint 中的消息格式**:
```python
# debug_message_format.py
checkpoint_tuple = await checkpointer.aget_tuple(config)
messages = checkpoint_tuple.checkpoint["channel_values"]["messages"]

for i, msg in enumerate(messages):
    print(f"消息 {i}: 类型={type(msg)}, 是AIMessage={isinstance(msg, AIMessage)}")
    
# ✅ 正确: <class 'langchain_core.messages.ai.AIMessage'>
# ❌ 错误: <class 'dict'> 且 keys=['type', 'data']
```

2. **验证 serializer 一致性**:
```python
# 检查所有创建 checkpointer 的地方
grep -rn "AsyncPostgresSaver" backend/graph/

# 每个地方都应该有 serde=JsonPlusSerializer(pickle_fallback=True)
```

3. **测试 add_messages reducer**:
```python
from langgraph.graph.message import add_messages

# ✅ 应该成功
openai_msg = {'role': 'assistant', 'content': '测试'}
result = add_messages([], [openai_msg])

# ❌ 应该失败（如果出现此格式说明有问题）
langchain_dict = {'type': 'ai', 'data': {'content': '测试'}}
result = add_messages([], [langchain_dict])  # MESSAGE_COERCION_FAILURE
```

**解决方案**:

1. **确保所有 checkpointer 使用相同的 serializer**:
```python
# backend/graph/checkpointer.py
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer

# 所有创建 AsyncPostgresSaver 的地方都必须加上
saver = AsyncPostgresSaver(
    conn=conn, 
    serde=JsonPlusSerializer(pickle_fallback=True)  # ✅ 必须
)
```

2. **清理旧的 checkpoint 数据**:
```bash
cd /Users/ariesmartin/Documents/new-video
source backend/.venv/bin/activate
python clear_checkpoints.py
```

3. **重新冷启动**:
刷新页面，让系统通过正确的 LangGraph 流程创建新的 checkpoint。

**相关 ADR**: ADR-006

---

### 问题 3: SDUI 按钮在刷新后消失

**症状**:
- 首次冷启动时 SDUI 按钮正常显示
- 刷新页面后，欢迎消息显示但按钮消失
- 控制台没有错误

**排查步骤**:

1. **检查 checkpoint 中是否有 ui_interaction**:
```python
# debug_ui_interaction.py
checkpoint_tuple = await checkpointer.aget_tuple(config)
channel_values = checkpoint_tuple.checkpoint["channel_values"]

# 检查独立字段
ui_interaction = channel_values.get("ui_interaction")
print(f"ui_interaction 存在: {ui_interaction is not None}")
print(f"ui_interaction 类型: {type(ui_interaction)}")

# 检查消息中的 additional_kwargs
msg = channel_values["messages"][0]
if hasattr(msg, 'additional_kwargs'):
    ui_in_msg = msg.additional_kwargs.get('ui_interaction')
    print(f"消息中有 ui_interaction: {ui_in_msg is not None}")
```

2. **检查前端收到的数据**:
```javascript
// 浏览器控制台
// 在 chat_init_endpoint 返回的数据中查看
console.log('Message 0:', messages[0]);
console.log('UI Interaction:', messages[0].ui_interaction);
```

3. **检查恢复逻辑**:
```python
# backend/api/graph.py - chat_init_endpoint
# 查找这段代码，应该优先从 msg.additional_kwargs 提取
if hasattr(msg, 'additional_kwargs') and msg.additional_kwargs:
    ui_data = msg.additional_kwargs.get('ui_interaction')
    # ...
```

**解决方案**:

修复 `backend/api/graph.py` 中的 SDUI 恢复逻辑：

```python
# 优先从消息的 additional_kwargs 中提取（第 345-425 行）
for idx, msg in enumerate(raw_messages):
    if isinstance(msg, (HumanMessage, AIMessage)):
        # ✅ 从 additional_kwargs 提取
        msg_ui_interaction = None
        if hasattr(msg, 'additional_kwargs') and msg.additional_kwargs:
            ui_data = msg.additional_kwargs.get('ui_interaction')
            if ui_data:
                if isinstance(ui_data, UIInteractionBlock):
                    msg_ui_interaction = ui_data
                elif isinstance(ui_data, dict):
                    msg_ui_interaction = UIInteractionBlock(**ui_data)
    
    # ✅ 如果消息本身没有，尝试使用全局 ui_interaction
    # 只为第一条欢迎消息（idx == 0）附加
    ui_interaction_data = msg_ui_interaction
    if not ui_interaction_data and idx == 0 and role == "assistant":
        if isinstance(saved_ui_interaction, UIInteractionBlock):
            ui_interaction_data = saved_ui_interaction
        # ...
```

**关键点**:
1. **数据源优先级**: 优先使用 `msg.additional_kwargs.ui_interaction`
2. **格式容错**: 处理 `UIInteractionBlock` 对象和字典两种格式
3. **位置正确**: 只为第一条 AI 消息（欢迎消息）附加 SDUI

**相关 ADR**: ADR-007

---

**最后更新**: 2026-02-06  
**构建状态**: Step 2/5 完成，Step 3 进行中  
**架构版本**: v4.0.2 Agent 架构 + 消息序列化修复 + SDUI 持久化修复

