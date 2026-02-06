-- =====================================================
-- AI Video Engine - Initial Database Schema
-- =====================================================
-- Version: 1.0.0
-- Created: 2026-02-02
-- Description: 完整的数据库结构，严格遵循系统架构文档
-- =====================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";  -- pgvector for RAG

-- =====================================================
-- Section A: 项目与资产 (Project & Assets)
-- Reference: 系统架构文档 Section 3.2A
-- =====================================================

-- 项目表
CREATE TABLE IF NOT EXISTS projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    name VARCHAR(100) NOT NULL,
    cover_image TEXT,
    meta JSONB DEFAULT '{}'::jsonb,  -- { genre, tone, target_word_count, ... }
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_projects_user_id ON projects(user_id);
CREATE INDEX IF NOT EXISTS idx_projects_updated_at ON projects(updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_projects_meta_genre ON projects USING GIN ((meta -> 'genre'));

-- 资产表 (角色/场景/道具的视觉参考)
CREATE TABLE IF NOT EXISTS assets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    name VARCHAR(50) NOT NULL,
    type VARCHAR(20) NOT NULL CHECK (type IN ('character', 'location', 'prop')),
    visual_tokens JSONB DEFAULT '{}'::jsonb,  -- { hair: "black", style: "anime", ... }
    avatar_url TEXT,
    reference_urls TEXT[] DEFAULT '{}',
    prompts JSONB DEFAULT '{}'::jsonb,  -- { front_view: "...", side_view: "..." }
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_assets_project_id ON assets(project_id);
CREATE INDEX IF NOT EXISTS idx_assets_type ON assets(type);

-- =====================================================
-- Section B: 业务内容数据 (Content - Generic Node System)
-- Reference: 系统架构文档 Section 3.2B
-- =====================================================

-- 通用内容节点表
CREATE TABLE IF NOT EXISTS story_nodes (
    node_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    parent_id UUID REFERENCES story_nodes(node_id) ON DELETE SET NULL,
    type VARCHAR(50) NOT NULL,  -- episode, scene, shot, character, outline, ...
    content JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_story_nodes_project_id ON story_nodes(project_id);
CREATE INDEX IF NOT EXISTS idx_story_nodes_type ON story_nodes(type);
CREATE INDEX IF NOT EXISTS idx_story_nodes_parent_id ON story_nodes(parent_id);
CREATE INDEX IF NOT EXISTS idx_story_nodes_content ON story_nodes USING GIN (content);

-- =====================================================
-- Section C: 画布布局数据 (Layout)
-- Reference: 系统架构文档 Section 3.2C
-- =====================================================

-- 节点布局表 (支持多画布 Tab)
CREATE TABLE IF NOT EXISTS node_layouts (
    node_id UUID NOT NULL REFERENCES story_nodes(node_id) ON DELETE CASCADE,
    canvas_tab VARCHAR(50) NOT NULL,  -- 'novel', 'drama', 'storyboard'
    position_x FLOAT NOT NULL DEFAULT 0,
    position_y FLOAT NOT NULL DEFAULT 0,
    PRIMARY KEY (node_id, canvas_tab)
);

CREATE INDEX IF NOT EXISTS idx_node_layouts_canvas_tab ON node_layouts(canvas_tab);

-- =====================================================
-- Section D: 全局模型配置 (Model Governance)
-- Reference: 系统架构文档 Section 3.2D
-- =====================================================

-- LLM 服务商注册表
CREATE TABLE IF NOT EXISTS llm_providers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    name VARCHAR(50) NOT NULL,
    protocol VARCHAR(20) DEFAULT 'openai' CHECK (protocol IN ('openai', 'anthropic', 'gemini', 'azure')),
    base_url VARCHAR(255),
    api_key TEXT NOT NULL,  -- Encrypted
    is_active BOOLEAN DEFAULT TRUE,
    last_verified_at TIMESTAMPTZ,
    available_models JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_llm_providers_user_id ON llm_providers(user_id);
CREATE INDEX IF NOT EXISTS idx_llm_providers_is_active ON llm_providers(is_active);

-- 任务模型映射表
CREATE TABLE IF NOT EXISTS model_mappings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,  -- NULL = 全局默认
    user_id UUID NOT NULL,
    task_type VARCHAR(50) NOT NULL,
    provider_id UUID NOT NULL REFERENCES llm_providers(id) ON DELETE CASCADE,
    model_name VARCHAR(100) NOT NULL,
    parameters JSONB DEFAULT '{"temperature": 0.7, "max_tokens": 4096}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_model_mappings_user_id ON model_mappings(user_id);
CREATE INDEX IF NOT EXISTS idx_model_mappings_project_id ON model_mappings(project_id);
CREATE INDEX IF NOT EXISTS idx_model_mappings_task_type ON model_mappings(task_type);

-- =====================================================
-- Section E: 数据增强层 (Data Enhancement)
-- Reference: 系统架构文档 Section 3.5
-- =====================================================

-- 节点历史版本 (Time Travel)
CREATE TABLE IF NOT EXISTS node_versions (
    version_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    node_id UUID NOT NULL REFERENCES story_nodes(node_id) ON DELETE CASCADE,
    content JSONB NOT NULL,
    user_id UUID,
    reason VARCHAR(50),  -- 'AI_Regenerate', 'User_Edit', 'Rollback'
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_node_versions_node_id ON node_versions(node_id);
CREATE INDEX IF NOT EXISTS idx_node_versions_created_at ON node_versions(created_at DESC);

-- 语义记忆向量表 (RAG)
CREATE TABLE IF NOT EXISTS project_vectors (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    node_id UUID REFERENCES story_nodes(node_id) ON DELETE SET NULL,
    embedding VECTOR(1536),  -- OpenAI text-embedding-3-small 维度
    text_chunk TEXT NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,  -- { type: "character_bio", name: "Chen Mo" }
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_project_vectors_project_id ON project_vectors(project_id);
CREATE INDEX IF NOT EXISTS idx_project_vectors_embedding ON project_vectors USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- =====================================================
-- Section F: 异步任务队列 (Job Queue)
-- Reference: 系统架构文档 Section 3.4
-- =====================================================

CREATE TABLE IF NOT EXISTS job_queue (
    job_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL,  -- 'video_generation', 'novel_writing', ...
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'RUNNING', 'COMPLETED', 'FAILED', 'CANCELLED', 'DEAD_LETTER')),
    priority INT DEFAULT 0 CHECK (priority >= 0 AND priority <= 10),
    
    -- 进度反馈
    progress_percent INT DEFAULT 0 CHECK (progress_percent >= 0 AND progress_percent <= 100),
    current_step VARCHAR(255),
    
    -- 任务参数与结果
    input_payload JSONB DEFAULT '{}'::jsonb,
    output_result JSONB,
    error_message TEXT,
    
    -- 生命周期
    created_at TIMESTAMPTZ DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    ended_at TIMESTAMPTZ,
    
    -- 看门狗用
    last_heartbeat TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_job_queue_project_id ON job_queue(project_id);
CREATE INDEX IF NOT EXISTS idx_job_queue_status ON job_queue(status);
CREATE INDEX IF NOT EXISTS idx_job_queue_priority ON job_queue(priority DESC);
CREATE INDEX IF NOT EXISTS idx_job_queue_created_at ON job_queue(created_at DESC);

-- =====================================================
-- Section G: 团队与扩展层 (Team & Extension)
-- Reference: 系统架构文档 Section 3.7
-- =====================================================

-- 团队表
CREATE TABLE IF NOT EXISTS teams (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    plan_tier VARCHAR(20) DEFAULT 'free' CHECK (plan_tier IN ('free', 'pro', 'enterprise')),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 项目成员表 (RBAC)
CREATE TABLE IF NOT EXISTS project_members (
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    user_id UUID NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('owner', 'editor', 'viewer')),
    joined_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (project_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_project_members_user_id ON project_members(user_id);

-- 插件注册表
CREATE TABLE IF NOT EXISTS plugins (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    type VARCHAR(20) NOT NULL CHECK (type IN ('exporter', 'generator', 'analyzer')),
    entry_point VARCHAR(255) NOT NULL,
    config_schema JSONB,
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- =====================================================
-- Section H: 熔断器状态 (Circuit Breaker)
-- Reference: 系统架构文档 Section 5.8B
-- =====================================================

CREATE TABLE IF NOT EXISTS circuit_breaker_states (
    provider_id UUID PRIMARY KEY REFERENCES llm_providers(id) ON DELETE CASCADE,
    state VARCHAR(20) NOT NULL DEFAULT 'CLOSED' CHECK (state IN ('CLOSED', 'OPEN', 'HALF_OPEN')),
    failure_count INT DEFAULT 0,
    last_failure_at TIMESTAMPTZ,
    opened_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- =====================================================
-- Section I: 语义缓存 (Semantic Cache)
-- Reference: 系统架构文档 Section 2.9B
-- =====================================================

CREATE TABLE IF NOT EXISTS semantic_cache (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    prompt_hash VARCHAR(64) NOT NULL,  -- SHA256 of prompt
    prompt_embedding VECTOR(1536),
    response TEXT NOT NULL,
    model_name VARCHAR(100) NOT NULL,
    hit_count INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_hit_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_semantic_cache_prompt_hash ON semantic_cache(prompt_hash);
CREATE INDEX IF NOT EXISTS idx_semantic_cache_embedding ON semantic_cache USING ivfflat (prompt_embedding vector_cosine_ops) WITH (lists = 50);

-- =====================================================
-- Triggers: 自动更新时间戳
-- =====================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_projects_updated_at
    BEFORE UPDATE ON projects
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- Initial Data: 默认配置
-- =====================================================

-- (可选) 插入默认的任务-模型映射模板
-- INSERT INTO model_mappings (...) VALUES (...);

-- =====================================================
-- Row Level Security (RLS) - 基础策略
-- =====================================================

-- Enable RLS on tables
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE assets ENABLE ROW LEVEL SECURITY;
ALTER TABLE story_nodes ENABLE ROW LEVEL SECURITY;
ALTER TABLE node_layouts ENABLE ROW LEVEL SECURITY;
ALTER TABLE llm_providers ENABLE ROW LEVEL SECURITY;
ALTER TABLE model_mappings ENABLE ROW LEVEL SECURITY;
ALTER TABLE job_queue ENABLE ROW LEVEL SECURITY;

-- Projects: 用户只能访问自己的项目
CREATE POLICY "Users can view own projects"
    ON projects FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own projects"
    ON projects FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own projects"
    ON projects FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own projects"
    ON projects FOR DELETE
    USING (auth.uid() = user_id);

-- Assets: 通过项目关联
CREATE POLICY "Users can access own project assets"
    ON assets FOR ALL
    USING (project_id IN (SELECT id FROM projects WHERE user_id = auth.uid()));

-- Story Nodes: 通过项目关联
CREATE POLICY "Users can access own project nodes"
    ON story_nodes FOR ALL
    USING (project_id IN (SELECT id FROM projects WHERE user_id = auth.uid()));

-- LLM Providers: 用户只能访问自己的配置
CREATE POLICY "Users can access own providers"
    ON llm_providers FOR ALL
    USING (auth.uid() = user_id);

-- Model Mappings: 用户只能访问自己的配置
CREATE POLICY "Users can access own mappings"
    ON model_mappings FOR ALL
    USING (auth.uid() = user_id);

-- Job Queue: 通过项目关联
CREATE POLICY "Users can access own project jobs"
    ON job_queue FOR ALL
    USING (project_id IN (SELECT id FROM projects WHERE user_id = auth.uid()));

-- =====================================================
-- Comments: 表注释
-- =====================================================

COMMENT ON TABLE projects IS '项目表 - 存储用户的短剧/漫剧项目';
COMMENT ON TABLE assets IS '资产表 - 角色、场景、道具的视觉参考';
COMMENT ON TABLE story_nodes IS '通用内容节点 - 支持无限画布的 Generic Node System';
COMMENT ON TABLE node_layouts IS '节点布局 - 存储画布上的坐标位置';
COMMENT ON TABLE llm_providers IS 'LLM 服务商 - BYOK 模式存储用户的 API Key';
COMMENT ON TABLE model_mappings IS '任务模型映射 - Task-Model Routing';
COMMENT ON TABLE node_versions IS '节点历史版本 - 支持时间旅行和回滚';
COMMENT ON TABLE project_vectors IS '语义向量 - RAG 长文本记忆';
COMMENT ON TABLE job_queue IS '异步任务队列 - 长时任务管理';
COMMENT ON TABLE circuit_breaker_states IS '熔断器状态 - API 保护';
COMMENT ON TABLE semantic_cache IS '语义缓存 - 降低 API 成本';
