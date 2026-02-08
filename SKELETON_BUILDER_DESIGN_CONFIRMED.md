# Skeleton Builder 设计方案确认文档 v3.2

**日期**: 2026-02-08  
**状态**: 已确认，待实现  
**版本**: v3.2（架构修正版）

---

## 核心变更记录

### v3.2 变更（架构修正）
1. **服务分类修正**: 明确区分 Service（纯逻辑）vs Tool（需要 LLM）
2. **移除 StyleService**: 文风分析改为 Tool/Skill，由 Agent 直接调用 LLM
3. **拆分 TensionService**: 
   - 标准曲线生成 → `TensionService`（Service，纯数学公式）
   - 内容张力评估 → Tool（Skill，需要 LLM）
4. **保留 ReviewService**: 权重计算为纯逻辑，保留 Service 设计
5. **架构层级明确**: Tool/Skill（层级1）→ Agent（层级2）→ Service（层级3）

### v3.1 变更（最终架构）
1. **服务化架构**: 引入 `ReviewService`, `StyleService`, `TensionService` 独立服务
2. **风格感知修复**: Refiner Agent 增加 `Style DNA` 约束，确保文风一致
3. **通用审阅框架**: 6大分类 + Skill Review Matrix 融合，动态适配所有内容类型
4. **完整上下文注入**: 确保 Editor/Refiner 获取所有必要的元数据（ending, genre等）
5. **层级审阅**: 6大分类（宏观）+ Skill Review Matrix（微观补充）

### v2.1 变更（相比 v2.0）
1. **职责分离**: Editor 只审阅不修复, Refiner 负责修复
2. **毒舌人设**: Editor 采用毒舌剧本医生人设
3. **多题材融合**: 权重根据题材组合动态计算（非单一题材）
4. **6大分类通用**: 所有 content_type 通用, 但检查点不同
5. **角色极致美丽**: 详细定义了男主/女主的视觉和心理特征规范

---

## 1. 系统架构

### 1.1 目录结构

```
backend/
├── agents/
│   ├── skeleton_builder.py          # 大纲生成 Agent (1 Agent, 6 Tasks)
│   └── quality_control/
│       ├── editor.py                # 通用毒舌审阅 Agent
│       └── refiner.py               # 通用冷静修复 Agent
├── graph/
│   └── workflows/
│       └── skeleton_builder_graph.py # 5-Node 工作流
├── services/
│   ├── review_service.py            # ✅ 审阅逻辑 Service (权重计算/检查点映射)
│   └── tension_service.py           # ✅ 张力标准曲线 Service (数学公式)
├── skills/
│   └── content_analysis/             # ✅ 内容分析 Skills (文风/张力评估)
│       └── __init__.py
└── prompts/
    ├── 3_Skeleton_Builder.md        # 需更新 (包含 Tool 定义)
    ├── 7_Editor_Reviewer.md         # 需更新(通用版)
    └── 8_Refiner.md                 # 需更新(包含 Style Tool 定义)
```

### 1.1.1 服务分类说明

| 服务 | 是否需要 LLM | 当前设计 | 正确设计 | 说明 |
|------|------------|---------|---------|------|
| **ReviewService** | ❌ 否 | ✅ 纯逻辑计算 | **保留** | 权重计算是数学运算，不需要 LLM |
| **StyleService** | ✅ 是 | ❌ 错误！空实现 | **应该是 Tool/Skill** | 文风分析需要 LLM，不能是纯逻辑 Service |
| **TensionService** | 部分 | ⚠️ 混合 | **拆分** | 标准曲线→Service(数学)；内容评估→Tool(LLM) |

### 1.1.2 架构层级（修正版）

```
┌─────────────────────────────────────┐
│ 层级1: Tool/Skill (被Agent调用)   │
│ - analyze_style_dna (LLM分析文风)  │
│ - analyze_content_tension (LLM评估)  │
│ - get_genre_context (查询数据库)     │
└─────────────────────────────────────┘
            ↓ 被调用
┌─────────────────────────────────────┐
│ 层级2: Agent (create_react_agent)   │
│ - Skeleton Builder (调用 Tension Tool)│
│ - Editor (不需要Tool，纯审阅)        │
│ - Refiner (调用 Style Tool)          │
└─────────────────────────────────────┘
            ↓ 依赖
┌─────────────────────────────────────┐
│ 层级3: Service (纯逻辑函数)          │
│ - ReviewService (权重计算)          │
│ - TensionService (标准曲线生成)     │
└─────────────────────────────────────┘
```

### 1.2 Graph 架构（5-Node 结构）

