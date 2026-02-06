# AI 短剧台 - 数据库 Schema 文档

## 概述

本项目使用 **Supabase (PostgreSQL)** 作为数据库，通过 PostgREST API 进行访问。

## 表结构

### 1. projects - 项目表

存储用户创建的项目信息。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键，项目唯一标识 |
| user_id | UUID | 外键，关联用户 |
| name | TEXT | 项目名称 |
| cover_image | TEXT | 封面图片 URL |
| meta | JSONB | 项目元数据（题材、调性等配置） |
| created_at | TIMESTAMPTZ | 创建时间 |
| updated_at | TIMESTAMPTZ | 更新时间 |

**RLS 策略**: 用户只能访问自己的项目

### 2. story_nodes - 内容节点表

通用节点系统，存储所有类型的内容节点。

| 字段 | 类型 | 说明 |
|------|------|------|
| node_id | UUID | 主键，节点唯一标识 |
| project_id | UUID | 外键，关联项目 |
| parent_id | UUID | 父节点 ID（用于构建树结构） |
| type | TEXT | 节点类型（见 NodeType 枚举） |
| content | JSONB | 节点内容（根据类型变化） |
| created_at | TIMESTAMPTZ | 创建时间 |
| updated_at | TIMESTAMPTZ | 更新时间 |

**节点类型 (NodeType)**:
- `config` - 项目配置节点
- `market_report` - 市场分析报告
- `story_plan` - 故事方案
- `character` - 角色设定
- `outline` - 分集大纲
- `episode_outline` - 单集大纲
- `novel_chapter` - 小说章节
- `script_scene` - 剧本场景
- `storyboard_shot` - 分镜
- `asset` - 资产（角色/场景/道具）
- `video` - 视频结果
- `note` - 用户笔记

**RLS 策略**: 用户只能访问自己项目的节点

### 3. node_layouts - 节点布局表

存储节点在画布上的位置和布局信息。

| 字段 | 类型 | 说明 |
|------|------|------|
| node_id | UUID | 主键，关联 story_nodes |
| canvas_tab | TEXT | 画布标签（novel/drama/asset） |
| position_x | FLOAT | X 坐标 |
| position_y | FLOAT | Y 坐标 |
| updated_at | TIMESTAMPTZ | 更新时间 |

**RLS 策略**: 用户只能访问自己项目的节点布局

### 4. job_queue - 任务队列表

存储异步任务，用于视频生成等耗时操作。

| 字段 | 类型 | 说明 |
|------|------|------|
| job_id | UUID | 主键，任务唯一标识 |
| project_id | UUID | 外键，关联项目 |
| type | TEXT | 任务类型 |
| status | TEXT | 任务状态（pending/running/completed/failed/cancelled） |
| priority | INT | 优先级（1-10） |
| input_payload | JSONB | 输入参数 |
| output_payload | JSONB | 输出结果 |
| progress_percent | INT | 进度百分比 |
| current_step | TEXT | 当前步骤描述 |
| error_message | TEXT | 错误信息 |
| started_at | TIMESTAMPTZ | 开始时间 |
| ended_at | TIMESTAMPTZ | 结束时间 |
| created_at | TIMESTAMPTZ | 创建时间 |
| updated_at | TIMESTAMPTZ | 更新时间 |

**RLS 策略**: 用户只能访问自己项目的任务

### 5. llm_providers - LLM 服务商表

存储用户的 LLM/视频生成服务商配置。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| user_id | UUID | 外键，关联用户 |
| name | TEXT | 服务商名称（如"OpenAI"、"Gemini"） |
| provider_type | TEXT | 服务商类型（llm/video） |
| protocol | TEXT | 协议（openai/anthropic/gemini） |
| base_url | TEXT | API 基础 URL |
| api_key | TEXT | API 密钥（加密存储） |
| is_active | BOOLEAN | 是否启用 |
| available_models | JSONB | 可用模型列表 |
| created_at | TIMESTAMPTZ | 创建时间 |
| updated_at | TIMESTAMPTZ | 更新时间 |

**RLS 策略**: 用户只能访问自己的服务商配置

### 6. model_mappings - 任务-模型映射表

