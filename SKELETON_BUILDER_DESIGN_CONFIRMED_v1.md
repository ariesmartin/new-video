# Skeleton Builder 设计方案确认文档

**日期**: 2026-02-08
**状态**: 已确认，待实现

---

## 1. 核心设计决策

### 1.1 Graph 架构（3-Node 结构）

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
   END
```

**节点清单**:
- `validate_input`: 普通函数，检查 ending 字段
- `request_ending`: 普通函数，构建询问 UI
- `skeleton_builder`: Agent，生成完整大纲

### 1.2 Agent 内部 6 任务

基于 `prompts/3_Skeleton_Builder.md` 扩展：

| 任务 | 名称 | 强制 Tool 调用 | 输出 |
|------|------|---------------|------|
| Task 1 | Consistency Lock | 否 | 检查报告 |
| Task 2 | Character Bible | **是** `get_character_archetypes` | 角色小传（极致美丽） |
| Task 3 | Relationship Keybeats | 否 | CP 里程碑 |
| Task 4 | World Rules | 否 | 3条铁律 |
| Task 5 | Beat Sheet | **是** `get_pacing_rules` + `load_genre_context` | 分集大纲 |
| Task 6 | Tension Curve | 否 | 张力曲线数据 |

### 1.3 输入数据

```json
{
  "selected_plan": {
    "title": "方案标题",
    "logline": "一句话梗概",
    "protagonist": { "name": "...", "traits": "..." },
    "core_dilemma": "核心困境",
    "genre_combination": ["revenge", "romance"],
    "scheme_type": "A"
  },
  "user_config": {
    "total_episodes": 80,
    "setting": "现代都市",
    "ending": "HE"  // 可能缺失
  },
  "market_report": { ... }
}
```

### 1.4 缺失字段处理

**唯一必填**: `ending` (HE/BE/OE)

**自动推断**（从 selected_plan）:
- `pacing_style`: A→fast, B/C→moderate
- `romance_level`: 根据题材组合推断
- `total_episodes`: 默认为 80

### 1.5 输出数据结构

```json
{
  "skeleton": {
    "character_bible": {
      "protagonist": {
        "visual": "极致美丽描述",
        "psychology": "核心欲望+致命弱点",
        "b_story": "独立暗线"
      },
      "supporting": [...]
    },
    "relationship_keybeats": [
      {"episode": 1, "event": "相遇", "type": "met"},
      {"episode": 5, "event": "动心", "type": "spark"}
    ],
    "world_rules": ["铁律1", "铁律2", "铁律3"],
    "beat_sheet": [
      {
        "episode": 1,
        "title": "集标题",
        "key_conflict": "核心冲突",
        "cliffhanger": "钩子",
        "foreshadowing": { "plant": "伏笔", "payoff": "回收集数" }
      }
    ],
    "tension_curve": {
      "values": [88, 92, 85, ...],
      "analysis": "张力分析说明"
    }
  },
  "ui_data": {
    "ui_mode": "outline_editor",
    "editable_fields": [...],
    "actions": [...]
  }
}
```

---

## 2. 角色小传规范

### 主角（强制极致美丽）

**男主**：
- Visual: 剑眉星目 / 深邃眼眸 / 轮廓分明 / 身高185+ / 建模身材
- Psychology: 核心欲望 + 致命弱点
- B-Story: 独立暗线

**女主**：
- Visual: 明眸皓齿 / 肤若凝脂 / 气质出尘 / 身材曼妙 / 惊艳众人
- Psychology: 核心欲望 + 致命弱点
- B-Story: 独立暗线

### 配角（拒绝工具人）

- 男二/女二：与主角关系 + 自己的故事线
- 反派：合理动机（不是纯恶）

---

## 3. 前端 UI 结构

### 3.1 顶部标签栏（新增大纲标签）

```
[大纲] [小说] [剧本] [分镜] [配音] [音乐] [预览]
 ↑
新增标签（最左侧）
```

### 3.2 每个标签页内部结构

```typescript
<OutlineEditor>
  <ContentEditor />                    // 大纲内容编辑区
  <ScriptDoctor type="outline" />      // 剧本医生（大纲审阅）
  <TensionCurve 
    data={tensionCurve} 
    editable={true}                    // 大纲阶段可编辑
  />
</OutlineEditor>

<NovelEditor>
  <ContentEditor />
  <ScriptDoctor type="novel" />        // 剧本医生（小说审阅）
  <TensionCurve 
    data={novelTensionCurve} 
    editable={true}                    // 小说阶段可编辑（继承但可偏离）
    warning={deviatedFromSkeleton}     // 偏离警告
  />
