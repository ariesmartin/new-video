# AI 短剧台 - 正确实施计划 (V3 文档驱动)

## 📋 执行顺序 (修正版)

### ✅ 正确的四步流程：

1. **Step 1**: 根据 `System-Architecture-V3.md` **重构后端代码**
   - 完善现有 API 实现
   - 补充缺失的 Graph 节点
   - 确保后端完全符合 V3 架构

2. **Step 2**: 根据 `Frontend-Design-V3.md` **修改新前端样式**
   - 替换色彩系统
   - 替换组件样式
   - 调整布局尺寸

3. **Step 3**: **对接前后端**
   - 新前端调用后端 V3 API
   - 补齐新前端缺失的功能逻辑

4. **Step 4**: **补充高级功能**
   - 后端添加新前端特有功能 (Inpaint/Outpaint 等)

---

## Step 1: 后端重构 (立即开始)

### 1.1 当前后端状态评估

| 模块 | 文件 | V3 要求 | 当前状态 | 需修改 |
|------|------|---------|----------|--------|
| **Projects API** | `api/projects.py` | 完整 CRUD | ✅ 已实现 | 无 |
| **Nodes API** | `api/nodes.py` | story_nodes 通用节点 | ✅ 已实现 | 无 |
| **Jobs API** | `api/jobs.py` | 异步任务队列 | ✅ 已实现 | 无 |
| **Graph API** | `api/graph.py` | SSE 流式 + Human-in-Loop | ⚠️ 基础实现 | **需完善** |
| **Models API** | `api/models.py` | 服务商 + 任务映射 | ⚠️ 部分实现 | **需完善** |
| **Action API** | ❌ 缺失 | SDUI Action 处理 | ❌ 未实现 | **需创建** |
| **Master Router** | ❌ 缺失 | 意图识别 + 路由 | ❌ 未实现 | **需创建** |
| **Module A Subgraph** | ❌ 缺失 | Writer-Editor-Refiner | ❌ 未实现 | **需创建** |
| **Module B Subgraph** | ❌ 缺失 | Script Adapter | ❌ 未实现 | **需创建** |
| **Module C Subgraph** | ❌ 缺失 | Storyboard Director | ❌ 未实现 | **需创建** |

### 1.2 后端重构任务清单

#### P0 - 核心基础 (必须先完成)

| # | 任务 | 目标文件 | 说明 |
|---|------|----------|------|
| 1 | 完善 AgentState Schema | `schemas/agent_state.py` | 按 V3 定义完整状态 |
| 2 | 创建 Master Router Node | `graph/nodes/master_router.py` | 意图识别 + 路由决策 |
| 3 | 完善 Graph API | `api/graph.py` | 补充 approve/state 接口 |
| 4 | 创建 Action API | `api/action.py` | SDUI Action 处理 |

#### P1 - LangGraph 子图 (核心功能)

| # | 任务 | 目标文件 | 说明 |
|---|------|----------|------|
| 5 | 创建 Module A Subgraph | `graph/subgraphs/module_a.py` | Writer-Editor-Refiner |
| 6 | 创建 Module B Subgraph | `graph/subgraphs/module_b.py` | Script Adapter |
| 7 | 创建 Module C Subgraph | `graph/subgraphs/module_c.py` | Storyboard Director |
| 8 | 创建主图编排 | `graph/main_graph.py` | 整合所有节点和子图 |
| 9 | 创建各 Agent Nodes | `graph/nodes/*.py` | Market/Story/Skeleton 等 |

#### P2 - 高级功能 (后续补充)

| # | 任务 | 目标文件 | 说明 |
|---|------|----------|------|
| 10 | Map-Reduce 实现 | `graph/nodes/storyboard.py` | 并发分镜生成 |
| 11 | Time Travel API | `api/graph.py` | 分支管理 |
| 12 | Live Directing | `api/graph.py` | 实时导戏 |

### 1.3 立即执行：P0 任务

#### 任务 1: 完善 AgentState Schema

**文件**: `backend/schemas/agent_state.py`

