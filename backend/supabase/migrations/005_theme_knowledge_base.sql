-- =====================================================
-- Migration: 005_theme_knowledge_base.sql
-- Description: 创建题材知识库表 - 存储Deep Research报告数据
-- Author: AI Video Engine Team
-- Date: 2026-02-07
-- =====================================================

-- =====================================================
-- 表: themes (题材主题库)
-- 说明: 存储短剧题材的核心信息、公式、关键词
-- =====================================================

CREATE TABLE IF NOT EXISTS themes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- 基本信息
    slug VARCHAR(100) NOT NULL UNIQUE,      -- URL友好的标识，如 revenge, romance
    name VARCHAR(100) NOT NULL,             -- 显示名称，如"复仇逆袭"
    name_en VARCHAR(100),                   -- 英文名
    category VARCHAR(50) NOT NULL,          -- 分类：drama, romance, thriller, fantasy
    
    -- 描述
    description TEXT NOT NULL,              -- 题材描述
    summary TEXT,                           -- 一句话总结
    
    -- 核心公式 (Deep Research四阶段结构)
    core_formula JSONB DEFAULT '{}'::jsonb,
    /*
    {
      "setup": {
        "episodes": "第1-5集",
        "task": "悲情渲染与仇恨种子埋设",
        "key_elements": ["至亲被害", "财产被夺"],
        "emotional_goal": "让观众产生强烈同情",
        "avoid": "不要过度虐待主角"
      },
      "rising": { ... },
      "climax": { ... },
      "resolution": { ... }
    }
    */
    
    -- 关键词 (写作 + 视觉)
    keywords JSONB DEFAULT '{}'::jsonb,
    /*
    {
      "writing": ["红眼", "掐腰", "居高临下"],
      "visual": ["破碎感", "逆光", "高对比"]
    }
    */
    
    -- 目标受众分析
    audience_analysis JSONB DEFAULT '{}'::jsonb,
    /*
    {
      "age_range": "18-35",
      "gender": "female",
      "psychographics": "渴望自我成长、追求公平正义",
      "pain_points": ["职场不公", "情感背叛"],
      "emotional_needs": ["爽感", "认同感"]
    }
    */
    
    -- 市场规模数据
    market_size JSONB DEFAULT '{}'::jsonb,
    /*
    {
      "market_share": "25%",
      "growth_rate": "35%",
      "revenue": "100亿+"
    }
    */
    
    -- 评分
    market_score DECIMAL(5,2) DEFAULT 0,    -- 市场热度评分 (0-100)
    success_rate DECIMAL(5,2) DEFAULT 0,    -- 成功率 (0-100)
    
    -- 状态
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'deprecated')),
    is_active BOOLEAN DEFAULT true,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_themes_slug ON themes(slug);
CREATE INDEX IF NOT EXISTS idx_themes_category ON themes(category);
CREATE INDEX IF NOT EXISTS idx_themes_status ON themes(status);
CREATE INDEX IF NOT EXISTS idx_themes_active ON themes(is_active) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_themes_market_score ON themes(market_score DESC);

-- 注释
COMMENT ON TABLE themes IS '题材主题库 - 存储短剧题材的核心信息、四阶段公式、关键词';
COMMENT ON COLUMN themes.core_formula IS '四阶段核心公式：Setup → Rising → Climax → Resolution';
COMMENT ON COLUMN themes.keywords IS '关键词分类：{"writing": [...], "visual": [...]}';
COMMENT ON COLUMN themes.audience_analysis IS '受众深度分析：年龄、性别、心理特征、痛点';


-- =====================================================
-- 表: theme_elements (爆款元素库)
-- 说明: 每个题材下的具体爆款元素、桥段
-- =====================================================

