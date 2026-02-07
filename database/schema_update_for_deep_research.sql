-- ============================================
-- 数据库字段更新 - 支持Deep Research报告数据
-- 基于v4.1架构和Deep Research报告
-- ============================================

-- ============================================
-- 1. 更新 themes 表 - 添加核心公式字段
-- ============================================

-- 添加四阶段核心公式字段
ALTER TABLE themes ADD COLUMN IF NOT EXISTS core_formula JSONB DEFAULT '{}';
COMMENT ON COLUMN themes.core_formula IS '四阶段核心公式：Setup → Rising → Climax → Resolution';

-- 添加细分关键词字段（写作+视觉）
ALTER TABLE themes ADD COLUMN IF NOT EXISTS keywords JSONB DEFAULT '{}';
COMMENT ON COLUMN themes.keywords IS '关键词分类：{"writing": [...], "visual": [...]}';

-- 添加目标受众详细字段（覆盖Deep Research的受众画像）
ALTER TABLE themes ADD COLUMN IF NOT EXISTS audience_analysis JSONB DEFAULT '{}';
COMMENT ON COLUMN themes.audience_analysis IS '受众深度分析：{
  "age_range": "18-35",
  "gender": "female",
  "psychographics": "心理特征",
  "pain_points": ["痛点1", "痛点2"],
  "emotional_needs": ["需求1", "需求2"]
}';

-- 添加市场规模数据
ALTER TABLE themes ADD COLUMN IF NOT EXISTS market_size JSONB DEFAULT '{}';
COMMENT ON COLUMN themes.market_size IS '市场规模数据：{
  "market_share": "市场份额",
  "growth_rate": "增长率",
  "revenue": "收入规模"
}';

-- ============================================
-- 2. 更新 theme_elements 表 - 添加效果评分
-- ============================================

-- 添加效果评分字段（Deep Research中的95分、92分等）
ALTER TABLE theme_elements ADD COLUMN IF NOT EXISTS effectiveness_score DECIMAL(5,2) DEFAULT 0;
COMMENT ON COLUMN theme_elements.effectiveness_score IS '效果评分（0-100），基于市场验证';

-- 添加使用时机指导
ALTER TABLE theme_elements ADD COLUMN IF NOT EXISTS usage_guidance JSONB DEFAULT '{}';
COMMENT ON COLUMN theme_elements.usage_guidance IS '使用指导：{
  "best_timing": "最佳使用时机（如第10-15集）",
  "preparation": "前期铺垫要求",
  "execution_tips": "执行技巧",
  "variations": ["变体1", "变体2"]
}';

-- 添加风险提示
ALTER TABLE theme_elements ADD COLUMN IF NOT EXISTS risk_factors TEXT[] DEFAULT '{}';
COMMENT ON COLUMN theme_elements.risk_factors IS '风险提示（如["过早揭露会削弱效果"]）';

-- ============================================
-- 3. 创建 theme_examples 表 - 标杆案例
-- ============================================

