# AI短剧台 - 架构设计文档 V2.0 (LangChain简化版)

## 设计决策

**选择方案**：B（只用LangChain，不用LangGraph）

**理由**：
1. 避免LangGraph的复杂度（checkpoint恢复、图结构、interrupt机制）
2. 保留流式输出和Human-in-the-Loop能力
3. 状态管理清晰（数据库表而非复杂的状态图）
4. 代码量少，易于维护

---

## 核心架构

```
┌─────────────────────────────────────────────────────────────┐
│  Frontend (React + SSE)                                     │
│  - 发送用户消息                                             │
│  - 接收流式token（纯文本）                                  │
│  - 显示SDUI按钮                                             │
└──────────────────────┬──────────────────────────────────────┘
                       │ POST /api/chat
                       │ {thread_id, message, stage?}
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  FastAPI Router                                             │
│  - 解析action（select_genre, random_plan, select_plan等）    │
│  - 加载conversation状态                                     │
│  - 调用对应chain                                            │
│  - 保存新状态                                               │
└──────────────────────┬──────────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ Market       │ │ Story        │ │ Writer       │
│ Analyst      │ │ Planner      │ │ Chain        │
│ Chain        │ │ Chain        │ │              │
└──────────────┘ └──────────────┘ └──────────────┘
        │              │              │
        └──────────────┴──────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  Gemini API (via LangChain)                                 │
│  - 流式输出token                                            │
│  - 返回结构化内容                                           │
└─────────────────────────────────────────────────────────────┘
```

---

## 数据模型

```python
# models/conversation.py
from pydantic import BaseModel
from typing import List, Dict, Optional, Literal
from datetime import datetime

class StoryPlan(BaseModel):
    plan_id: str
    title: str
    tagline: str

class ConversationState(BaseModel):
    """对话状态 - 用SQLite存储"""
    thread_id: str
    project_id: str
    user_id: str
    
    # 当前阶段
    stage: Literal["welcome", "L1", "L2", "L3", "writing", "completed"]
    
    # Level 1: 用户配置
    user_config: Dict = {}
    # {
    #   "genre": "银发觉醒",
    #   "tone": ["爽感", "情感"],
    #   "target_word_count": 500,
    #   "total_episodes": 10
    # }
    
    # Level 2: 故事方案
    story_plans: List[StoryPlan] = []
    selected_plan: Optional[StoryPlan] = None
    
    # Level 3: 人设和大纲
    character_bible: str = ""
    beat_sheet: str = ""
    
    # Module A: 小说内容
    current_episode: int = 1
    novel_content: str = ""
    
    # 对话历史（用于上下文）
    messages: List[Dict] = []
    # [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
    
    # UI状态
    waiting_for_input: bool = False  # Human-in-the-Loop标记
    ui_buttons: List[Dict] = []      # 当前显示的按钮
    
    created_at: datetime
    updated_at: datetime
```

---

## API设计

### 1. 聊天接口（SSE流式）

```python
@router.post("/api/chat")
async def chat(request: ChatRequest) -> StreamingResponse:
    """
    核心聊天接口
    
    Request:
    {
        "thread_id": "uuid",
        "message": "用户消息或action JSON",
        "user_id": "user_123"
    }
    
    Response (SSE):
    data: {"type": "token", "content": "AI生成的文字..."}\n\n
    data: {"type": "buttons", "buttons": [...]}\n\n  # 结束时发送按钮
    data: {"type": "done", "state": {...}}\n\n
    """
```

### 2. 状态查询

```python
@router.get("/api/state/{thread_id}")
async def get_state(thread_id: str) -> ConversationState:
    """获取当前对话状态"""
```

### 3. 继续执行（Human-in-the-Loop）

```python
@router.post("/api/continue")
async def continue_execution(request: ContinueRequest):
    """
    用户点击按钮后继续执行
    
    Request:
    {
        "thread_id": "uuid",
        "action": "select_plan",
        "payload": {"plan_id": "A"}
    }
    """
```

---