</NovelEditor>

<ScriptEditor>
  <ContentEditor />
  <ScriptDoctor type="script" />       // 剧本医生（单集审阅）
  <TensionCurve 
    data={novelTensionCurve}           // 继承小说曲线
    readonly={true}                    // 剧本阶段只读
    highlightCurrent={currentEpisode}
  />
</ScriptEditor>
```

---

## 4. 审阅流程设计

### 4.1 Quality Control 独立

**不使用**架构文档定义的 3-Agent 结构（consistency_checker, character_designer, beat_sheet_planner），而是：

```
Skeleton Builder Graph（只生成，不审阅）
    ↓
用户主动触发 "剧本医生"
    ↓
Quality Control Graph（独立工作流）
    ├─ Editor Agent（审阅）
    └─ Refiner Agent（修复）
```

### 4.2 审阅 Agent 配置

使用现有 Prompt 文件：
- `prompts/7_Editor_Reviewer.md`
- `prompts/8_Refiner.md`

Agent 位置：
- `backend/agents/quality_control/editor.py`
- `backend/agents/quality_control/refiner.py`

### 4.3 审阅粒度

| 阶段 | 审阅范围 | 审阅方式 |
|------|---------|---------|
| 大纲 | **全部** 80集 | 整体结构审阅 |
| 小说 | **当前章** | 用户点击哪章审阅哪章 |
| 剧本 | **当前集** | 用户点击哪集审阅哪集 |

**解决方案**：大纲审阅和单章审阅不冲突，是不同功能入口

---

## 5. 张力曲线设计

### 5.1 数据结构

```json
{
  "tension_curve": {
    "version": "v1.0",
    "source": "skeleton",           // skeleton/novel/script/manual
    "total_points": 80,             // 根据 total_episodes 动态
    "values": [88, 92, 85, ...],
    "key_points": {
      "opening": {"episodes": "1-3", "min_value": 85},
      "paywall": {"episode": 12, "min_value": 90},
      "climax": {"episode": 70, "value": 100}
    },
    "last_modified": "2026-02-08",
    "modified_by": "user"
  }
}
```

### 5.2 阶段行为

| 阶段 | 曲线来源 | 可编辑 | 修改影响 |
|------|---------|--------|---------|
| 大纲 | 生成时计算 | ✅ 是 | 影响小说写作指导 |
| 小说 | 继承大纲 | ✅ 是（偏离警告） | 影响剧本改编 |
| 剧本 | 继承小说 | ❌ 只读 | 无（回到小说修改） |

### 5.3 修改粒度

**方案**: 支持两种粒度

1. **全量模式**: 按集修改（N 个点，N=total_episodes）
2. **关键节点模式**: 只修改关键节点（开篇、卡点、高潮）

默认使用**关键节点模式**（用户体验更好）

---

## 6. 用户上传内容处理

### 6.1 上传小说（无大纲）

**流程**：
1. 反向分析生成大纲
2. 从小说内容提取张力曲线
3. 置信度评估
4. 用户确认或调整后转为正式版

### 6.2 上传剧本（无大纲无小说）

**流程**：
1. 反向解析为小说
2. 反向生成大纲
3. 或者直接创建空大纲框架

---

## 7. 修改传播机制

### 7.1 大纲曲线修改时

```python
# 检查下游影响
if has_novel or has_script:
    return {
        "status": "warning",
        "options": [
            {
                "id": "rebuild_all",
                "label": "重新生成相关章节",
                "description": "根据新曲线重写受影响章节"
            },
            {
                "id": "keep_downstream", 
                "label": "仅修改大纲，保持下游不变",
                "description": "小说和剧本保持原节奏"
            }
        ]
    }
```

### 7.2 小说曲线偏离大纲时

显示警告但不阻止：
> ⚠️ 当前小说节奏与大纲设计有偏差（第15-20集张力过高），是否同步到大纲？

---

## 8. 待确认问题

### 8.1 已确认
- ✅ Graph 3-Node 结构
- ✅ Agent 6 任务（含张力曲线）
- ✅ 角色小传规范（极致美丽）
- ✅ 前端标签结构（大纲在最左）
- ✅ 审阅流程独立（不耦合生成）
- ✅ 张力曲线阶段行为（剧本只读）

### 8.2 待解决
- ❓ 张力曲线点数：动态根据 total_episodes？
- ❓ 审阅粒度冲突：大纲全局审阅 vs 小说单章审阅的 UI 设计

---

## 9. 下一步行动

1. 解决待确认问题
2. 编写详细技术文档
3. 实现代码

**维护者**: AI短剧生成引擎团队
**最后更新**: 2026-02-08
