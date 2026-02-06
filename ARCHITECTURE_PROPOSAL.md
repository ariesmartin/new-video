# AI短剧台 - 架构重构方案 V1.0

## 现状分析

### 原始设计意图（来自Product-Spec.md & System-Architecture.md）

**核心功能**：
1. **Level 1-3 大纲规划**：参数锚定 → 灵感风暴 → 骨架构建
2. **Module A 小说编写**：Writer-Editor-Refiner闭环
3. **Module B 剧本提取**：小说→结构化剧本
4. **Module C 分镜拆分**：剧本→可视化分镜
5. **生产模块**：生图、视频、资产、配音等

**设计亮点**：
- Human-in-the-Loop：关键节点暂停等待用户确认
- Agentic Workflow：多Agent协作（Market Analyst, Story Planner等）
- SDUI交互：AI返回可点击按钮
- 流式输出：实时显示AI思考过程

### 当前实现的问题

1. **架构过度复杂**：
   - 使用了LangGraph的checkpoint、interrupt、subgraph等高级特性
   - 路由逻辑分散在6个函数中（`_route_from_start`, `_route_after_*`等）
   - 为了修复bug，添加了不存在的`wait_for_input`节点
   - 禁用了`interrupt_before`，破坏了Human-in-the-Loop设计

2. **状态管理混乱**：
   - 为了绕过checkpoint恢复问题，创建"fresh graph"
   - 多层状态拷贝（current_state, final_state_values等）
   - 手动管理checkpoint清除和保存

3. **流式输出问题**：
   - 使用了`astream_events`而不是简单的流式
   - 内容被截断（`[:100]`）
   - Gemini返回的格式未正确处理

---

## 方案对比

### 方案A：简化LangGraph（保留原架构，精简实现）

**核心思想**：保留LangGraph，但移除不必要的复杂度

**文件结构**：
```
backend/
├── main.py                    # FastAPI入口（简化）
├── api/
│   └── chat.py               # 聊天API（简化路由）
├── graph/
│   ├── __init__.py
│   ├── state.py              # AgentState定义
│   ├── nodes.py              # 3个节点函数
│   └── router.py             # 1个路由函数
└── services/
    ├── llm.py               # LLM调用
    └── prompts.py           # Prompt管理
```

**关键设计**：
1. **只保留3个节点**：
   - `market_analyst`：选择题材
   - `story_planner`：生成方案（interrupt_before）
   - `writer`：写小说

2. **简化路由**：
   ```python
   def route(state):
       action = parse_action(state["messages"][-1])
       if action == "select_genre":
           return "story_planner"
       elif action == "select_plan":
           return "writer"
       # ...
   ```

3. **正确处理interrupt**：
   - `story_planner`配置`interrupt_before=True`
   - 用户点击按钮后调用`graph.ainvoke(None, config)`继续

**优点**：
- 保留LangGraph的可视化和调试能力
- 代码结构清晰（5个文件vs现在的20+）
- 约300行代码vs现在的2000+

**缺点**：
- 仍然依赖LangGraph的复杂度
- 需要正确理解interrupt机制

---

### 方案B：只用LangChain（轻量级）

**核心思想**：去掉LangGraph的图结构，用简单的链式调用

**文件结构**：
```
backend/
├── main.py
├── api/
│   └── chat.py              # 路由分发
├── chains/
│   ├── __init__.py
│   ├── market_analyst.py    # 独立链
│   ├── story_planner.py     # 独立链
│   └── writer.py            # 独立链
├── services/
│   ├── llm.py
│   └── prompts.py
└── models/
    └── state.py             # 简单的Pydantic模型
```

**关键设计**：
1. **API层路由**：
   ```python
   @router.post("/chat")
   async def chat(request):
       state = load_state(request.thread_id)
       
       if request.action == "select_genre":
           result = await run_market_analyst_chain(state)
       elif request.action == "random_plan":
           result = await run_story_planner_chain(state)
       # ...
       
       save_state(request.thread_id, result)
       return result
   ```