## 核心流程实现

### 1. 路由分发

```python
# api/chat.py

async def handle_chat(thread_id: str, message: str, user_id: str):
    # 加载状态
    state = await db.get_conversation(thread_id)
    if not state:
        state = create_new_conversation(thread_id, user_id)
    
    # 解析用户意图
    action = parse_action(message)
    
    # 根据当前阶段和action决定执行哪个chain
    if state.stage == "welcome":
        if action == "start":
            async for token in market_analyst_chain(state):
                yield token
    
    elif state.stage == "L1":
        if action == "select_genre":
            # 更新用户配置
            state.user_config = extract_config(message)
            state.stage = "L2"
            # 生成故事方案
            async for token in story_planner_chain(state):
                yield token
            state.waiting_for_input = True  # 等待用户选择
    
    elif state.stage == "L2":
        if action == "select_plan":
            # 用户选择了方案
            state.selected_plan = extract_plan(message)
            state.waiting_for_input = False
            # 继续生成人设和大纲
            async for token in skeleton_builder_chain(state):
                yield token
        elif action == "regenerate":
            # 重新生成方案
            async for token in story_planner_chain(state):
                yield token
    
    # 保存状态
    await db.save_conversation(state)
```

### 2. Chain实现

```python
# chains/story_planner.py

async def story_planner_chain(state: ConversationState):
    """生成故事方案"""
    
    # 构建prompt
    prompt = f"""
    你是一位专业的短剧编剧，擅长创作爆款短剧。
    
    用户选择的题材：{state.user_config.get('genre')}
    内容调性：{state.user_config.get('tone', [])}
    
    请为【{state.user_config.get('genre')}】赛道生成3个差异化的故事方案。
    
    每个方案包含：
    - 剧名（简短有力）
    - 一句话梗概（Logline）
    - 核心爽点
    
    最后以JSON格式输出UI按钮配置：
    ```json
    {{
      "plans": [
        {{"id": "A", "title": "方案A标题", "tagline": "简短描述"}},
        {{"id": "B", "title": "方案B标题", "tagline": "简短描述"}},
        {{"id": "C", "title": "方案C标题", "tagline": "简短描述"}}
      ],
      "buttons": [
        {{"label": "选择方案A", "action": "select_plan", "payload": {{"plan_id": "A"}}}},
        {{"label": "选择方案B", "action": "select_plan", "payload": {{"plan_id": "B"}}}},
        {{"label": "选择方案C", "action": "select_plan", "payload": {{"plan_id": "C"}}}},
        {{"label": "重新生成", "action": "regenerate", "style": "secondary"}}
      ]
    }}
    ```
    """
    
    # 调用LLM（流式）
    model = get_gemini_model()
    
    full_response = ""
    async for chunk in model.astream(prompt):
        content = chunk.content
        if content:
            full_response += content
            # 只yield文字部分，不yield JSON代码块
            if "```json" not in full_response:
                yield {"type": "token", "content": content}
    
    # 解析JSON，提取按钮
    json_match = re.search(r'```json\n(.*?)\n```', full_response, re.DOTALL)
    if json_match:
        data = json.loads(json_match.group(1))
        state.story_plans = data["plans"]
        yield {"type": "buttons", "buttons": data["buttons"]}
```

---

## 流式输出设计

### 前端接收

```javascript
// 前端SSE处理
const eventSource = new EventSource('/api/chat?...');

eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data);
    
    if (data.type === 'token') {
        // 追加文字到聊天窗口
        appendText(data.content);
    } else if (data.type === 'buttons') {
        // 显示按钮组
        showButtons(data.buttons);
    } else if (data.type === 'done') {
        // 完成，更新状态
        updateState(data.state);
        eventSource.close();
    }
};
```

### 按钮点击处理

```javascript
// 点击按钮后继续
function onButtonClick(action, payload) {
    fetch('/api/continue', {
        method: 'POST',
        body: JSON.stringify({
            thread_id: currentThreadId,
            action: action,
            payload: payload
        })
    });
    
    // 开始新的SSE连接接收结果
    startChatStream();
}
```

---

## 状态转换图

```
                    ┌─────────────┐
                    │   welcome   │
                    └──────┬──────┘
                           │ 用户输入"开始创作"
                           ▼
                    ┌─────────────┐
                    │     L1      │ ← Market Analyst
                    │   选择题材   │   (询问题材、调性)
                    └──────┬──────┘
                           │ 用户选择题材
                           ▼
                    ┌─────────────┐
                    │     L2      │ ← Story Planner
                    │   选择方案   │   (生成3个方案)
                    │  [等待输入]  │   (显示按钮，暂停)
                    └──────┬──────┘
                           │ 用户选择方案
                           ▼
                    ┌─────────────┐
                    │     L3      │ ← Skeleton Builder
                    │   确认大纲   │   (生成人设+大纲)
                    │  [等待输入]  │   (显示按钮，暂停)
                    └──────┬──────┘
                           │ 用户确认
                           ▼
                    ┌─────────────┐
                    │   writing   │ ← Novel Writer
                    │   编写小说   │   (生成完整内容)
                    └──────┬──────┘
                           │ 完成
                           ▼
                    ┌─────────────┐
                    │  completed  │
                    └─────────────┘
```

**Human-in-the-Loop标记**：
- L2和L3阶段设置 `waiting_for_input = True`
- 前端检测到后显示按钮，暂停等待
- 用户点击后调用 `/api/continue`，设置 `waiting_for_input = False`，继续执行

---

## 文件结构

```
backend_v2/                    # 全新的后端目录
├── main.py                    # FastAPI入口
├── config.py                  # 配置（数据库、API key等）
├── models/
│   ├── __init__.py
│   └── conversation.py        # ConversationState定义
├── api/
│   ├── __init__.py
│   ├── chat.py               # 核心聊天API
│   └── state.py              # 状态查询API
├── chains/
│   ├── __init__.py
│   ├── market_analyst.py     # L1: 市场分析
│   ├── story_planner.py      # L2: 故事规划
│   ├── skeleton_builder.py   # L3: 骨架构建
│   └── writer.py             # Module A: 小说写作
├── services/
│   ├── __init__.py
│   ├── db.py                 # 数据库操作
│   ├── llm.py                # LLM模型配置
│   └── prompts.py            # Prompt模板
└── tests/
    └── test_chat.py          # 测试
```

---

## 数据库Schema

```sql
-- conversations表
CREATE TABLE conversations (
    thread_id TEXT PRIMARY KEY,
    project_id TEXT,
    user_id TEXT,
    stage TEXT DEFAULT 'welcome',
    user_config JSON DEFAULT '{}',
    story_plans JSON DEFAULT '[]',
    selected_plan JSON,
    character_bible TEXT DEFAULT '',
    beat_sheet TEXT DEFAULT '',
    current_episode INTEGER DEFAULT 1,
    novel_content TEXT DEFAULT '',
    messages JSON DEFAULT '[]',
    waiting_for_input BOOLEAN DEFAULT FALSE,
    ui_buttons JSON DEFAULT '[]',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 实施步骤

1. **创建新目录** `backend_v2/`，不触碰现有混乱代码
2. **编写模型** `models/conversation.py`
3. **编写数据库服务** `services/db.py`
4. **编写Chains**（market_analyst, story_planner, skeleton_builder）
5. **编写API** `api/chat.py`（SSE流式）
6. **测试** 验证流式输出和Human-in-the-Loop
7. **切换** 前端切换到新API（或保持兼容）
8. **删除** 旧代码（确认新代码稳定后）

---

## 预期效果

- **代码量**：从2000+行减少到~300行核心逻辑
- **文件数**：从20+个减少到10个
- **调试难度**：大幅降低（单步跟踪即可）
- **流式输出**：纯文本token，无JSON污染
- **Human-in-the-Loop**：正确实现，用户确认后才继续
- **可维护性**：清晰的阶段转换，易于理解和修改
