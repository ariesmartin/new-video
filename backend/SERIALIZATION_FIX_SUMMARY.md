# 消息序列化与 SDUI 持久化修复总结

## 📋 修复概览

**日期**: 2026-02-06  
**版本**: v4.0.2  
**影响范围**: LangGraph Checkpoint 序列化机制、SDUI 持久化与恢复

---

## 🐛 问题 1: MESSAGE_COERCION_FAILURE 错误

### 症状
```
ValueError: Message dict must contain 'role' and 'content' keys, 
got {'type': 'ai', 'data': {'content': '...', 'additional_kwargs': {...}}}
```

### 根本原因
**序列化和反序列化使用了不同的 Serializer**

| 位置 | 代码 | Serializer |
|------|------|------------|
| 初始化 | `checkpointer_manager.initialize()` | ✅ `JsonPlusSerializer(pickle_fallback=True)` |
| `get_checkpointer()` | 上下文管理器 | ❌ 没有设置 serde（使用默认） |
| `get_or_create_checkpointer()` | 返回新实例 | ❌ 没有设置 serde（使用默认） |

**结果**:
1. 消息用 `JsonPlusSerializer` **序列化**保存
2. 但用**默认 serializer** 反序列化读取
3. 格式不匹配：`{'type': 'ai', 'data': {...}}` vs `{'role': 'assistant', 'content': '...'}`
4. `add_messages` reducer 只接受 OpenAI 格式 → 报错

### 修复方案

**文件**: `backend/graph/checkpointer.py`

```python
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer

# 修复 get_checkpointer() (第 120 行)
@asynccontextmanager
async def get_checkpointer(self):
    async with self._pool.connection() as conn:
        # ✅ 添加 JsonPlusSerializer
        saver = AsyncPostgresSaver(
            conn=conn, 
            serde=JsonPlusSerializer(pickle_fallback=True)
        )
        yield saver

# 修复 get_or_create_checkpointer() (第 179 行)
async def get_or_create_checkpointer():
    conn = await checkpointer_manager._pool.getconn()
    # ✅ 添加 JsonPlusSerializer
    saver = AsyncPostgresSaver(
        conn=conn, 
        serde=JsonPlusSerializer(pickle_fallback=True)
    )
    return saver, conn
```

### 验证方法

```python
# 测试脚本: debug_message_format.py
checkpoint_tuple = await checkpointer.aget_tuple(config)
messages = checkpoint_tuple.checkpoint["channel_values"]["messages"]

# ✅ 正确: 应该是 AIMessage 对象
assert isinstance(messages[0], AIMessage)

# ❌ 错误: 如果是 dict，说明 serializer 不一致
assert not isinstance(messages[0], dict)
```

### 迁移步骤

如果已有旧的 checkpoint 数据：

```bash
cd /Users/ariesmartin/Documents/new-video
source backend/.venv/bin/activate
python clear_checkpoints.py  # 清理旧数据
# 刷新页面重新冷启动
```

---

## 🐛 问题 2: SDUI 按钮在刷新后消失

### 症状
- 首次冷启动：SDUI 按钮 ✅ 正常显示
- 刷新页面：欢迎消息显示，但按钮 ❌ 消失

### 根本原因

**SDUI 数据已正确保存，但恢复逻辑有误**

调试发现（`debug_ui_interaction.py`）：
- ✅ `channel_values.ui_interaction` 存在（`UIInteractionBlock` 对象）
- ✅ `messages[0].additional_kwargs.ui_interaction` 存在（字典格式）

但恢复逻辑（`backend/api/graph.py` 第 373-379 行）：
```python
# ❌ 旧实现的问题
ui_interaction_data = None
if idx == len(raw_messages) - 1 and saved_ui_interaction:  # 问题 1
    ui_interaction_data = UIInteractionBlock(**saved_ui_interaction)  # 问题 2
```

**问题**:
1. 只为**最后一条消息**附加 SDUI，但欢迎消息是**第一条**
2. 假设 `saved_ui_interaction` 是字典，但实际可能是对象
3. 没有从消息的 `additional_kwargs` 中提取