```python
# 按 V3 文档完整实现 AgentState

from typing import TypedDict, Optional, List, Dict, Any, Annotated
from langgraph.graph import MessagesState
from operator import add

class AgentState(MessagesState):
    """LangGraph Agent 全局状态 - V3 完整版"""
    
    # ===== Core Identifiers =====
    thread_id: str
    project_id: Optional[str]
    user_id: str
    
    # ===== Level 1: User Configuration =====
    user_config: Dict[str, Any]
    market_report: Optional[Dict]
    
    # ===== Level 2: Story Planning =====
    story_plans: List[Dict]
    selected_plan: Optional[Dict]
    fusion_request: Optional[Dict]
    
    # ===== Level 3: Skeleton Building =====
    character_bible: List[Dict]
    beat_sheet: List[Dict]
    
    # ===== Module A: Novel Generation =====
    current_episode: int
    novel_content: str
    novel_archive: Dict[int, str]
    
    # ===== Module B: Script Extraction =====
    script_data: List[Dict]
    narrative_mode: str
    
    # ===== Module C: Storyboard =====
    storyboard: Annotated[List[Dict], add]  # Reducer
    generation_model: str
    
    # ===== Module X: Asset Inspector =====
    asset_manifest: Dict
    asset_prompts: List[Dict]
    
    # ===== Control Flags =====
    current_stage: str
    approval_status: str
    human_feedback: str
    revision_count: int
    quality_score: float
    skill_scores: Dict[str, float]
    
    # ===== Routing Control =====
    use_master_router: bool
    routed_agent: Optional[str]
    routed_function: Optional[str]
    routed_parameters: Optional[Dict]
    
    # ===== SDUI Protocol =====
    ui_interaction: Optional[Dict]
    ui_feedback: Optional[str]
    
    # ===== Error Handling =====
    error_message: Optional[str]
    last_successful_node: Optional[str]

# 创建初始状态
def create_initial_state(
    user_id: str,
    project_id: str,
    thread_id: Optional[str] = None,
) -> AgentState:
    return AgentState(
        thread_id=thread_id or f"thread_{project_id}",
        project_id=project_id,
        user_id=user_id,
        messages=[],
        user_config={},
        story_plans=[],
        character_bible=[],
        beat_sheet=[],
        current_episode=1,
        novel_content="",
        novel_archive={},
        script_data=[],
        storyboard=[],
        current_stage="L1",
        approval_status="PENDING",
        revision_count=0,
        quality_score=100.0,
        use_master_router=True,
    )
```

#### 任务 2: 创建 Master Router Node

**文件**: `backend/graph/nodes/master_router.py`

```python
"""
Master Router Agent

意图识别 + 上下文构建 + Agent 路由 + SDUI 生成
"""

import structlog
from typing import Dict, Any
from langchain_core.messages import AIMessage

from backend.schemas.agent_state import AgentState
from backend.services.model_router import get_llm_for_task

logger = structlog.get_logger(__name__)

MASTER_ROUTER_PROMPT = """
你是 AI 短剧台的 Master Router，负责理解用户意图并路由到正确的 Agent。

当前上下文：
- 项目ID: {project_id}
- 当前阶段: {current_stage}
- 用户配置: {user_config}

用户输入: {user_message}

请分析：
1. 用户意图类型：创作/编辑/分析/生成/系统
2. 目标 Agent：Market_Analyst/Story_Planner/Skeleton_Builder/Novel_Writer/Script_Adapter/Storyboard_Director
3. 提取参数

输出 JSON 格式：
{{
    "intent": "creation|editing|analysis|generation|system",
    "target_agent": "Agent_Name",
    "parameters": {{}},
    "ui_feedback": "用户可读的反馈文本",
    "ui_interaction": {{
        "blockType": "action_group|selector|confirmation",
        "buttons": [...]
    }}
}}
"""

async def master_router_node(state: AgentState) -> Dict[str, Any]:
    """
    Master Router 节点 - 意图识别和路由决策
    """
    messages = state.get("messages", [])
    if not messages:
        return {"ui_feedback": "等待用户输入..."}
    
    # 获取最后一条用户消息
    last_message = messages[-1]
    user_message = last_message.content if hasattr(last_message, 'content') else str(last_message)
    
    logger.info("Master Router processing", message=user_message[:50])
    
    # 构建提示词
    prompt = MASTER_ROUTER_PROMPT.format(
        project_id=state.get("project_id", "unknown"),
        current_stage=state.get("current_stage", "L1"),
        user_config=state.get("user_config", {}),
        user_message=user_message,
    )
    
    # 调用 LLM
    llm = get_llm_for_task("master_brain")
    response = await llm.ainvoke([{"role": "system", "content": prompt}])
    
    # 解析响应
    try:
        import json
        result = json.loads(response.content)
        
        return {
            "routed_agent": result.get("target_agent"),
            "routed_parameters": result.get("parameters", {}),
            "ui_feedback": result.get("ui_feedback", ""),
            "ui_interaction": result.get("ui_interaction"),
            "messages": [AIMessage(content=result.get("ui_feedback", ""))],
        }
    except Exception as e:
        logger.error("Master Router parse error", error=str(e))
        return {
            "ui_feedback": "理解您的意图时出现问题，请重新描述。",
            "error_message": str(e),
        }
```