CREATE TABLE IF NOT EXISTS theme_examples (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    theme_id UUID NOT NULL REFERENCES themes(id) ON DELETE CASCADE,
    
    -- 案例基本信息
    example_type VARCHAR(50) NOT NULL,  -- 'drama'(短剧), 'novel'(小说), 'movie'(电影)
    title VARCHAR(500) NOT NULL,        -- 案例名称，如《黑莲花上位手册》
    alternative_title VARCHAR(500),     -- 别名/英文名称
    release_year INTEGER,               -- 发布年份
    
    -- 案例描述
    description TEXT,                   -- 案例描述
    storyline_summary TEXT,             -- 剧情概要
    
    -- 成就数据（JSONB灵活存储）
    achievements JSONB DEFAULT '{}',
    -- {
    --   "revenue": "2000万",           -- 收入/分账
    --   "views": "30亿",               -- 播放量
    --   "awards": ["分账冠军", "热度第一"],
    --   "records": ["24小时充值破2000万"],
    --   "retention_rate": "62%"        -- 留存率
    -- }
    
    -- 成功因素
    key_success_factors TEXT[],         -- 成功关键因素
    unique_selling_points TEXT[],       -- 独特卖点
    
    -- 可借鉴点
    learnings TEXT,                     -- 可借鉴的创作技巧
    applicable_elements UUID[],         -- 引用的theme_elements ID
    
    -- 市场数据
    market_performance JSONB DEFAULT '{}',
    -- {
    --   "trending_duration": "30天",   -- 热门持续时间
    --   "peak_rank": 1,                -- 最高排名
    --   "audience_rating": 4.8         -- 观众评分
    -- }
    
    -- 外部链接
    external_links JSONB DEFAULT '{}',
    -- {
    --   "platform_url": "播放链接",
    --   "review_article": "分析文章链接",
    --   "trailer": "预告片链接"
    -- }
    
    -- 状态
    is_verified BOOLEAN DEFAULT false,  -- 是否已验证（真实爆款）
    verification_source TEXT,           -- 验证来源（如DataEye、艾瑞咨询）
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_theme_examples_theme_id ON theme_examples(theme_id);
CREATE INDEX IF NOT EXISTS idx_theme_examples_type ON theme_examples(example_type);
CREATE INDEX IF NOT EXISTS idx_theme_examples_year ON theme_examples(release_year);
CREATE INDEX IF NOT EXISTS idx_theme_examples_verified ON theme_examples(is_verified) WHERE is_verified = true;

-- 触发器：自动更新updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER IF NOT EXISTS update_theme_examples_updated_at
    BEFORE UPDATE ON theme_examples
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- 4. 创建 hook_templates 表 - 钩子模板库
-- ============================================

CREATE TABLE IF NOT EXISTS hook_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- 钩子类型
    hook_type VARCHAR(100) NOT NULL,    -- 'situation'(情境型), 'question'(悬念型), 'visual'(视觉型)
    
    -- 钩子名称和描述
    name VARCHAR(255) NOT NULL,         -- 钩子名称，如"极限羞辱"
    template TEXT NOT NULL,             -- 模板文本，如"主角正在遭受[羞辱]，倒计时[3,2,1]即将反击"
    
    -- 模板变量定义
    variables JSONB DEFAULT '{}',
    -- {
    --   "羞辱类型": ["被当众退婚", "被经理泼咖啡"],
    --   "反击方式": ["暴露身份", "展示实力"]
    -- }
    
    -- 效果数据
    effectiveness_score DECIMAL(5,2) DEFAULT 0,  -- 效果评分（95分等）
    psychology_mechanism TEXT,          -- 心理机制说明
    
    -- 使用约束
    usage_constraints JSONB DEFAULT '{}',
    -- {
    --   "must_follow_up": "必须在5集内反击",
    --   "avoid": "不要过度虐待",
    --   "tone": "压抑中带有隐忍"
    -- }
    
    -- 适用题材
    applicable_genres TEXT[],           -- 适用的题材列表
    applicable_episodes VARCHAR(50),    -- 适用集数（如"第1集前30秒"）
    
    -- 示例
    examples JSONB DEFAULT '[]',
    -- [
    --   {
    --     "scenario": "被当众退婚",
    --     "hook_text": "具体钩子文案",
    --     "effectiveness": "高",
    --     "completion_rate": "完播率数据"
    --   }
    -- ]
    
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

-- 触发器
CREATE TRIGGER IF NOT EXISTS update_hook_templates_updated_at
    BEFORE UPDATE ON hook_templates
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- 5. 创建 market_insights 表 - 市场洞察
-- ============================================

CREATE TABLE IF NOT EXISTS market_insights (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- 统计周期
    period_start DATE NOT NULL,         -- 统计开始日期
    period_end DATE NOT NULL,           -- 统计结束日期
    period_type VARCHAR(50) NOT NULL,   -- 'weekly', 'monthly', 'quarterly', 'yearly'
    
    -- 整体市场数据
    market_overview JSONB DEFAULT '{}',
    -- {
    --   "total_revenue": "504.4亿",
    --   "user_count": "6.62亿",
    --   "growth_rate": "25.7%"
    -- }
    
    -- 题材热度排名
    genre_rankings JSONB DEFAULT '[]',
    -- [
    --   {"genre_id": "...", "rank": 1, "heat_score": 95, "market_share": "18%"}
    -- ]
    
    -- 热门组合
    trending_combinations JSONB DEFAULT '[]',
    -- [
    --   {
    --     "name": "复仇+甜宠",
    --     "genres": ["revenge", "sweet"],
    --     "heat_score": 92,
    --     "example": "《我在八零年代当后妈》"
    --   }
    -- ]
    
    -- 新兴趋势
    emerging_trends TEXT[],             -- 新兴趋势列表
    
    -- 数据来源
    data_sources TEXT[],                -- 数据来源（如DataEye、艾瑞咨询）
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_market_insights_period ON market_insights(period_start, period_end);
CREATE INDEX IF NOT EXISTS idx_market_insights_type ON market_insights(period_type);

-- ============================================
-- 6. 创建视图 - 方便查询
-- ============================================

-- 主题完整信息视图（包含公式、元素、案例）
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
            )
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
            )
        )
        FROM theme_examples tex
        WHERE tex.theme_id = t.id AND tex.is_verified = true
    ) as verified_examples
FROM themes t
WHERE t.status = 'active';

-- 热门元素视图
CREATE OR REPLACE VIEW popular_elements AS
SELECT 
    te.*,
    t.name as theme_name,
    t.slug as theme_slug
FROM theme_elements te
JOIN themes t ON te.theme_id = t.id
WHERE te.is_active = true
ORDER BY te.effectiveness_score DESC;

-- ============================================
-- 7. 数据导入示例（基于Deep Research报告）
-- ============================================

