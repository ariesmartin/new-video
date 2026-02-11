-- =====================================================
-- AI Video Engine - Project Content Table
-- =====================================================
-- Version: 1.0.0
-- Created: 2026-02-11
-- Description: 创建 project_content 表用于存储大纲、方案等内容数据
-- =====================================================

-- 项目内容表（大纲、方案等）
CREATE TABLE IF NOT EXISTS project_content (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    content_type VARCHAR(50) NOT NULL,  -- 'outline', 'plan', 'story_plan', etc.
    title VARCHAR(255),
    content TEXT NOT NULL,  -- JSON 字符串存储具体内容
    metadata JSONB DEFAULT '{}'::jsonb,  -- 额外的元数据
    status VARCHAR(50) DEFAULT 'draft',  -- 'draft', 'confirmed', 'archived'
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(project_id, content_type)
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_project_content_project_id ON project_content(project_id);
CREATE INDEX IF NOT EXISTS idx_project_content_type ON project_content(content_type);
CREATE INDEX IF NOT EXISTS idx_project_content_status ON project_content(status);

-- 更新时间戳触发器
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_project_content_updated_at
    BEFORE UPDATE ON project_content
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- 启用 RLS (Row Level Security)
ALTER TABLE project_content ENABLE ROW LEVEL SECURITY;

-- 创建 RLS 策略
CREATE POLICY "Enable read access for project members" ON project_content
    FOR SELECT
    USING (EXISTS (
        SELECT 1 FROM projects 
        WHERE projects.id = project_content.project_id 
        AND projects.user_id = auth.uid()
    ));

CREATE POLICY "Enable insert access for project owners" ON project_content
    FOR INSERT
    WITH CHECK (EXISTS (
        SELECT 1 FROM projects 
        WHERE projects.id = project_content.project_id 
        AND projects.user_id = auth.uid()
    ));

CREATE POLICY "Enable update access for project owners" ON project_content
    FOR UPDATE
    USING (EXISTS (
        SELECT 1 FROM projects 
        WHERE projects.id = project_content.project_id 
        AND projects.user_id = auth.uid()
    ));

CREATE POLICY "Enable delete access for project owners" ON project_content
    FOR DELETE
    USING (EXISTS (
        SELECT 1 FROM projects 
        WHERE projects.id = project_content.project_id 
        AND projects.user_id = auth.uid()
    ));