```
START
  │
  ▼
┌─────────────────────────┐
│ validate_input          │  ← 普通函数 Node
│ 检查 ending 是否存在    │
└──────────┬──────────────┘
           │
     ┌─────┴─────┐
     ▼           ▼
[存在]       [不存在]
     │           │
     ▼           ▼
┌─────────┐  ┌─────────────────┐
│ skeleton│  │ request_ending  │  ← 普通函数 Node
│_builder │  │ 返回 UI 询问    │
│ (Agent) │  │ 然后 END        │
└────┬────┘  └─────────────────┘
     │
     ▼
┌─────────────┐
│ auto_review │  ← Agent (Editor)
│ (审阅)      │  依赖 ReviewService
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ auto_refine │  ← Agent (Refiner)
│ (修复)      │  依赖 StyleService
└──────┬──────┘
       │
       ▼
     END
```

### 1.3 Agent 职责边界（关键！）

| Agent | 人设 | 输入 | 输出 | 绝对禁止 | 服务支持 |
|-------|------|------|------|---------|---------|
| **Editor** | 🔥 毒舌剧本医生<br>暴躁、挑剔、直接 | 大纲/小说/剧本<br>+ 完整上下文 | 问题列表 + 吐槽<br>分类评分 | ❌ 给修复建议<br>❌ 说"建议..."<br>❌ 修复内容 | `ReviewService`<br>(权重/检查点) |
| **Refiner** | 🧊 冷静修复工程师<br>专业、高效、不情绪化 | Editor报告<br>+ 原始内容<br>+ Style DNA | 修复后内容<br>+ 修改清单 | ❌ 情绪化表达<br>❌ 吐槽原内容<br>❌ 只给建议不修复 | `StyleService`<br>(文风/声纹) |

**工作流程**:
```
Editor: "第15-20集烂透了！连续5集没高潮，观众早跑光了！"
    ↓
Refiner: （识别文风：快节奏爽文）→（默默修改）在第17集增加'身份揭露'冲突
    ↓
输出: 修复后大纲 + "已修复3处问题：1. 第17集增加冲突..."
```

---

## 2. 审阅体系设计

### 2.1 双层审阅架构

```
┌─────────────────────────────────────────┐
│ 第一层: 6大分类（宏观）                   │
│ 所有 content_type 通用                   │
├─────────────────────────────────────────┤
│ 逻辑/设定 │ 节奏/张力 │ 人设/角色        │
│ 冲突/事件 │ 世界/规则 │ 钩子/悬念        │
└─────────────────────────────────────────┘
                    ↓
        （如果是 novel/script/storyboard）
                    ↓
┌─────────────────────────────────────────┐
│ 第二层: Skill Review Matrix（微观）       │
│ 仅微观质量检查                           │
├─────────────────────────────────────────┤
│ S_Logic │ S_Engagement │ S_Texture       │
│ S_Human │ S_Protocol   │ ...             │
└─────────────────────────────────────────┘
```

### 2.2 6大分类详细定义（通用框架）

```python
REVIEW_CATEGORIES = {
    "logic": {
        "label": "逻辑/设定",
        "icon": "🧠",
        "color": "#3B82F6",
        "checkpoints": {
            "outline": ["大纲结构完整", "世界观一致性", "时间线合理性"],
            "novel": ["因果逻辑通顺", "无吃书现象", "设定前后一致"],
            "script": ["场景逻辑合理", "道具一致性", "转场流畅"],
            "storyboard": ["镜头逻辑", "跳轴检查", "空间一致性"]
        }
    },
    "pacing": {
        "label": "节奏/张力",
        "icon": "📈",
        "color": "#F97316",
        "checkpoints": {
            "outline": ["整体节奏曲线", "高潮位置(87.5%)", "卡点张力", "开篇钩子"],
            "novel": ["每章爽点密度", "情绪高低起伏", "无拖沓段落"],
            "script": ["每集节奏", "场景时长分配", "转场节奏"],
            "storyboard": ["镜头时长", "剪辑节奏", "视觉张力"]
        }
    },
    "character": {
        "label": "人设/角色",
        "icon": "👤",
        "color": "#A855F7",
        "checkpoints": {
            "outline": ["角色小传完整", "极致美丽达标", "B-Story存在", "拒绝工具人"],
            "novel": ["行为一致性", "成长弧光", "台词符合人设"],
            "script": ["表演指导", "情绪层次", "角色关系动态"],
            "storyboard": ["角色造型一致", "表情神态", "动作设计"]
        }
    },
    "conflict": {
        "label": "冲突/事件",
        "icon": "⚔️",
        "color": "#EF4444",
        "checkpoints": {
            "outline": ["核心冲突明确", "冲突升级路径", "爽点分布", "反转设计"],
            "novel": ["冲突升级", "反转合理性", "爽点密度", "事件冗余"],
            "script": ["戏剧冲突", "场景张力", "高潮呈现"],
            "storyboard": ["动作设计", "冲突可视化", "冲击力"]
        }
    },
    "world": {
        "label": "世界/规则",
        "icon": "🌍",
        "color": "#22C55E",
        "checkpoints": {
            "outline": ["3条铁律明确", "战力平衡", "规则一致性"],
            "novel": ["规则遵守", "设定一致性", "无战力崩坏"],
            "script": ["场景设定", "特效可行性", "逻辑自洽"],
            "storyboard": ["场景细节", "道具准确性", "环境氛围"]
        }
    },
    "hook": {
        "label": "钩子/悬念",
        "icon": "🪝",
        "color": "#EAB308",
        "checkpoints": {
            "outline": ["前3秒钩子", "每集cliffhanger", "付费卡点悬念", "伏笔回收"],
            "novel": ["章节结尾", "悬念留存", "情绪高点"],
            "script": ["镜头钩子", "转场悬念", "情绪峰值"],
            "storyboard": ["视觉冲击", "构图吸引力", "色彩情绪"]
        }
    }
}
```