-- 插入复仇逆袭题材数据示例
INSERT INTO themes (
    name, name_en, slug, category, 
    description, summary,
    core_formula, keywords, audience_analysis, market_size,
    popularity_score, success_rate,
    example_loglines, example_titles,
    status, is_featured
) VALUES (
    '复仇逆袭', 'Revenge & Comeback', 'revenge', 'drama',
    '主角遭受不公，通过努力或隐藏身份实现逆袭打脸',
    '当灰姑娘遇到霸道总裁，一场甜蜜又曲折的爱情冒险',
    '{
        "setup": {
            "episodes": "第1-5集（10-15%）",
            "task": "悲情渲染与仇恨种子埋设",
            "key_elements": ["至亲被害", "财产被夺", "当众羞辱"],
            "emotional_goal": "让观众产生同情和愤怒",
            "avoid": "不要过度虐待主角（不超过3集无反击）"
        },
        "rising": {
            "episodes": "第6-30集（30-40%）",
            "task": "隐忍蓄力与身份/能力提升",
            "key_elements": ["隐藏身份", "获取金手指", "建立盟友"],
            "pacing": "每3集一个小打脸，保持爽感"
        },
        "climax": {
            "episodes": "第31-70集（40-50%）",
            "task": "层层反击与终极对决",
            "key_elements": ["身份揭露", "证据公开", "权力碾压"],
            "satisfaction_curve": "身份揭露→打脸1→打脸2→打脸3（递进）"
        },
        "resolution": {
            "episodes": "第71-80+集（10-15%）",
            "task": "复仇完成与新身份确立",
            "key_elements": ["反派下场", "情感收束", "主题升华"],
            "avoid": "圣母原谅（主角必须彻底胜利）"
        }
    }'::jsonb,
    '{
        "writing": ["红眼", "掐腰", "居高临下", "冷笑", "颤抖"],
        "visual": ["破碎感", "逆光", "高对比", "权力象征"]
    }'::jsonb,
    '{
        "age_range": "18-35",
        "gender": "female",
        "psychographics": "追求爽感的都市女性",
        "pain_points": ["职场不公", "情感背叛", "社会阶层固化"],
        "emotional_needs": ["正义伸张", "身份认同", "逆袭快感"]
    }'::jsonb,
    '{
        "market_share": "25%",
        "growth_rate": "stable",
        "average_roi": "1:3.5"
    }'::jsonb,
    95.5, 88.0,
    ARRAY['当少女魂穿太奶奶，整顿家风不含糊', '离婚后我成了billionaire，前夫跪求复合'],
    ARRAY['《黑莲花上位手册》', '《幸得相遇离婚时》', '《战神归来》'],
    'active', true
) ON CONFLICT (slug) DO UPDATE SET
    core_formula = EXCLUDED.core_formula,
    keywords = EXCLUDED.keywords,
    audience_analysis = EXCLUDED.audience_analysis,
    updated_at = NOW();

-- 插入爆款元素示例
INSERT INTO theme_elements (
    theme_id, element_type, name, description,
    config, effectiveness_score, usage_guidance, risk_factors,
    weight, is_required
) 
SELECT 
    t.id, 'trope', '身份揭露', '主角真实身份在关键时刻暴露，震惊全场',
    '{
        "type": "identity",
        "preparation": "前期埋设3-5个身份线索",
        "execution_steps": [
            "1. 反派再次挑衅（营造紧张）",
            "2. 主角被逼入绝境（增加悬念）",
            "3. 关键人物出现/证据曝光（触发点）",
            "4. 身份揭露（高潮）",
            "5. 全场震惊反应（爽点）"
        ],
        "dialogue_template": "没想到吧，我才是真正的[身份]"
    }'::jsonb,
    95.0,
    '{
        "best_timing": "第10-15集效果最佳",
        "preparation": "需要前期铺垫3-5集",
        "execution": "揭露时机要配合高潮场景"
    }'::jsonb,
    ARRAY['过早揭露会削弱效果', '铺垫不足会显得突兀'],
    1.0, true
FROM themes t WHERE t.slug = 'revenge'
ON CONFLICT DO NOTHING;

-- 插入标杆案例示例
INSERT INTO theme_examples (
    theme_id, example_type, title, release_year,
    description, achievements, key_success_factors,
    is_verified, verification_source
)
SELECT 
    t.id, 'drama', '《黑莲花上位手册》', 2024,
    '24小时充值破2000万，因极端暴力被下架，但商业成功不可否认',
    '{
        "revenue": "2000万（24小时）",
        "records": ["24小时充值破2000万"],
        "controversy": "因极端暴力被下架"
    }'::jsonb,
    ARRAY['极端羞辱反转为极致爽感', '快速建立冲突', '强情绪刺激'],
    true, 'DataEye研究院'
FROM themes t WHERE t.slug = 'revenge'
ON CONFLICT DO NOTHING;

-- ============================================
-- 完成
-- ============================================

COMMENT ON TABLE themes IS '短剧主题库，包含核心公式、关键词、受众分析等完整数据';
COMMENT ON TABLE theme_elements IS '主题元素（Trope/Hook/Character等），包含效果评分和使用指导';
COMMENT ON TABLE theme_examples IS '标杆案例库，存储真实爆款的详细数据和成功因素';
COMMENT ON TABLE hook_templates IS '钩子模板库，包含模板文本、变量定义、使用效果数据';
COMMENT ON TABLE market_insights IS '市场洞察数据，包含趋势分析、热度排名、热门组合';
