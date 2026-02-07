-- Theme Library Database Schema
-- For Supabase PostgreSQL
-- Created: 2026-02-07
-- Version: 1.0.0

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm"; -- For text search

-- ============================================
-- TABLE: themes (主题库)
-- ============================================
CREATE TABLE themes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- 主题核心信息
    name VARCHAR(255) NOT NULL,                          -- 主题名称
    name_en VARCHAR(255),                                -- 英文名称（国际化）
    slug VARCHAR(100) UNIQUE NOT NULL,                   -- URL友好的标识
    
    -- 分类与标签
    category VARCHAR(100) NOT NULL,                      -- 主要分类: romance, thriller, comedy, etc.
    subcategories TEXT[],                                -- 子分类数组
    tags TEXT[],                                         -- 标签数组
    
    -- 受众定位
    target_audience JSONB DEFAULT '{}',                  -- 目标受众
    -- {
    --   "age_range": "18-35",
    --   "gender": "female",
    --   "interests": ["romance", "career"],
    --   "viewing_habits": "short-form"
    -- }
    
    -- 主题元数据
    description TEXT,                                    -- 主题描述
    summary TEXT,                                        -- 一句话总结
    key_themes TEXT[],                                   -- 核心主题关键词
    emotional_beats TEXT[],                              -- 情感节拍
    
    -- 风格与基调
    tone JSONB DEFAULT '{}',                             -- 基调配置
    -- {
    --   "overall": "light-hearted",
    --   "emotional_arc": "hopeful",
    --   "pacing": "fast"
    -- }
    
    -- 热门度与使用统计
    popularity_score DECIMAL(5,2) DEFAULT 0,            -- 热门度评分 (0-100)
    usage_count INTEGER DEFAULT 0,                       -- 使用次数
    success_rate DECIMAL(5,2) DEFAULT 0,                -- 成功率 (%)
    
    -- 内容示例
    example_loglines TEXT[],                             -- 示例一句话梗概
    example_titles TEXT[],                               -- 示例标题
    
    -- 状态与元数据
    status VARCHAR(50) DEFAULT 'active',                 -- active, draft, archived
    is_featured BOOLEAN DEFAULT false,                   -- 是否推荐
    is_premium BOOLEAN DEFAULT false,                    -- 是否付费主题
    
    -- 时间戳
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- 搜索优化
    search_vector TSVECTOR
);

-- 创建索引
CREATE INDEX idx_themes_category ON themes(category);
CREATE INDEX idx_themes_status ON themes(status);
CREATE INDEX idx_themes_popularity ON themes(popularity_score DESC);
CREATE INDEX idx_themes_featured ON themes(is_featured) WHERE is_featured = true;
CREATE INDEX idx_themes_tags ON themes USING GIN(tags);
CREATE INDEX idx_themes_subcategories ON themes USING GIN(subcategories);
CREATE INDEX idx_themes_search ON themes USING GIN(search_vector);

-- 创建搜索向量更新触发器
CREATE OR REPLACE FUNCTION update_theme_search_vector()
RETURNS TRIGGER AS $$
BEGIN
    NEW.search_vector := 
        setweight(to_tsvector('simple', COALESCE(NEW.name, '')), 'A') ||
        setweight(to_tsvector('simple', COALESCE(NEW.description, '')), 'B') ||
        setweight(to_tsvector('simple', COALESCE(array_to_string(NEW.tags, ' '), '')), 'C') ||
        setweight(to_tsvector('simple', COALESCE(array_to_string(NEW.key_themes, ' '), '')), 'D');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_theme_search
    BEFORE INSERT OR UPDATE ON themes
    FOR EACH ROW
    EXECUTE FUNCTION update_theme_search_vector();