存储任务类型与模型的映射关系。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| user_id | UUID | 外键，关联用户 |
| project_id | UUID | 外键，关联项目（可为 NULL，表示全局默认） |
| task_type | TEXT | 任务类型 |
| provider_id | UUID | 外键，关联 llm_providers |
| model_name | TEXT | 模型名称 |
| parameters | JSONB | 模型参数（temperature、max_tokens 等） |
| created_at | TIMESTAMPTZ | 创建时间 |
| updated_at | TIMESTAMPTZ | 更新时间 |

**RLS 策略**: 用户只能访问自己的映射配置

### 7. circuit_breaker_states - 熔断器状态表

存储服务商熔断器状态。

| 字段 | 类型 | 说明 |
|------|------|------|
| provider_id | UUID | 主键，关联 llm_providers |
| state | TEXT | 熔断状态（closed/open/half_open） |
| failure_count | INT | 失败计数 |
| opened_at | TIMESTAMPTZ | 熔断开启时间 |
| updated_at | TIMESTAMPTZ | 更新时间 |

**RLS 策略**: 用户只能访问自己的熔断器状态

### 8. video_results - 视频结果表

存储视频生成结果。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| job_id | UUID | 外键，关联 job_queue |
| shot_number | TEXT | 镜头编号 |
| video_url | TEXT | 视频 URL |
| provider | TEXT | 视频生成服务商 |
| generation_id | TEXT | 生成任务 ID |
| created_at | TIMESTAMPTZ | 创建时间 |

**RLS 策略**: 用户只能访问自己项目的视频结果

## 索引

### 性能优化索引

```sql
-- story_nodes 索引
CREATE INDEX idx_nodes_project_id ON story_nodes(project_id);
CREATE INDEX idx_nodes_type ON story_nodes(type);
CREATE INDEX idx_nodes_parent_id ON story_nodes(parent_id);

-- job_queue 索引
CREATE INDEX idx_jobs_project_id ON job_queue(project_id);
CREATE INDEX idx_jobs_status ON job_queue(status);
CREATE INDEX idx_jobs_user_id ON job_queue(user_id);

-- llm_providers 索引
CREATE INDEX idx_providers_user_id ON llm_providers(user_id);
CREATE INDEX idx_providers_type ON llm_providers(provider_type);

-- model_mappings 索引
CREATE INDEX idx_mappings_user_id ON model_mappings(user_id);
CREATE INDEX idx_mappings_project_id ON model_mappings(project_id);
```

## RLS (Row Level Security) 策略

所有表都启用了 RLS，基本策略模式：

```sql
-- 启用 RLS
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;

-- 创建策略
CREATE POLICY "Users can only access their own projects"
ON projects
FOR ALL
USING (user_id = auth.uid());
```

## 关系图

```
users (Supabase Auth)
  │
  ├─> projects
  │     ├─> story_nodes
  │     │     └─> node_layouts
  │     ├─> job_queue
  │     │     └─> video_results
  │
  ├─> llm_providers
  │     ├─> circuit_breaker_states
  │     └─> model_mappings
```

## 数据流

### 项目创建流程

1. 用户在 Dashboard 输入创意
2. 调用 `POST /api/projects` 创建项目
3. 创建 Market Analyst Node 开始分析
4. 生成 story_nodes.config 节点

### 小说生成流程

1. LangGraph 进入 Module A (Novel Writer)
2. 创建 story_nodes.novel_chapter 节点
3. 更新 job_queue 记录进度
4. WebSocket 推送进度事件

### 视频生成流程

1. 用户请求生成视频
2. 创建 job_queue.video_generation 任务
3. Celery Worker 处理任务
4. 轮询视频生成状态
5. 存储结果到 video_results
6. WebSocket 推送完成事件

## 备份与恢复

使用 Supabase 内置的备份功能：

```bash
# 导出数据
supabase db dump -f backup.sql

# 导入数据
supabase db restore backup.sql
```

## 监控

关键监控指标：

- 表大小：`pg_total_relation_size`
- 查询性能：`pg_stat_statements`
- 连接数：`pg_stat_activity`
- RLS 性能影响