#### 任务 3: 创建 Action API

**文件**: `backend/api/action.py`

```python
"""
Action API - SDUI Action 处理

核心原则：不将按钮点击转换为聊天消息，直接处理 Action
"""

from uuid import UUID
from typing import Optional, Dict, Any
from pydantic import BaseModel
import structlog
from fastapi import APIRouter, Depends, HTTPException

from backend.schemas.common import SuccessResponse
from backend.graph import get_compiled_graph
from backend.api.deps import get_current_user_id

router = APIRouter(prefix="/action", tags=["SDUI Action"])
logger = structlog.get_logger(__name__)


class ActionRequest(BaseModel):
    """Action 请求"""
    thread_id: str
    action: str                    # 动作名称
    payload: Dict[str, Any] = {}   # 动作参数
    project_id: Optional[UUID] = None


class ActionResponse(BaseModel):
    """Action 响应"""
    success: bool
    message: str
    ui_interaction: Optional[Dict] = None
    state_updates: Dict[str, Any] = {}


@router.post("", response_model=SuccessResponse[ActionResponse])
async def handle_action(
    request: ActionRequest,
    user_id: str = Depends(get_current_user_id),
):
    """
    处理 SDUI 按钮 Action
    
    直接处理前端按钮点击，不转换为聊天消息
    """
    logger.info("Handling action", action=request.action, thread_id=request.thread_id)
    
    graph = get_compiled_graph()
    config = {"configurable": {"thread_id": request.thread_id}}
    
    # 根据 action 类型构建状态更新
    updates = _build_state_updates(request.action, request.payload)
    
    # 更新状态
    await graph.aupdate_state(config, updates)
    
    # 恢复 Graph 执行
    events = []
    async for event in graph.astream(None, config):
        events.append(event)
    
    # 获取新状态
    new_state = await graph.aget_state(config)
    
    return SuccessResponse.of(ActionResponse(
        success=True,
        message=updates.get("ui_feedback", "操作已执行"),
        ui_interaction=new_state.values.get("ui_interaction"),
        state_updates=updates,
    ))


def _build_state_updates(action: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """根据 action 构建状态更新"""
    
    action_handlers = {
        # Level 1-3 Actions
        "select_plan": lambda p: {
            "selected_plan": p.get("plan"),
            "approval_status": "APPROVED",
            "ui_feedback": f"已选择方案: {p.get('plan', {}).get('title', '未命名')}",
        },
        "approve_skeleton": lambda p: {
            "approval_status": "APPROVED",
            "ui_feedback": "大纲已确认，开始生成小说...",
        },
        
        # Module A Actions
        "next_episode": lambda p: {
            "current_episode": p.get("episode", 1),
            "ui_feedback": f"切换到第 {p.get('episode', 1)} 集",
        },
        "regenerate": lambda p: {
            "revision_count": p.get("revision_count", 0) + 1,
            "human_feedback": p.get("feedback", ""),
            "ui_feedback": "根据反馈重新生成...",
        },
        
        # Module B Actions
        "confirm_script": lambda p: {
            "approval_status": "APPROVED",
            "ui_feedback": "剧本已确认，开始拆分分镜...",
        },
        
        # Module C Actions
        "generate_shots": lambda p: {
            "ui_feedback": "开始生成分镜...",
        },
        "approve_shots": lambda p: {
            "approval_status": "APPROVED",
            "ui_feedback": "分镜已确认",
        },
    }
    
    handler = action_handlers.get(action)
    if handler:
        return handler(payload)
    
    return {"ui_feedback": f"未知 action: {action}"}
```

### 1.4 后端重构时间表

| 阶段 | 任务 | 天数 | 产出 |
|------|------|------|------|
| **P0** | AgentState + Master Router + Action API | 2天 | 核心路由可用 |
| **P1** | Module A Subgraph | 3天 | 小说生成可用 |
| **P2** | Module B Subgraph | 2天 | 剧本提取可用 |
| **P3** | Module C Subgraph | 3天 | 分镜生成可用 |
| **P4** | 整合测试 | 2天 | 完整工作流可用 |

**总计**: ~12 天完成后端重构

---

## Step 2: 新前端样式修改 (并行进行)

### 2.1 样式替换清单