### 2.3 Skill Review Matrix（微观补充层）

```python
# 仅 novel/script/storyboard 使用
SKILL_REVIEW_MATRIX = {
    "S_Protocol": {
        "label": "协议合规性",
        "applies_to": ["script", "storyboard"],
        "checks": ["格式规范", "字段完整", "命名规范"]
    },
    "S_Logic": {
        "label": "逻辑卫士",
        "applies_to": ["novel", "script"],
        "checks": ["因果检查", "弧光检查", "吃书检查"]
    },
    "S_Engagement": {
        "label": "吸引力",
        "applies_to": ["novel", "script"],
        "checks": ["爽点密度", "钩子检查", "情绪曲线"]
    },
    "S_Texture": {
        "label": "文学质感",
        "applies_to": ["novel"],  # 仅小说
        "checks": ["五感描写", "共情能力", "环境投射"]
    },
    "S_Human": {
        "label": "拟真度",
        "applies_to": ["novel", "script"],
        "checks": ["对话自然", "反套路", "潜台词"]
    }
}
```

---

## 3. 多题材融合权重设计

### 3.1 权重计算逻辑

```python
def calculate_weights(genre_combination: List[str]) -> Dict[str, float]:
    """
    根据题材组合计算6大分类权重
    例如: ["revenge", "romance"] → 复仇甜宠
    """
    
    # 基础权重表（单题材）
    BASE_WEIGHTS = {
        "revenge": {      # 复仇爽剧
            "logic": 0.10, "pacing": 0.30, "character": 0.10,
            "conflict": 0.25, "world": 0.05, "hook": 0.20
        },
        "romance": {      # 甜宠
            "logic": 0.10, "pacing": 0.20, "character": 0.30,
            "conflict": 0.10, "world": 0.05, "hook": 0.25
        },
        "suspense": {     # 悬疑
            "logic": 0.30, "pacing": 0.20, "character": 0.05,
            "conflict": 0.05, "world": 0.15, "hook": 0.25
        },
        "transmigration": {  # 穿越重生
            "logic": 0.20, "pacing": 0.25, "character": 0.15,
            "conflict": 0.20, "world": 0.10, "hook": 0.10
        },
        "family": {       # 家庭伦理
            "logic": 0.20, "pacing": 0.05, "character": 0.30,
            "conflict": 0.15, "world": 0.25, "hook": 0.05
        }
    }
    
    # 融合计算：加权平均
    combined = {key: 0.0 for key in BASE_WEIGHTS["revenge"].keys()}
    
    for genre in genre_combination:
        weights = BASE_WEIGHTS.get(genre, BASE_WEIGHTS["revenge"])
        for key in combined:
            combined[key] += weights[key] / len(genre_combination)
    
    # 归一化
    total = sum(combined.values())
    return {k: round(v/total, 2) for k, v in combined.items()}


# 示例计算
# ["revenge", "romance"]:
#   logic: (0.10+0.10)/2=0.10
#   pacing: (0.30+0.20)/2=0.25
#   character: (0.10+0.30)/2=0.20
#   conflict: (0.25+0.10)/2=0.175
#   world: (0.05+0.05)/2=0.05
#   hook: (0.20+0.25)/2=0.225
```

### 3.2 常见组合权重示例

| 题材组合 | 最高权重维度 | 特点 |
|---------|-------------|------|
| **复仇+甜宠** | pacing(0.25), hook(0.225), character(0.20) | 爽感+情感并重 |
| **悬疑+甜宠** | logic(0.20), hook(0.25), character(0.175) | 智力+情感 |
| **复仇+悬疑** | logic(0.20), pacing(0.25), conflict(0.15) | 高能+烧脑 |
| **穿越+甜宠** | character(0.225), pacing(0.225), hook(0.175) | 人设+节奏 |
| **家庭+甜宠** | character(0.30), world(0.15), logic(0.15) | 情感+现实 |

### 3.3 Prompt 动态注入

```markdown
## 审阅权重配置（根据题材组合动态计算）

题材组合: {genre_combination}

计算后权重:
- 🧠 逻辑/设定: {logic_weight}% — 侧重检查: {logic_checkpoints}
- 📈 节奏/张力: {pacing_weight}% — 侧重检查: {pacing_checkpoints}
- 👤 人设/角色: {character_weight}% — 侧重检查: {character_checkpoints}
- ⚔️ 冲突/事件: {conflict_weight}% — 侧重检查: {conflict_checkpoints}
- 🌍 世界/规则: {world_weight}% — 侧重检查: {world_checkpoints}
- 🪝 钩子/悬念: {hook_weight}% — 侧重检查: {hook_checkpoints}

审阅时按此权重侧重检查,权重高的维度问题严重性加倍。
```

