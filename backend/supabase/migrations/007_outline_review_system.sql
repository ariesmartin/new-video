-- =====================================================
-- Migration: 007_outline_review_system.sql
-- Description: 大纲审阅系统 - 创建 reviews 和 story_plans 表
-- Author: AI Video Engine Team
-- Date: 2026-02-09
-- =====================================================

-- =====================================================
-- 表: story_plans (故事策划方案)
-- 说明: 存储故事策划阶段生成的方案
-- =====================================================

CREATE TABLE IF NOT EXISTS story_plans (
    plan_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    
    -- 方案基本信息
    title VARCHAR(200) NOT NULL,              -- 方案标题
    description TEXT,                         -- 方案描述
    
    -- 题材配置
    genre VARCHAR(100),                       -- 主要题材
    sub_tags JSONB DEFAULT '[]'::jsonb,       -- 子题材标签
    tone JSONB DEFAULT '[]'::jsonb,           -- 调性标签
    
    -- 结构配置
    total_episodes INT DEFAULT 80,            -- 总集数
    target_word_count INT DEFAULT 1500,       -- 每集目标字数
    ending_type VARCHAR(20) DEFAULT 'HE',     -- 结局类型: HE/BE/OE
    
    -- 视觉配置
    aspect_ratio VARCHAR(10) DEFAULT '9:16',  -- 画面比例
    drawing_type VARCHAR(50),                 -- 绘制类型
    visual_style VARCHAR(100),                -- 视觉风格
    
    -- 方案内容
    plan_data JSONB DEFAULT '{}'::jsonb,      -- 完整方案数据
    
    -- 状态
    status VARCHAR(50) DEFAULT 'draft',       -- draft/active/archived
    is_selected BOOLEAN DEFAULT FALSE,        -- 是否被选中
    
    -- 时间戳
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_story_plans_project_id ON story_plans(project_id);
CREATE INDEX IF NOT EXISTS idx_story_plans_user_id ON story_plans(user_id);
CREATE INDEX IF NOT EXISTS idx_story_plans_status ON story_plans(status);
CREATE INDEX IF NOT EXISTS idx_story_plans_selected ON story_plans(project_id, is_selected);

-- 注释
COMMENT ON TABLE story_plans IS '故事策划方案表 - 存储 Story Planner 生成的方案';
COMMENT ON COLUMN story_plans.plan_data IS '方案完整数据 JSON: {logline, synopsis, episodes, ...}';


-- =====================================================
-- 表: content_reviews (内容审阅结果)
-- 说明: 存储大纲、小说、剧本的审阅结果
-- =====================================================

CREATE TABLE IF NOT EXISTS content_reviews (
    review_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    
    -- 审阅类型
    review_type VARCHAR(50) NOT NULL,         -- 'global' | 'chapter' | 'scene' | 'shot'
    content_type VARCHAR(50) NOT NULL,        -- 'outline' | 'novel' | 'script' | 'storyboard'
    
    -- 关联内容
    episode_id UUID REFERENCES episodes(episode_id) ON DELETE CASCADE,  -- 如适用
    scene_id UUID REFERENCES scenes(scene_id) ON DELETE CASCADE,        -- 如适用
    shot_id UUID REFERENCES shot_nodes(shot_id) ON DELETE CASCADE,      -- 如适用
    
    -- 审阅结果
    overall_score INT NOT NULL CHECK (overall_score >= 0 AND overall_score <= 100),
    categories JSONB DEFAULT '{}'::jsonb,     -- 6大分类评分 {logic, pacing, character, ...}
    tension_curve JSONB DEFAULT '[]'::jsonb,  -- 张力曲线数据 [80, 85, 90, ...]
    chapter_reviews JSONB DEFAULT '{}'::jsonb,-- 章节审阅映射 {chapterId: {score, status, issues}}
    
    -- 问题列表
    issues JSONB DEFAULT '[]'::jsonb,         -- 问题列表 [{id, category, severity, description}]
    
    -- 总结
    summary TEXT,                             -- 审阅总结
    recommendations JSONB DEFAULT '[]'::jsonb,-- 建议列表
    
    -- 审阅元数据
    reviewer_model VARCHAR(100),              -- 审阅使用的模型
    review_params JSONB DEFAULT '{}'::jsonb,  -- 审阅参数
    
    -- 状态
    status VARCHAR(50) DEFAULT 'completed',   -- pending/completed/failed
    
    -- 版本
    version INT DEFAULT 1,                    -- 审阅版本
    
    -- 时间戳
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_content_reviews_project_id ON content_reviews(project_id);
CREATE INDEX IF NOT EXISTS idx_content_reviews_type ON content_reviews(review_type, content_type);
CREATE INDEX IF NOT EXISTS idx_content_reviews_episode ON content_reviews(episode_id);
CREATE INDEX IF NOT EXISTS idx_content_reviews_created ON content_reviews(project_id, created_at DESC);

-- GIN 索引用于 JSONB 查询
CREATE INDEX IF NOT EXISTS idx_content_reviews_categories ON content_reviews USING GIN (categories);
CREATE INDEX IF NOT EXISTS idx_content_reviews_chapter_reviews ON content_reviews USING GIN (chapter_reviews);

-- 注释
COMMENT ON TABLE content_reviews IS '内容审阅结果表 - 存储 Editor Agent 的审阅结果';
COMMENT ON COLUMN content_reviews.categories IS '6大分类评分: {logic: {score, weight}, pacing: {...}}';
COMMENT ON COLUMN content_reviews.chapter_reviews IS '章节审阅映射: {ep_xxx_1: {score, status, issues}}';
COMMENT ON COLUMN content_reviews.tension_curve IS '张力曲线数据，动态长度';


-- =====================================================
-- 更新 user_preferences 表添加配置字段
-- =====================================================

-- 检查并添加 user_config 字段
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'user_preferences' 
                   AND column_name = 'user_config') THEN
        ALTER TABLE user_preferences ADD COLUMN user_config JSONB DEFAULT '{}'::jsonb;
    END IF;
END $$;

COMMENT ON COLUMN user_preferences.user_config IS '用户配置 JSON: {sub_tags, ending, total_episodes, ...}';


-- =====================================================
-- 触发器: 自动更新 updated_at
-- =====================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- story_plans 触发器
DROP TRIGGER IF EXISTS update_story_plans_updated_at ON story_plans;
CREATE TRIGGER update_story_plans_updated_at
    BEFORE UPDATE ON story_plans
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- content_reviews 触发器
DROP TRIGGER IF EXISTS update_content_reviews_updated_at ON content_reviews;
CREATE TRIGGER update_content_reviews_updated_at
    BEFORE UPDATE ON content_reviews
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();


-- =====================================================
-- RLS (Row Level Security) Policies
-- =====================================================

-- 启用 RLS
ALTER TABLE story_plans ENABLE ROW LEVEL SECURITY;
ALTER TABLE content_reviews ENABLE ROW LEVEL SECURITY;

-- story_plans: 仅项目成员可访问
CREATE POLICY "Project members can view story_plans" 
ON story_plans FOR SELECT USING (
    EXISTS (
        SELECT 1 FROM projects 
        WHERE projects.id = story_plans.project_id
        AND (projects.user_id = auth.uid() 
             OR EXISTS (
                 SELECT 1 FROM project_members 
                 WHERE project_members.project_id = projects.id 
                 AND project_members.user_id = auth.uid()
             ))
    )
);

CREATE POLICY "Project members can insert story_plans" 
ON story_plans FOR INSERT WITH CHECK (
    EXISTS (
        SELECT 1 FROM projects 
        WHERE projects.id = story_plans.project_id
        AND (projects.user_id = auth.uid() 
             OR EXISTS (
                 SELECT 1 FROM project_members 
                 WHERE project_members.project_id = projects.id 
                 AND project_members.user_id = auth.uid()
             ))
    )
);

CREATE POLICY "Project members can update story_plans" 
ON story_plans FOR UPDATE USING (
    EXISTS (
        SELECT 1 FROM projects 
        WHERE projects.id = story_plans.project_id
        AND (projects.user_id = auth.uid() 
             OR EXISTS (
                 SELECT 1 FROM project_members 
                 WHERE project_members.project_id = projects.id 
                 AND project_members.user_id = auth.uid()
             ))
    )
);

-- content_reviews: 仅项目成员可访问
CREATE POLICY "Project members can view content_reviews" 
ON content_reviews FOR SELECT USING (
    EXISTS (
        SELECT 1 FROM projects 
        WHERE projects.id = content_reviews.project_id
        AND (projects.user_id = auth.uid() 
             OR EXISTS (
                 SELECT 1 FROM project_members 
                 WHERE project_members.project_id = projects.id 
                 AND project_members.user_id = auth.uid()
             ))
    )
);

CREATE POLICY "Project members can insert content_reviews" 
ON content_reviews FOR INSERT WITH CHECK (
    EXISTS (
        SELECT 1 FROM projects 
        WHERE projects.id = content_reviews.project_id
        AND (projects.user_id = auth.uid() 
             OR EXISTS (
                 SELECT 1 FROM project_members 
                 WHERE project_members.project_id = projects.id 
                 AND project_members.user_id = auth.uid()
             ))
    )
);


-- =====================================================
-- 完成
-- =====================================================