| 文件 | 当前 | 目标 | 修改内容 |
|------|------|------|----------|
| `index.css` | 未知变量 | V3 色彩系统 | 完全替换 CSS 变量 |
| `components/ui/button.tsx` | shadcn 默认 | V3 样式 | Primary/Accent/Ghost |
| `components/ui/card.tsx` | 默认 | V3 Elevated | 背景/边框/阴影 |
| `components/ui/dialog.tsx` | 默认 | V3 暗色 | 背景/文字色 |
| `pages/HomePage.tsx` | 自定义布局 | V3 Dashboard | 间距/对齐 |
| `pages/ProjectPage.tsx` | 自定义 | V3 三栏 | 240/自适应/400 |

### 2.2 关键修改点

**CSS 变量替换**:
```css
/* 替换为新前端 index.css */
:root {
  /* V3 色彩系统 */
  --primary: 217 91% 60%;
  --primary-hover: 221 83% 53%;
  --accent: 24 95% 53%;
  --background: 220 25% 4%;
  --surface: 220 20% 10%;
  --elevated: 220 14% 18%;
  --text-primary: 220 13% 98%;
  --text-secondary: 220 9% 65%;
  --border: 220 13% 26%;
}
```

**布局尺寸调整**:
```tsx
// Header: 56px
// Sidebar: 240px (可折叠到 64px)
// AI Panel: 320px/400px
// 间距: 4px 基础单位
```

---

## Step 3: 前后端对接

### 3.1 API 对接清单

| 前端功能 | 后端 API | 状态 |
|----------|----------|------|
| 项目列表 | `GET /api/projects` | ✅ 可用 |
| 创建项目 | `POST /api/projects` | ✅ 可用 |
| 获取节点 | `GET /api/projects/{id}/nodes` | ✅ 可用 |
| 创建节点 | `POST /api/projects/{id}/nodes` | ✅ 可用 |
| AI 聊天 | `POST /api/graph/chat` (SSE) | ✅ 可用 |
| 用户确认 | `POST /api/graph/approve` | ✅ 可用 |
| Action 处理 | `POST /api/action` | ⚠️ Step 1 完成后 |
| 任务管理 | `GET/POST /api/jobs` | ✅ 可用 |

### 3.2 数据转换层

由于新前端使用 Card 模型，后端使用 Node 模型：

```typescript
// utils/adapter.ts

// Card → Node (发送给后端)
export const cardToNode = (card: Card): NodeCreate => ({
  type: card.type === 'scene_master' ? 'scene' : 'shot',
  content: {
    title: card.title,
    description: card.content.description,
    params: card.params,
  },
  layout: {
    position_x: card.position.x,
    position_y: card.position.y,
  },
});

// Node → Card (接收自后端)
export const nodeToCard = (node: NodeResponse): Card => ({
  id: node.node_id,
  type: node.type === 'scene' ? 'scene_master' : 'shot',
  title: node.content.title,
  position: { x: node.layout.position_x, y: node.layout.position_y },
  // ... 其他字段映射
});
```

---

## Step 4: 高级功能补充

### 4.1 后端补充功能 (新前端特有)

| 功能 | API | 优先级 |
|------|-----|--------|
| 图片生成 | `POST /api/images/generate` | P0 |
| 批量生成 | `POST /api/jobs/batch` | P0 |
| Inpaint | `POST /api/images/:id/inpaint` | P1 |
| Outpaint | `POST /api/images/:id/outpaint` | P1 |
| Virtual Camera | `POST /api/images/:id/virtual-camera` | P1 |

---

## 🚀 立即开始

### 今天执行 (Day 1)

1. ✅ **备份当前后端代码**
2. ✅ **完善 AgentState Schema** (`schemas/agent_state.py`)
3. ✅ **创建 Master Router Node** (`graph/nodes/master_router.py`)
4. ✅ **注册 Action API** (`api/action.py` + `main.py`)

### 本周目标

- **后端**: P0 完成 (AgentState + Master Router + Action API)
- **前端**: 样式替换完成
- **对接**: 基础 API 连通

---

## 📁 文档位置

- **本计划**: `/docs/CORRECT_IMPLEMENTATION_PLAN.md`
- **V3 架构**: `/System-Architecture-V3.md` (主目录)
- **V3 前端设计**: `/Frontend-Design-V3.md` (主目录)
- **V3 产品需求**: `/Product-Spec-V3.md` (主目录)

---

**计划版本**: v1.0 (修正版)  
**创建时间**: 2026-02-02  
**状态**: 准备执行 Step 1