---

## 4. Editor Agent 设计（毒舌审阅官）

### 4.1 人设设定

```markdown
# System Prompt: AI Editor (毒舌审阅版)

## Role
你是短剧界最挑剔的制片人,眼睛里揉不得沙子。
你的口头禅是: "这也能播?"

**性格特征**:
- 🔥 直接: 有问题直说,不绕弯子
- 🗡️ 毒舌: 吐槽精准,一针见血
- 📊 专业: 每句话都有数据支撑
- ❌ 不干活: 只找问题,不负责修复(那是Refiner的事)

**语言风格示例**:
❌ 错误示范: "这部分节奏稍显缓慢,建议调整。"
✅ 正确示范: "第15-20集烂透了!连续5集没高潮,观众早跑光了!"

**绝对禁止**:
- 禁止给出修复建议(不要说"建议增加...")
- 禁止温和表达
- 禁止修复内容(只审阅不修复)

**必须输出**:
- 问题位置
- 问题严重程度
- 毒舌吐槽
- 分类归属
```

### 4.2 严重程度分级

```python
SEVERITY_LEVELS = {
    "critical": {
        "label": "致命",
        "color": "#DC2626",
        "icon": "🔴",
        "editor_comment": "这也能播?立刻给我改!",
        "score_threshold": 0,      # 0-59分
        "examples": ["结局逻辑崩坏", "主角人设全崩", "付费卡点无力"]
    },
    "high": {
        "label": "严重",
        "color": "#EA580C",
        "icon": "🟠",
        "editor_comment": "问题很大,不想被骂就改!",
        "score_threshold": 60,     # 60-74分
        "examples": ["连续5集平淡", "核心冲突模糊", "人设工具人"]
    },
    "medium": {
        "label": "警告",
        "color": "#EAB308",
        "icon": "🟡",
        "editor_comment": "小问题,但影响质感。",
        "score_threshold": 75,     # 75-84分
        "examples": ["某集钩子弱", "细节逻辑漏洞", "节奏稍慢"]
    },
    "low": {
        "label": "提示",
        "color": "#6B7280",
        "icon": "⚪",
        "editor_comment": "挑刺的话可以说,但问题不大。",
        "score_threshold": 85,     # 85-100分
        "examples": ["某句台词可以更精炼", "某场景可删减"]
    }
}
```

### 4.3 输出格式

```json
{
  "overall_score": 75,
  "verdict": "勉强及格,但第15-20集烂得像老太太裹脚布!",
  
  "weights_applied": {
    "genre_combination": ["revenge", "romance"],
    "logic": 0.10,
    "pacing": 0.25,
    "character": 0.20,
    "conflict": 0.175,
    "world": 0.05,
    "hook": 0.225
  },
  
  "categories": {
    "logic": {
      "score": 88,
      "weight": 0.10,
      "weighted_score": 8.8,
      "comment": "逻辑还行,没出大岔子。",
      "issues_count": 1
    },
    "pacing": {
      "score": 65,
      "weight": 0.25,
      "weighted_score": 16.25,
      "comment": "烂透了!第15-20集节奏像便秘!",
      "issues_count": 3
    }
  },
  
  "issues": [
    {
      "id": 1,
      "category": "pacing",
      "severity": "high",
      "score": 60,
      "location": "第15-20集",
      "title": "连续5集节奏拖沓",
      "description": "你是想让观众睡着吗?连续5集没高潮,完播率肯定崩!",
      "affected_weight": 0.25
      // 注意: 没有 fix_suggestion,那是Refiner的事
    }
  ],
  
  "one_sentence_diagnosis": "大纲骨架还行,但第10-30集节奏像便秘,赶紧通一通!",
  "editor_mood": "暴躁但还算满意"
}
```

---

## 5. Refiner Agent 设计（冷静修复工程师）

### 5.1 人设设定（修正版：Tool 集成）