-- ============================================
-- TABLE: theme_elements (主题元素)
-- ============================================
CREATE TABLE theme_elements (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    theme_id UUID NOT NULL REFERENCES themes(id) ON DELETE CASCADE,
    
    element_type VARCHAR(100) NOT NULL,                  -- 元素类型
    -- 'character', 'setting', 'conflict', 'trope', 'mood', 'twist'
    
    name VARCHAR(255) NOT NULL,                          -- 元素名称
    description TEXT,                                    -- 元素描述
    
    -- 配置数据（JSONB灵活存储）
    config JSONB DEFAULT '{}',                           -- 元素配置
    -- 例如 character 类型:
    -- {
    --   "role": "protagonist",
    --   "traits": ["ambitious", "kind"],
    --   "archetype": "underdog",
    --   "relationship_dynamics": ["enemies_to_lovers"]
    -- }
    
    -- 使用权重
    weight DECIMAL(3,2) DEFAULT 1.0,                    -- 权重 (0-1)
    frequency INTEGER DEFAULT 0,                         -- 使用频率
    
    -- 状态
    is_required BOOLEAN DEFAULT false,                   -- 是否必需
    is_active BOOLEAN DEFAULT true,                      -- 是否激活
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_theme_elements_theme_id ON theme_elements(theme_id);
CREATE INDEX idx_theme_elements_type ON theme_elements(element_type);
CREATE INDEX idx_theme_elements_active ON theme_elements(is_active) WHERE is_active = true;

-- ============================================
-- TABLE: theme_trends (主题趋势)
-- ============================================
CREATE TABLE theme_trends (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    theme_id UUID NOT NULL REFERENCES themes(id) ON DELETE CASCADE,
    
    date DATE NOT NULL,                                  -- 统计日期
    
    -- 指标
    view_count INTEGER DEFAULT 0,                        -- 观看次数
    engagement_score DECIMAL(5,2) DEFAULT 0,            -- 互动分数
    completion_rate DECIMAL(5,2) DEFAULT 0,             -- 完播率 (%)
    share_count INTEGER DEFAULT 0,                       -- 分享次数
    
    -- 排名
    daily_rank INTEGER,                                  -- 当日排名
    category_rank INTEGER,                               -- 分类排名
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_theme_trends_theme_id ON theme_trends(theme_id);
CREATE INDEX idx_theme_trends_date ON theme_trends(date);
CREATE INDEX idx_theme_trends_rank ON theme_trends(daily_rank);

-- 唯一约束：每天每个主题只有一条记录
CREATE UNIQUE INDEX idx_theme_trends_unique ON theme_trends(theme_id, date);

-- ============================================
-- TABLE: user_preferences (用户偏好)
-- ============================================
CREATE TABLE user_preferences (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,                               -- 关联用户ID
    
    -- 偏好设置
    preferred_categories TEXT[],                         -- 喜欢的分类
    preferred_themes UUID[],                             -- 喜欢的主题ID数组
    disliked_themes UUID[],                              -- 不喜欢的主题ID数组
    
    -- 观看历史统计
    viewing_history JSONB DEFAULT '{}',                  -- 观看历史统计
    -- {
    --   "total_watch_time": 3600,
    --   "favorite_genres": ["romance", "comedy"],
    --   "average_completion_rate": 0.75
    -- }
    
    -- AI生成偏好
    generation_preferences JSONB DEFAULT '{}',           -- 生成偏好
    -- {
    --   "default_tone": "light-hearted",
    --   "preferred_episode_length": 60,
    --   "auto_optimize": true
    -- }
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_user_preferences_user_id ON user_preferences(user_id);
CREATE INDEX idx_user_preferences_categories ON user_preferences USING GIN(preferred_categories);

-- ============================================
-- TABLE: projects (项目)
-- ============================================
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,                               -- 创建者
    
    -- 项目信息
    title VARCHAR(500),                                  -- 项目标题
    description TEXT,                                    -- 项目描述
    status VARCHAR(50) DEFAULT 'planning',               -- planning, writing, editing, completed, archived
    
    -- 关联的主题
    theme_id UUID REFERENCES themes(id),                 -- 使用的主题
    theme_config JSONB DEFAULT '{}',                     -- 主题配置覆盖
    
    -- 项目设置
    settings JSONB DEFAULT '{}',                         -- 项目设置
    -- {
    --   "target_episodes": 60,
    --   "target_duration": 60,
    --   "language": "zh-CN",
    --   "style_guide": "modern_dramatic"
    -- }
    
    -- 统计数据
    episode_count INTEGER DEFAULT 0,                     -- 剧集数量
    total_word_count INTEGER DEFAULT 0,                  -- 总字数
    completion_percentage DECIMAL(5,2) DEFAULT 0,       -- 完成百分比
    
    -- 时间戳
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

CREATE INDEX idx_projects_user_id ON projects(user_id);
CREATE INDEX idx_projects_status ON projects(status);
CREATE INDEX idx_projects_theme_id ON projects(theme_id);

-- ============================================
-- TABLE: project_content (项目内容 - 各阶段产出)
-- ============================================
CREATE TABLE project_content (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    
    content_type VARCHAR(100) NOT NULL,                  -- 内容类型
    -- 'logline', 'beat_sheet', 'synopsis', 'outline', 
    -- 'episode_skeleton', 'episode_script', 'scene_description'
    
    episode_number INTEGER,                              -- 剧集编号（如适用）
    scene_number INTEGER,                                -- 场景编号（如适用）
    
    -- 内容
    title VARCHAR(500),                                  -- 标题
    content TEXT NOT NULL,                               -- 内容
    metadata JSONB DEFAULT '{}',                         -- 元数据
    
    -- 版本控制
    version INTEGER DEFAULT 1,                           -- 版本号
    parent_version UUID,                                 -- 父版本ID（用于分支）
    
    -- AI生成信息
    ai_model VARCHAR(100),                               -- 使用的AI模型
    generation_params JSONB DEFAULT '{}',                -- 生成参数
    
    -- 状态
    status VARCHAR(50) DEFAULT 'draft',                  -- draft, review, approved, rejected
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_project_content_project_id ON project_content(project_id);
CREATE INDEX idx_project_content_type ON project_content(content_type);
CREATE INDEX idx_project_content_episode ON project_content(project_id, episode_number);
CREATE INDEX idx_project_content_status ON project_content(status);

-- ============================================
-- RLS (Row Level Security) Policies
-- ============================================

-- 启用RLS
ALTER TABLE themes ENABLE ROW LEVEL SECURITY;
ALTER TABLE theme_elements ENABLE ROW LEVEL SECURITY;
ALTER TABLE theme_trends ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_preferences ENABLE ROW LEVEL SECURITY;
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE project_content ENABLE ROW LEVEL SECURITY;

-- Themes: 所有人可读，管理员可写
CREATE POLICY "Themes are viewable by everyone" 
ON themes FOR SELECT USING (status = 'active');

CREATE POLICY "Themes are insertable by admins" 
ON themes FOR INSERT WITH CHECK (
    auth.role() = 'admin' OR auth.role() = 'service_role'
);

CREATE POLICY "Themes are updatable by admins" 
ON themes FOR UPDATE USING (
    auth.role() = 'admin' OR auth.role() = 'service_role'
);

-- Theme Elements: 继承Themes的权限
CREATE POLICY "Theme elements are viewable by everyone" 
ON theme_elements FOR SELECT USING (
    EXISTS (
        SELECT 1 FROM themes 
        WHERE themes.id = theme_elements.theme_id 
        AND themes.status = 'active'
    )
);

-- User Preferences: 仅自己可访问
CREATE POLICY "Users can view own preferences" 
ON user_preferences FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own preferences" 
ON user_preferences FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own preferences" 
ON user_preferences FOR UPDATE USING (auth.uid() = user_id);

-- Projects: 仅自己可访问
CREATE POLICY "Users can view own projects" 
ON projects FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own projects" 
ON projects FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own projects" 
ON projects FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own projects" 
ON projects FOR DELETE USING (auth.uid() = user_id);

-- Project Content: 继承Projects的权限
CREATE POLICY "Users can view own project content" 
ON project_content FOR SELECT USING (
    EXISTS (
        SELECT 1 FROM projects 
        WHERE projects.id = project_content.project_id 
        AND projects.user_id = auth.uid()
    )
);

CREATE POLICY "Users can insert own project content" 
ON project_content FOR INSERT WITH CHECK (
    EXISTS (
        SELECT 1 FROM projects 
        WHERE projects.id = project_content.project_id 
        AND projects.user_id = auth.uid()
    )
);

CREATE POLICY "Users can update own project content" 
ON project_content FOR UPDATE USING (
    EXISTS (
        SELECT 1 FROM projects 
        WHERE projects.id = project_content.project_id 
        AND projects.user_id = auth.uid()
    )
);

-- ============================================
-- Functions & Triggers
-- ============================================

-- 自动更新 updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_themes_updated_at 
    BEFORE UPDATE ON themes 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_theme_elements_updated_at 
    BEFORE UPDATE ON theme_elements 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_preferences_updated_at 
    BEFORE UPDATE ON user_preferences 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_projects_updated_at 
    BEFORE UPDATE ON projects 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_project_content_updated_at 
    BEFORE UPDATE ON project_content 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- Seed Data: Sample Themes
-- ============================================

INSERT INTO themes (
    name, name_en, slug, category, subcategories, tags, 
    target_audience, description, summary, key_themes, emotional_beats,
    tone, popularity_score, is_featured
) VALUES 
(
    '霸道总裁爱上我', 
    'CEO Falls for Me',
    'ceo-romance',
    'romance',
    ARRAY['workplace', 'power_dynamic', 'modern'],
    ARRAY['霸道总裁', '甜宠', '职场', '灰姑娘', '高甜'],
    '{"age_range": "18-35", "gender": "female", "interests": ["romance", "fantasy"]}'::JSONB,
    '平凡女孩与霸道总裁之间的甜蜜爱情故事，充满误会、反转与最终的幸福结局',
    '当灰姑娘遇到霸道总裁，一场甜蜜又曲折的爱情冒险',
    ARRAY['爱情', '成长', '阶级跨越', '误会与和解'],
    ARRAY['初遇', '误会', '心动', '阻碍', '表白', '幸福结局'],
    '{"overall": "sweet", "emotional_arc": "hopeful", "pacing": "fast"}'::JSONB,
    95.5,
    true
),
(
    '重生复仇',
    'Reborn for Revenge',
    'reborn-revenge',
    'thriller',
    ARRAY['reincarnation', 'revenge', 'suspense'],
    ARRAY['重生', '复仇', '爽文', '打脸', '逆袭'],
    '{"age_range": "20-40", "gender": "female", "interests": ["revenge", "justice"]}'::JSONB,
    '女主重生回到过去，利用前世记忆改变命运，向曾经伤害她的人复仇',
    '带着前世的记忆重生，这一次她要拿回属于自己的一切',
    ARRAY['重生', '复仇', '正义', '成长', '谋略'],
    ARRAY['死亡', '重生', '觉醒', '布局', '反击', '胜利'],
    '{"overall": "intense", "emotional_arc": "triumphant", "pacing": "fast"}'::JSONB,
    92.0,
    true
),
(
    '先婚后爱',
    'Married First, Love Later',
    'contract-marriage',
    'romance',
    ARRAY['marriage', 'slow_burn', 'modern'],
    ARRAY['契约婚姻', '先婚后爱', '日久生情', '甜宠'],
    '{"age_range": "22-38", "gender": "female", "interests": ["romance", "family"]}'::JSONB,
    '两个陌生人因为某种原因被迫结婚，在共同生活中逐渐产生真挚感情',
    '一场契约婚姻，却在日常相处中擦出真爱火花',
    ARRAY['婚姻', '爱情', '信任', '成长', '家庭'],
    ARRAY['被迫结婚', '陌生', '摩擦', '了解', '心动', '真爱'],
    '{"overall": "warm", "emotional_arc": "gradual", "pacing": "moderate"}'::JSONB,
    88.5,
    true
);

-- Insert sample theme elements
INSERT INTO theme_elements (theme_id, element_type, name, description, config, weight, is_required)
SELECT 
    t.id,
    'character',
    '霸道总裁',
    '高冷、能力强、外表英俊的企业总裁，内心温柔',
    '{"role": "protagonist", "traits": ["dominant", "capable", "protective"], "archetype": "alpha_male"}'::JSONB,
    1.0,
    true
FROM themes t WHERE t.slug = 'ceo-romance';

INSERT INTO theme_elements (theme_id, element_type, name, description, config, weight, is_required)
SELECT 
    t.id,
    'trope',
    '误会与和解',
    '男女主角之间产生误会，最终通过沟通和理解化解矛盾',
    '{"frequency": "high", "variation": "communication"}'::JSONB,
    0.9,
    false
FROM themes t WHERE t.slug = 'ceo-romance';

INSERT INTO theme_elements (theme_id, element_type, name, description, config, weight, is_required)
SELECT 
    t.id,
    'character',
    '重生女主',
    '带着前世记忆重生的女性主角，聪明、坚韧、有仇必报',
    '{"role": "protagonist", "traits": ["intelligent", "resilient", "determined"], "archetype": "avenger"}'::JSONB,
    1.0,
    true
FROM themes t WHERE t.slug = 'reborn-revenge';

-- ============================================
-- Views for Common Queries
-- ============================================

-- 热门主题视图
CREATE VIEW popular_themes AS
SELECT 
    t.*,
    COUNT(te.id) as element_count
FROM themes t
LEFT JOIN theme_elements te ON te.theme_id = t.id AND te.is_active = true
WHERE t.status = 'active'
GROUP BY t.id
ORDER BY t.popularity_score DESC;

-- 主题详情视图（包含元素）
CREATE VIEW theme_details AS
SELECT 
    t.*,
    json_agg(
        json_build_object(
            'id', te.id,
            'type', te.element_type,
            'name', te.name,
            'description', te.description,
            'config', te.config,
            'weight', te.weight,
            'is_required', te.is_required
        )
    ) FILTER (WHERE te.id IS NOT NULL) as elements
FROM themes t
LEFT JOIN theme_elements te ON te.theme_id = t.id AND te.is_active = true
GROUP BY t.id;

-- ============================================
-- Comments
-- ============================================

COMMENT ON TABLE themes IS '短剧主题库，存储所有可用的故事主题';
COMMENT ON TABLE theme_elements IS '主题元素，包括角色原型、情节套路、场景设定等';
COMMENT ON TABLE theme_trends IS '主题趋势数据，用于热门度分析';
COMMENT ON TABLE user_preferences IS '用户偏好设置';
COMMENT ON TABLE projects IS '用户创建的项目';
COMMENT ON TABLE project_content IS '项目各阶段生成的内容';