### 修复方案

**文件**: `backend/api/graph.py` (第 345-425 行)

```python
for idx, msg in enumerate(raw_messages):
    if isinstance(msg, (HumanMessage, AIMessage)):
        role = "user" if isinstance(msg, HumanMessage) else "assistant"
        formatted_content = format_message_content(str(msg.content))
        
        # ✅ 优先从 additional_kwargs 提取
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
    
    # ✅ 如果消息本身没有，尝试使用全局 ui_interaction
    # 只为第一条欢迎消息（idx == 0）附加
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
            ui_interaction=ui_interaction_data,  # ✅
        )
    )
```

### 设计原则
1. **数据源优先级**: `msg.additional_kwargs.ui_interaction` > `channel_values.ui_interaction`
2. **格式容错**: 处理 `UIInteractionBlock` 对象和字典两种格式
3. **位置正确**: 只为第一条 AI 消息（欢迎消息）附加 SDUI
4. **向后兼容**: 支持旧的字典格式消息

---

## 📝 文档更新

### 新增架构决策记录 (ADR)

**ADR-006**: 消息序列化一致性 (JsonPlusSerializer)
- 问题根因分析
- 验证方法
- 正确实现模式
- 迁移指南

**ADR-007**: SDUI 持久化与恢复机制
- 问题根因分析
- 调试验证过程
- 正确实现模式
- 设计原则

### 更新故障排除指南

新增 3 个常见问题的诊断和解决方案：
1. Chat 历史记录在刷新后丢失
2. MESSAGE_COERCION_FAILURE 错误
3. SDUI 按钮在刷新后消失

每个问题包含：
- 症状描述
- 详细排查步骤
- 具体解决方案
- 相关 ADR 引用

---

## 🔧 调试工具

### 创建的调试脚本

1. **`debug_message_format.py`**
   - 测试 JsonPlusSerializer 序列化/反序列化
   - 检查 checkpoint 中的消息格式
   - 测试 add_messages reducer 行为

2. **`debug_ui_interaction.py`**
   - 检查 checkpoint 中的 ui_interaction 字段
   - 检查消息中的 additional_kwargs.ui_interaction
   - 验证数据是否正确保存

3. **`clear_checkpoints.py`**
   - 清理旧格式的 checkpoint 数据
   - 用于迁移到新的序列化机制

---

## ✅ 验证结果

### 修复前
- ❌ 点击 SDUI 按钮 → MESSAGE_COERCION_FAILURE 错误
- ❌ 刷新页面 → SDUI 按钮消失

### 修复后
- ✅ 消息正确序列化/反序列化为 `AIMessage` 对象
- ✅ 刷新页面后 SDUI 按钮正确显示
- ✅ 所有交互功能正常

---

## 📚 相关文件

### 修改的代码文件
- `backend/graph/checkpointer.py` (第 120、179 行)
- `backend/api/graph.py` (第 345-425 行)

### 更新的文档
- `backend/ARCHITECTURE_REBUILD.md`
  - 新增 ADR-006 和 ADR-007
  - 更新故障排除指南
  - 更新变更日志为 v4.0.2

### 创建的工具
- `debug_message_format.py`
- `debug_ui_interaction.py`  
- `clear_checkpoints.py`

---

## 🎯 关键教训

### 1. Serializer 一致性至关重要
所有创建 checkpointer 的地方必须使用相同的 serializer，否则会导致格式不匹配。

### 2. SDUI 数据应嵌入消息
优先从消息的 `additional_kwargs` 中恢复 SDUI，而不是依赖独立的 `ui_interaction` 字段。

### 3. 测试驱动调试
创建专门的调试脚本来验证 checkpoint 数据格式，可以快速定位问题根源。

### 4. 文档化架构决策
将问题根因、修复方案和设计原则记录为 ADR，便于后续维护和问题排查。

---

**最后更新**: 2026-02-06  
**架构版本**: v4.0.2