```markdown
# System Prompt: AI Refiner (Style-Aware 修复版 v3.0)

## Role
你是资深内容修复工程师，擅长在保持原文风的前提下进行外科手术式修复。

**性格特征**:
- 🧊 冷静: 不被Editor的情绪影响
- 🔧 专业: 给出精准修复方案
- 📋 详细: 列出所有修改清单
- ✅ 执行: 直接修复,不只是建议

**输入上下文**:
- **Content Type**: {content_type}
- **Original Content**: {content}
- **Issues**: {issues}
- **Context Before**: {context_before}
- **Context After**: {context_after}

**可用工具**:
- `analyze_style_dna`: 分析文本的Style DNA (LLM分析)
- `extract_character_voices`: 从角色小传提取声纹特征

**核心原则 (Style Consistency)**:
1. **文风一致**: 修复部分的用词、句式必须与原文完全一致。
   - *Example*: 原文是"那人似笑非笑"，修复不能写成"那男的嘿嘿一笑"。
   - *Check*: 调用 `analyze_style_dna` 工具获取文风特征，确保修复匹配
2. **人设一致**: 修复后的台词必须符合角色性格。
   - *Example*: 高冷男主不能说"哎呀妈呀"。
   - *Check*: 调用 `extract_character_voices` 工具获取角色声纹，确保台词符合人设
3. **无缝衔接**: 修复内容必须能流畅连接前文和后文。
   - *Check*: 修复内容插入 context_before 和 context_after 之间，确保自然流畅

**工作流**:
1. 接收 Editor 的问题列表
2. 调用 `analyze_style_dna({content})` 获取文风特征
3. 调用 `extract_character_voices({character_bible})` 获取角色声纹
4. 基于文风和人设进行修复
5. 确保修复内容能流畅连接 context_before 和 context_after

**语言风格**:
冷静、专业、不情绪化、不吐槽

**绝对禁止**:
- 禁止吐槽原内容(不要说"写得很烂")
- 禁止情绪化表达
- 禁止只给建议不修复
```

### 5.2 修复策略

```python
REFINE_STRATEGIES = {
    "pacing": {
        "slow_middle": {
            "detection": "连续N集张力<40",
            "action": "插入冲突事件或合并场景",
            "examples": ["增加身份揭露", "加速矛盾升级"]
        },
        "weak_opening": {
            "detection": "前3集张力<85",
            "action": "强化开篇钩子",
            "examples": ["增加视觉冲击", "提前抛出悬念"]
        }
    },
    "character": {
        "flat_protagonist": {
            "detection": "缺乏B-Story或成长弧光",
            "action": "增加独立暗线或转变节点",
            "examples": ["设计隐藏身份", "规划觉醒时刻"]
        },
        "tool_supporting": {
            "detection": "配角无独立故事线",
            "action": "赋予配角独立动机和故事",
            "examples": ["男二增加暗恋线", "反派增加背景故事"]
        }
    },
    "hook": {
        "weak_cliffhanger": {
            "detection": "卡点张力<90",
            "action": "强化悬念或增加反转",
            "examples": ["身份揭露", "危机突降"]
        }
    }
}
```

### 5.3 Tool 定义（修正版：Service → Tool）

#### 5.3.1 analyze_style_dna Tool

```python
# backend/skills/content_analysis/__init__.py

from langchain_core.tools import tool

@tool
def analyze_style_dna(sample_text: str) -> str:
    """
    Skill: 分析文本的 Style DNA（文风基因）
    
    使用 LLM 分析文本的语言风格特征，包括：
    - 语言风格（古风/现代/幽默/严肃）
    - 叙事视角（第一人称/第三人称）
    - 描写密度（详尽/简练）
    - 句式特点（长句/短句/长短结合）
    
    Args:
        sample_text: 待分析的文本样本（建议 200-500 字）
    
    Returns:
        文风特征描述，格式如："古风、辞藻华丽、第一人称、短句为主"
    """
    # 这是一个 Tool，由 Agent 调用 LLM 进行分析
    # LLM 会根据 sample_text 分析出文风特征
    pass  # 实际实现中，这里会调用 LLM 并返回分析结果
```

**使用示例（在 Refiner Agent Prompt 中）**:
```markdown
你是一个内容修复工程师。

**可用的工具**:
- `analyze_style_dna`: 分析文本的文风特征

**使用流程**:
1. 接收到 {content} 后，调用 `analyze_style_dna({content})` 获取文风特征
2. 基于文风特征进行修复
3. 确保修复后的文本符合文风特征
```

#### 5.3.2 extract_character_voices Tool

```python
# backend/skills/content_analysis/__init__.py

from langchain_core.tools import tool

@tool
def extract_character_voices(character_bible: dict) -> str:
    """
    Skill: 从角色小传提取角色声纹特征
    
    从 character_bible 中提取每个角色的说话方式和性格特征。
    如果 bible 信息不足，使用 LLM 基于角色描述推断声纹特征。
    
    Args:
        character_bible: 角色小传字典，包含 name, traits, description 等字段
    
    Returns:
        角色声纹描述，格式如："男主：冷峻、惜字如金；女主：温婉、内心坚韧"
    """
    # 如果 character_bible 信息完整，可以直接提取
    # 如果信息不足，调用 LLM 基于描述推断
    pass  # 实际实现
```

#### 5.3.3 分析内容张力 Tool（修正版：Service → Tool）

```python
# backend/skills/content_analysis/__init__.py

from langchain_core.tools import tool

@tool
def analyze_content_tension(episode_summary: str) -> int:
    """
    Skill: 分析单集内容的张力值
    
    使用 LLM 评估单集内容的张力，返回 0-100 的分数。
    
    评估维度：
    - 冲突强度（0-25分）
    - 情绪起伏（0-25分）
    - 悬念设置（0-25分）
    - 高潮爆发（0-25分）
    
    Args:
        episode_summary: 单集内容摘要（建议 300-500 字）
    
    Returns:
        张力值（0-100）
    """
    # 使用 LLM 评估后返回分数
    pass  # 实际实现
```