2. **每个模块独立**：
   ```python
   # chains/story_planner.py
   async def run_story_planner_chain(state):
       prompt = load_prompt("story_planner")
       response = await llm.ainvoke(prompt.format(**state))
       return {
           "story_plans": parse_plans(response),
           "ui_interaction": create_ui(response)
       }
   ```

3. **状态用数据库管理**：
   ```python
   # models/state.py
   class ConversationState(BaseModel):
       thread_id: str
       stage: str  # "L1", "L2", "L3", "writing"
       user_config: dict
       story_plans: list
       selected_plan: dict
       messages: list
   ```

**优点**：
- 简单直观，无框架复杂度
- 容易调试（单步跟踪）
- 状态管理清晰（数据库表）
- 约200行核心代码

**缺点**：
- 失去LangGraph的可视化
- 需要手动管理流程状态

---

### 方案C：纯FastAPI（最简单）

**核心思想**：不用任何AI框架，直接调用API

**文件结构**：
```
backend/
├── main.py
├── api/
│   └── chat.py              # 所有逻辑在此
├── services/
│   ├── gemini.py           # 直接调用Gemini API
│   └── prompts.py          # Prompt字符串
└── models/
    └── schemas.py          # Pydantic模型
```

**关键设计**：
1. **一个文件处理所有逻辑**：
   ```python
   # api/chat.py
   @router.post("/chat")
   async def chat(request):
       history = await db.get_history(request.thread_id)
       
       if request.stage == "L1":
           system_prompt = prompts.MARKET_ANALYST
           user_prompt = f"选择题材：{request.message}"
       elif request.stage == "L2":
           system_prompt = prompts.STORY_PLANNER
           user_prompt = f"生成方案，题材：{history['genre']}"
       # ...
       
       response = await gemini.generate(system_prompt, user_prompt, history)
       
       # 解析响应，更新stage
       new_stage = determine_next_stage(request.stage, response)
       await db.update_state(request.thread_id, {
           "stage": new_stage,
           "content": response
       })
       
       return {
           "content": response,
           "stage": new_stage,
           "ui_buttons": extract_buttons(response)
       }
   ```

2. **前端轮询状态**：
   - SSE只用于流式输出
   - 状态变化通过独立API获取

**优点**：
- 极致简单（约100行核心代码）
- 无框架依赖
- 完全可控

**缺点**：
- 所有逻辑硬编码
- 扩展性受限
- 需要前端配合轮询

---

## 方案对比表

| 维度 | 方案A：简化LangGraph | 方案B：只用LangChain | 方案C：纯FastAPI |
|------|---------------------|---------------------|-----------------|
| **代码量** | ~300行 | ~200行 | ~100行 |
| **文件数** | 5-6个 | 4-5个 | 3-4个 |
| **学习曲线** | 中等（需理解LangGraph） | 低（简单链式调用） | 极低（纯Python） |
| **调试难度** | 中等 | 低 | 极低 |
| **可扩展性** | 高（保留图结构） | 中（需手动扩展） | 低（硬编码） |
| **Human-in-the-Loop** | 原生支持 | 需手动实现 | 需手动实现 |
| **流式输出** | LangGraph自动处理 | LangChain支持 | 需手动实现 |
| **状态管理** | LangGraph checkpoint | 数据库 | 数据库 |
| **开发时间** | 1周 | 3-4天 | 2-3天 |

---

## 我的建议

### 如果这是MVP验证阶段：
→ **选方案C**：最快实现，验证产品市场匹配

### 如果产品方向已确定，需要长期维护：
→ **选方案B**：平衡了简洁和可维护性

### 如果坚信需要复杂的Agent编排：
→ **选方案A**：但要严格限制复杂度

---

## 下一步

1. **你确认方案**（A、B、C中的一个）
2. **我编写详细的设计文档**：
   - 文件结构
   - 核心代码示例
   - API接口定义
3. **你确认设计文档**
4. **我开始重写代码**

**请告诉我你的选择（A、B或C），或者你有其他想法？**