CREATE TABLE IF NOT EXISTS theme_elements (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    theme_id UUID NOT NULL REFERENCES themes(id) ON DELETE CASCADE,
    
    -- 元素类型
    element_type VARCHAR(50) NOT NULL,      -- trope(桥段), character(人设), plot(剧情), visual(视觉)
    
    -- 基本信息
    name VARCHAR(200) NOT NULL,             -- 元素名称，如"隐藏大佬"
    name_en VARCHAR(200),                   -- 英文名
    description TEXT,                       -- 详细描述
    
    -- 效果评分 (Deep Research数据)
    effectiveness_score DECIMAL(5,2) DEFAULT 0,  -- 效果评分 0-100
    weight DECIMAL(3,2) DEFAULT 1.0,        -- 权重 0-1
    
    -- 使用指导
    usage_guidance JSONB DEFAULT '{}'::jsonb,
    /*
    {
      "best_timing": "第10-15集效果最佳",
      "preparation": "需要前期铺垫3-5集",
      "execution_tips": "配合特写镜头和慢动作",
      "variations": ["变体1", "变体2"]
    }
    */
    
    -- 风险提示
    risk_factors TEXT[] DEFAULT '{}',
    
    -- 情感影响力
    emotional_impact JSONB DEFAULT '{}'::jsonb,
    /*
    {
      "satisfaction": 95,
      "surprise": 90,
      "replay_value": 85
    }
    */
    
    -- 经典案例引用
    classic_examples JSONB DEFAULT '[]'::jsonb,
    /*
    [
      {
        "drama": "好一个乖乖女",
        "scene": "画展上揭露身份",
        "why_effective": "配合高潮场景，反差强烈"
      }
    ]
    */
    
    -- 状态
    is_active BOOLEAN DEFAULT true,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_theme_elements_theme_id ON theme_elements(theme_id);
CREATE INDEX IF NOT EXISTS idx_theme_elements_type ON theme_elements(element_type);
CREATE INDEX IF NOT EXISTS idx_theme_elements_score ON theme_elements(effectiveness_score DESC);
CREATE INDEX IF NOT EXISTS idx_theme_elements_active ON theme_elements(is_active) WHERE is_active = true;

-- 注释
COMMENT ON TABLE theme_elements IS '爆款元素库 - 存储每个题材下的具体爆款元素和桥段';
COMMENT ON COLUMN theme_elements.effectiveness_score IS '效果评分（0-100），基于市场验证';
COMMENT ON COLUMN theme_elements.usage_guidance IS '使用指导：最佳时机、前期铺垫、执行技巧';


-- =====================================================
-- 表: theme_examples (标杆案例库)
-- 说明: 存储真实爆款短剧的详细数据
-- =====================================================

CREATE TABLE IF NOT EXISTS theme_examples (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    theme_id UUID NOT NULL REFERENCES themes(id) ON DELETE CASCADE,
    
    -- 案例基本信息
    example_type VARCHAR(50) NOT NULL DEFAULT 'drama',  -- drama(短剧), novel(小说), movie(电影)
    title VARCHAR(500) NOT NULL,                        -- 案例名称，如《黑莲花上位手册》
    alternative_title VARCHAR(500),                     -- 别名/英文名称
    release_year INTEGER,                               -- 发布年份
    
    -- 案例描述
    description TEXT,                                   -- 案例描述
    storyline_summary TEXT,                             -- 剧情概要
    
    -- 成就数据（JSONB灵活存储）
    achievements JSONB DEFAULT '{}'::jsonb,
    /*
    {
      "revenue": "2000万",
      "views": "30亿",
      "awards": ["分账冠军", "热度第一"],
      "records": ["24小时充值破2000万"],
      "retention_rate": "62%"
    }
    */
    
    -- 成功因素
    key_success_factors TEXT[],                         -- 成功关键因素
    unique_selling_points TEXT[],                       -- 独特卖点
    
    -- 可借鉴点
    learnings TEXT,                                     -- 可借鉴的创作技巧
    applicable_elements UUID[],                         -- 引用的theme_elements ID
    
    -- 市场数据
    market_performance JSONB DEFAULT '{}'::jsonb,
    /*
    {
      "trending_duration": "30天",
      "peak_rank": 1,
      "audience_rating": 4.8
    }
    */
    
    -- 外部链接
    external_links JSONB DEFAULT '{}'::jsonb,
    /*
    {
      "platform_url": "播放链接",
      "review_article": "分析文章链接",
      "trailer": "预告片链接"
    }
    */
    
    -- 状态
    is_verified BOOLEAN DEFAULT false,                  -- 是否已验证（真实爆款）
    verification_source TEXT,                           -- 验证来源（如DataEye）
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_theme_examples_theme_id ON theme_examples(theme_id);
CREATE INDEX IF NOT EXISTS idx_theme_examples_type ON theme_examples(example_type);
CREATE INDEX IF NOT EXISTS idx_theme_examples_year ON theme_examples(release_year);
CREATE INDEX IF NOT EXISTS idx_theme_examples_verified ON theme_examples(is_verified) WHERE is_verified = true;

-- 注释
COMMENT ON TABLE theme_examples IS '标杆案例库 - 存储真实爆款短剧的详细数据和成功因素';


-- =====================================================
-- 表: hook_templates (钩子模板库)
-- 说明: 前3秒黄金钩子模板
-- =====================================================

CREATE TABLE IF NOT EXISTS hook_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- 钩子类型
    hook_type VARCHAR(100) NOT NULL,        -- situation(情境型), question(悬念型), visual(视觉型)
    
    -- 钩子名称和描述
    name VARCHAR(255) NOT NULL,             -- 钩子名称，如"极限羞辱"
    template TEXT NOT NULL,                 -- 模板文本
    description TEXT,                       -- 描述
    
    -- 模板变量定义
    variables JSONB DEFAULT '{}'::jsonb,
    /*
    {
      "羞辱类型": ["被当众退婚", "被经理泼咖啡"],
      "反击方式": ["暴露身份", "展示实力"]
    }
    */
    
    -- 效果数据
    effectiveness_score DECIMAL(5,2) DEFAULT 0,  -- 效果评分
    psychology_mechanism TEXT,              -- 心理机制说明
    
    -- 使用约束
    usage_constraints JSONB DEFAULT '{}'::jsonb,
    /*
    {
      "must_follow_up": "必须在5集内反击",
      "avoid": "不要过度虐待",
      "tone": "压抑中带有隐忍",
      "duration": "前30秒"
    }
    */
    
    -- 适用题材
    applicable_genres TEXT[],               -- 适用的题材slug列表
    applicable_episodes VARCHAR(50),        -- 适用集数（如"第1集前30秒"）
    
    -- 示例
    examples JSONB DEFAULT '[]'::jsonb,
    /*
    [
      {
        "scenario": "被当众退婚",
        "hook_text": "具体钩子文案",
        "effectiveness": "高",
        "completion_rate": "完播率数据"
      }
    ]
    */
    
    -- 状态
    is_active BOOLEAN DEFAULT true,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_hook_templates_type ON hook_templates(hook_type);
CREATE INDEX IF NOT EXISTS idx_hook_templates_score ON hook_templates(effectiveness_score DESC);
CREATE INDEX IF NOT EXISTS idx_hook_templates_active ON hook_templates(is_active) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_hook_templates_genres ON hook_templates USING GIN(applicable_genres);

-- 注释
COMMENT ON TABLE hook_templates IS '钩子模板库 - 前3秒黄金钩子模板，提高留存率';


-- =====================================================
-- 表: market_insights (市场洞察)
-- 说明: 存储市场趋势分析、热门组合
-- =====================================================

CREATE TABLE IF NOT EXISTS market_insights (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- 统计周期
    period_start DATE NOT NULL,             -- 统计开始日期
    period_end DATE NOT NULL,               -- 统计结束日期
    period_type VARCHAR(50) NOT NULL,       -- weekly, monthly, quarterly, yearly
    
    -- 整体市场数据
    market_overview JSONB DEFAULT '{}'::jsonb,
    /*
    {
      "total_revenue": "504.4亿",
      "user_count": "6.62亿",
      "growth_rate": "25.7%"
    }
    */
    
    -- 题材热度排名
    genre_rankings JSONB DEFAULT '[]'::jsonb,
    /*
    [
      {"genre_id": "uuid", "rank": 1, "heat_score": 95, "market_share": "18%"}
    ]
    */
    
    -- 热门组合
    trending_combinations JSONB DEFAULT '[]'::jsonb,
    /*
    [
      {
        "name": "复仇+甜宠",
        "genres": ["revenge", "sweet"],
        "heat_score": 92,
        "example": "《我在八零年代当后妈》"
      }
    ]
    */
    
    -- 新兴趋势
    emerging_trends TEXT[],                 -- 新兴趋势列表
    
    -- 关键发现
    key_findings TEXT[],                    -- 关键发现列表
    
    -- 数据来源
    data_sources TEXT[],                    -- 数据来源
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_market_insights_period ON market_insights(period_start, period_end);
CREATE INDEX IF NOT EXISTS idx_market_insights_type ON market_insights(period_type);

-- 注释
COMMENT ON TABLE market_insights IS '市场洞察 - 存储市场趋势分析、热门组合、新兴趋势';


-- =====================================================
-- 触发器: 自动更新 updated_at
-- =====================================================

-- 删除已存在的函数（避免权限问题）
DROP FUNCTION IF EXISTS update_updated_at_column() CASCADE;

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 为所有表添加触发器（使用DROP IF EXISTS + CREATE避免重复）
DROP TRIGGER IF EXISTS update_themes_updated_at ON themes;
CREATE TRIGGER update_themes_updated_at
    BEFORE UPDATE ON themes
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_theme_elements_updated_at ON theme_elements;
CREATE TRIGGER update_theme_elements_updated_at
    BEFORE UPDATE ON theme_elements
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_theme_examples_updated_at ON theme_examples;
CREATE TRIGGER update_theme_examples_updated_at
    BEFORE UPDATE ON theme_examples
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_hook_templates_updated_at ON hook_templates;
CREATE TRIGGER update_hook_templates_updated_at
    BEFORE UPDATE ON hook_templates
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();


-- =====================================================
-- 视图: 主题完整信息视图
-- =====================================================

CREATE OR REPLACE VIEW theme_full_details AS
SELECT 
    t.*,
    (
        SELECT json_agg(
            json_build_object(
                'id', te.id,
                'type', te.element_type,
                'name', te.name,
                'score', te.effectiveness_score,
                'weight', te.weight
            ) ORDER BY te.effectiveness_score DESC
        )
        FROM theme_elements te
        WHERE te.theme_id = t.id AND te.is_active = true
    ) as elements,
    (
        SELECT json_agg(
            json_build_object(
                'id', tex.id,
                'title', tex.title,
                'type', tex.example_type,
                'achievements', tex.achievements
            ) ORDER BY tex.created_at DESC
        )
        FROM theme_examples tex
        WHERE tex.theme_id = t.id AND tex.is_verified = true
    ) as verified_examples
FROM themes t
WHERE t.is_active = true;

COMMENT ON VIEW theme_full_details IS '主题完整信息视图 - 包含公式、元素、案例';


-- =====================================================
-- 视图: 热门元素视图
-- =====================================================

CREATE OR REPLACE VIEW popular_elements AS
SELECT 
    te.*,
    t.name as theme_name,
    t.slug as theme_slug
FROM theme_elements te
JOIN themes t ON te.theme_id = t.id
WHERE te.is_active = true
ORDER BY te.effectiveness_score DESC;

COMMENT ON VIEW popular_elements IS '热门元素视图 - 按效果评分排序';


-- =====================================================
-- Row Level Security (RLS) 策略
-- =====================================================

-- 启用RLS
ALTER TABLE themes ENABLE ROW LEVEL SECURITY;
ALTER TABLE theme_elements ENABLE ROW LEVEL SECURITY;
ALTER TABLE theme_examples ENABLE ROW LEVEL SECURITY;
ALTER TABLE hook_templates ENABLE ROW LEVEL SECURITY;
ALTER TABLE market_insights ENABLE ROW LEVEL SECURITY;

-- 所有用户可读策略
CREATE POLICY "All users can read themes" ON themes
    FOR SELECT USING (true);

CREATE POLICY "All users can read theme_elements" ON theme_elements
    FOR SELECT USING (true);

CREATE POLICY "All users can read theme_examples" ON theme_examples
    FOR SELECT USING (true);

CREATE POLICY "All users can read hook_templates" ON hook_templates
    FOR SELECT USING (true);

CREATE POLICY "All users can read market_insights" ON market_insights
    FOR SELECT USING (true);

-- 只有服务角色可以写入
CREATE POLICY "Service role can write themes" ON themes
    FOR ALL USING (auth.role() = 'service_role')
    WITH CHECK (auth.role() = 'service_role');

CREATE POLICY "Service role can write theme_elements" ON theme_elements
    FOR ALL USING (auth.role() = 'service_role')
    WITH CHECK (auth.role() = 'service_role');

CREATE POLICY "Service role can write theme_examples" ON theme_examples
    FOR ALL USING (auth.role() = 'service_role')
    WITH CHECK (auth.role() = 'service_role');

CREATE POLICY "Service role can write hook_templates" ON hook_templates
    FOR ALL USING (auth.role() = 'service_role')
    WITH CHECK (auth.role() = 'service_role');

CREATE POLICY "Service role can write market_insights" ON market_insights
    FOR ALL USING (auth.role() = 'service_role')
    WITH CHECK (auth.role() = 'service_role');