**注意**: `generate_tension_curve(total_episodes)` 仍然是 Service（纯数学公式），不涉及 LLM。
```
# backend/services/tension_service.py

class TensionService:
    """张力曲线计算服务（纯数学公式，不涉及 LLM）"""
    
    def generate_tension_curve(self, total_episodes: int) -> list[int]:
        """
        根据戏剧性结构生成标准张力曲线
        
        使用黄金前三集 + 爽点分布算法生成标准曲线。
        这是纯数学计算，不需要 LLM。
        
        Args:
            total_episodes: 总集数
        
        Returns:
            张力值列表，长度为 total_episodes，每个值 0-100
        """
        # 数学公式实现
        pass
```

### 5.3 输出格式

```json
{
  "refined_content": {
    // 修复后的完整大纲
  },
  
  "change_log": [
    {
      "issue_id": 1,
      "category": "pacing",
      "change_type": "add_conflict",
      "location": "第17集",
      "description": "增加'身份揭露'冲突事件,提升张力",
      "before": "第17集: 主角继续隐藏身份...",
      "after": "第17集: 反派设计陷阱,主角被迫暴露真实身份,张力升级...",
      "impact": "该集张力从45提升至92"
    },
    {
      "issue_id": 2,
      "category": "character",
      "change_type": "enhance_b_story",
      "location": "男二角色",
      "description": "增加男二独立暗线",
      "before": "男二: 单纯助攻主角...",
      "after": "男二: 表面助攻,实则是敌对势力卧底,内心挣扎...",
      "impact": "丰富配角层次,增加戏剧张力"
    }
  ],
  
  "summary": {
    "total_changes": 5,
    "critical_fixed": 2,
    "high_fixed": 2,
    "medium_fixed": 1,
    "overall_improvement": "+13分 (75→88)"
  }
}
```

---

## 6. Skeleton Builder Graph 完整结构

```python
# backend/graph/workflows/skeleton_builder_graph.py

def build_skeleton_builder_graph(user_id: str):
    """
    大纲构建工作流
    5-Node结构: validate → request_ending(conditional) → skeleton_builder → editor → refiner
    """
    
    workflow = StateGraph(AgentState)
    
    # Node 1: 输入验证
    workflow.add_node("validate_input", validate_input_node)
    
    # Node 2: 请求ending(如缺失)
    workflow.add_node("request_ending", request_ending_node)
    
    # Node 3: 生成大纲(6任务)
    workflow.add_node("skeleton_builder", create_skeleton_builder_agent(user_id))
    
    # Node 4: 毒舌审阅(只审阅不修复)
    workflow.add_node("editor", create_editor_agent(user_id, content_type="outline"))
    
    # Node 5: 冷静修复(根据审阅结果修复)
    workflow.add_node("refiner", create_refiner_agent(user_id, content_type="outline"))
    
    # 流程定义
    workflow.set_entry_point("validate_input")
    
    # 条件分支: ending是否存在?
    workflow.add_conditional_edges(
        "validate_input",
        route_after_validation,
        {
            "complete": "skeleton_builder",
            "incomplete": "request_ending"
        }
    )
    
    # request_ending后结束(等待用户)
    workflow.add_edge("request_ending", END)
    
    # skeleton_builder → editor → refiner → END
    workflow.add_edge("skeleton_builder", "editor")
    workflow.add_edge("editor", "refiner")
    workflow.add_edge("refiner", END)
    
    return workflow.compile()


def validate_input_node(state: AgentState) -> AgentState:
    """检查ending字段,自动推断其他配置"""
    user_config = state.get("user_config", {})
    selected_plan = state.get("selected_plan", {})
    
    # 检查ending
    if not user_config.get("ending"):
        return {
            **state,
            "validation_status": "incomplete",
            "missing_fields": ["ending"]
        }
    
    # 自动推断配置
    inferred = infer_config_from_plan(selected_plan)
    
    return {
        **state,
        "validation_status": "complete",
        "inferred_config": inferred
    }


def create_editor_agent(user_id: str, content_type: str, context: dict):
    """创建毒舌审阅 Agent"""
    
    from backend.services.review_service import ReviewService
    
    review_service = ReviewService()
    
    # 准备 Prompt 变量
    genre_combo = context.get("genre_combination", [])
    weights = review_service.calculate_weights(genre_combo)
    checkpoints = review_service.get_checkpoints(content_type)
    
    # 加载 Prompt 并注入变量
    prompt = load_editor_prompt().format(
        content_type=content_type,
        genre_combination=genre_combo,
        ending=context.get("ending", "HE"),
        total_episodes=context.get("total_episodes", 80),
        logic_weight=weights.get("logic", 0.10),
        logic_checkpoints=checkpoints.get("logic", []),
        pacing_weight=weights.get("pacing", 0.25),
        pacing_checkpoints=checkpoints.get("pacing", []),
        character_weight=weights.get("character", 0.20),
        character_checkpoints=checkpoints.get("character", []),
        conflict_weight=weights.get("conflict", 0.175),
        conflict_checkpoints=checkpoints.get("conflict", []),
        world_weight=weights.get("world", 0.05),
        world_checkpoints=checkpoints.get("world", []),
        hook_weight=weights.get("hook", 0.225),
        hook_checkpoints=checkpoints.get("hook", []),
    )
    
    return create_react_agent(
        model=get_model(user_id, TaskType.EDITOR),
        tools=[],  # Editor不需要Tools,纯审阅
        prompt=prompt
    )


def create_refiner_agent(user_id: str, content_type: str, context: dict):
    """创建冷静修复 Agent（Tool 方式）"""
    
    from backend.skills.content_analysis import (
        analyze_style_dna,
        extract_character_voices,
    )
    from backend.services.review_service import ReviewService
    from backend.services.tension_service import TensionService
    
    review_service = ReviewService()
    tension_service = TensionService()
    
    # 准备 Prompt 变量
    # 注意：style_dna 和 character_voices 不在这里计算！
    # 而是由 Agent 调用 Tool 在运行时获取
    weights = review_service.calculate_weights(context.get("genre_combination", []))
    
    # 加载 Prompt
    prompt = load_refiner_prompt().format(
        content_type=content_type,
        # style_dna 和 character_voices 不在这里注入！
        # Agent 会通过调用 Tool 获取这些信息
    )
    
    return create_react_agent(
        model=get_model(user_id, TaskType.REFINER),
        tools=[analyze_style_dna, extract_character_voices],  # ✅ 传入 Tools
        prompt=prompt
    )
```

---

## 7. 输入输出数据规范

### 7.1 完整输入

```json
{
  "selected_plan": {
    "title": "《豪门弃妇是满级太奶奶》",
    "logline": "被扫地出门的弃妇,竟是顶级财阀的太奶奶...",
    "protagonist": {
      "name": "林晚晴",
      "traits": "隐忍、聪慧、马甲大佬",
      "appearance": "表面温婉,实则气场全开"
    },
    "core_dilemma": "家族仇恨与真爱的抉择",
    "genre_combination": ["revenge", "romance", "family"],  // 多题材融合
    "scheme_type": "A",
    "opening_hook": "被当众羞辱退婚",
    "paywall_design": {"episode": 12, "event": "身份揭露"}
  },
  "user_config": {
    "total_episodes": 80,  // 动态,非固定80
    "setting": "现代都市",
    "ending": "HE"
  },
  "market_report": {
    "target_audience": "25-35岁女性",
    "trending_elements": ["马甲", "打脸", "甜宠"]
  }
}
```

### 7.2 完整输出

```json
{
  "skeleton": {
    "version": "v1.0",
    "character_bible": {...},
    "relationship_keybeats": [...],
    "world_rules": [...],
    "beat_sheet": [...],
    "tension_curve": {
      "total_points": 80,  // 根据total_episodes动态
      "values": [88, 92, 85, ...],
      "key_points": {...}
    }
  },
  
  "review_report": {
    "overall_score": 88,
    "verdict": "还行,勉强能看",
    "weights_applied": {...},
    "categories": {...},
    "issues": [...]
  },
  
  "refine_log": {
    "total_changes": 3,
    "changes": [...],
    "improvement": "+13分"
  },
  
  "ui_data": {
    "ui_mode": "outline_editor",
    "editable_fields": [...],
    "actions": [
      {"id": "confirm", "label": "确认大纲", "style": "primary"},
      {"id": "regenerate", "label": "重新生成", "style": "secondary"}
    ]
  }
}
```

---

## 9. v3.2 架构修正说明

### 9.1 修正原因

在 v3.1 版本中发现以下架构问题：

#### 问题 1: StyleService 错误设计
**错误**: 将 StyleService 设计为纯逻辑 Service，但实际上文风分析需要 LLM。

```python
# ❌ 错误设计（v3.1）
class StyleService:
    def analyze_style_dna(self, sample_text: str) -> str:
        pass  # 空实现，无法真正分析文风！
```

**后果**: 
- `analyze_style_dna()` 无法真正实现
- Refiner Agent 无法获取文风特征
- 文风一致性要求无法满足

#### 问题 2: TensionService 混合设计
**错误**: 将标准曲线生成和内容张力评估都放在同一个 Service 中。

```python
# ⚠️ 混合设计（v3.1）
class TensionService:
    def generate_tension_curve(self, total_episodes: int):
        # 数学公式，不需要 LLM
        return curve_values
    
    def analyze_content_tension(self, episode_summary: str) -> int:
        # 需要 LLM 分析，不应是 Service
        pass
```

**后果**: 
- Service 职责不清晰
- 无法遵循 LangGraph 的 Service/Tool 分层架构

#### 问题 3: Refiner Agent 缺少 Tools
**错误**: Refiner Agent 的 `tools=[]`，无法调用任何 Tool。

```python
# ❌ 错误设计（v3.1）
def create_refiner_agent(user_id: str, content_type: str):
    return create_react_agent(
        model=get_model(user_id, TaskType.REFINER),
        tools=[],  # Refiner也不需要Tools,纯修复逻辑
        prompt=prompt
    )
```

**后果**: 
- Refiner 无法调用 `analyze_style_dna` Tool
- 无法调用 `extract_character_voices` Tool
- 无法获取文风和角色声纹信息

### 9.2 修正方案

#### 修正 1: 移除 StyleService，改为 Tool

```python
# ✅ 正确设计（v3.2）
# backend/skills/content_analysis/__init__.py

from langchain_core.tools import tool

@tool
def analyze_style_dna(sample_text: str) -> str:
    """
    Skill: 分析文本的 Style DNA（文风基因）
    
    使用 LLM 分析文本的语言风格特征。
    这是 Tool，由 Agent 调用 LLM 实现。
    """
    # LLM 分析实现
    pass
```

#### 修正 2: 拆分 TensionService

```python
# ✅ 正确设计（v3.2）

# Service 层（纯数学公式）
# backend/services/tension_service.py
class TensionService:
    def generate_tension_curve(self, total_episodes: int) -> list[int]:
        """根据戏剧性结构生成标准张力曲线（数学公式）"""
        pass

# Tool 层（需要 LLM）
# backend/skills/content_analysis/__init__.py
@tool
def analyze_content_tension(episode_summary: str) -> int:
    """
    Skill: 分析单集内容的张力值
    
    使用 LLM 评估单集内容的张力，返回 0-100 的分数。
    """
    # LLM 分析实现
    pass
```

#### 修正 3: Refiner Agent 增加 Tools

```python
# ✅ 正确设计（v3.2）
def create_refiner_agent(user_id: str, content_type: str, context: dict):
    """创建冷静修复 Agent（Tool 方式）"""
    
    from backend.skills.content_analysis import (
        analyze_style_dna,
        extract_character_voices,
    )
    
    return create_react_agent(
        model=get_model(user_id, TaskType.REFINER),
        tools=[analyze_style_dna, extract_character_voices],  # ✅ 传入 Tools
        prompt=prompt
    )
```

### 9.3 修正后的架构层级

```
┌─────────────────────────────────────┐
│ 层级1: Tool/Skill (被Agent调用)   │
│ - analyze_style_dna (LLM分析文风)  │
│ - extract_character_voices (LLM提取)  │
│ - analyze_content_tension (LLM评估)  │
│ - get_genre_context (查询数据库)      │
└─────────────────────────────────────┘
            ↓ 被调用
┌─────────────────────────────────────┐
│ 层级2: Agent (create_react_agent)   │
│ - Skeleton Builder (调用 Tool)      │
│ - Editor (纯审阅,不需要Tool)       │
│ - Refiner (调用 Style Tool)         │
└─────────────────────────────────────┘
            ↓ 依赖
┌─────────────────────────────────────┐
│ 层级3: Service (纯逻辑函数)          │
│ - ReviewService (权重计算)          │
│ - TensionService (标准曲线生成)     │
└─────────────────────────────────────┘
```

### 9.4 实现优先级（修正版）

**P0(核心)**:
1. `backend/services/review_service.py` - 实现纯逻辑 Service（权重计算）
2. `backend/services/tension_service.py` - 实现纯数学 Service（标准曲线）
3. `backend/skills/content_analysis/__init__.py` - 实现 3 个 Tools（文风/声纹/张力）
4. `backend/agents/quality_control/refiner.py` - 实现 Agent（集成 Tools）
5. `backend/agents/skeleton_builder.py` - 实现 Agent（集成 Tools）

**P1(审阅修复)**:
6. `prompts/3_Skeleton_Builder.md` - 更新 Prompt（包含 Tool 定义）
7. `prompts/8_Refiner.md` - 更新 Prompt（包含 Tool 调用说明）
8. `backend/agents/quality_control/editor.py` - 实现 Agent（集成 ReviewService）

**P2(前端)**:
9. 张力曲线可视化
10. 审阅分类UI(6大分类标签+毒舌评语)
11. 修改清单展示

---

## 10. 文档历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2026-02-08 | 初始设计(3-Node,无审阅) |
| v2.0 | 2026-02-08 | 增加自动审阅修复、6大分类、动态张力曲线 |
| v2.1 | 2026-02-08 | 职责分离(Editor/Refiner)、毒舌人设、多题材权重、6大分类通用化 |
| v3.1 | 2026-02-08 | 服务化架构（StyleService + TensionService）、风格感知修复、完整上下文注入 |
| **v3.2** | **2026-02-08** | **架构修正：Service分类修正、移除 StyleService（改为 Tool）、拆分 TensionService、Refiner 增加 Tools** |
