-- =====================================================
-- Migration: 009_generated_plans_history.sql
-- Description: 创建方案生成历史记录表，用于去重和偏好学习
-- Author: AI Video Engine Team
-- Date: 2026-02-10
-- =====================================================

-- =====================================================
-- 表: generated_plans_history (方案生成历史)
-- 说明: 记录用户生成的方案历史，用于去重和偏好学习
-- =====================================================

CREATE TABLE IF NOT EXISTS generated_plans_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) NOT NULL,
    project_id UUID REFERENCES projects(id),
    
    -- 方案内容指纹
    plan_title TEXT NOT NULL,  -- 方案标题
    plan_summary TEXT,  -- 一句话梗概
    core_tropes JSONB DEFAULT '[]'::jsonb,  -- 核心元素列表
    genre_combination JSONB DEFAULT '[]'::jsonb,  -- 题材组合
    
    -- 生成参数
    background_setting TEXT,  -- 背景设定
    total_episodes INTEGER DEFAULT 80,  -- 总集数
    episode_duration DECIMAL(3,1) DEFAULT 1.5,  -- 每集时长
    
    -- 完整方案数据（可选）
    plan_data JSONB DEFAULT '{}'::jsonb,  -- 完整方案JSON
    
    -- 生成上下文
    market_report_id UUID,  -- 使用的市场报告ID
    theme_slugs JSONB DEFAULT '[]'::jsonb,  -- 使用的主题列表
    
    -- 用户反馈
    user_selected BOOLEAN DEFAULT FALSE,  -- 用户是否选择
    user_regenerated BOOLEAN DEFAULT FALSE,  -- 用户是否重新生成
    user_feedback JSONB DEFAULT '{}'::jsonb,  -- 用户反馈详情
    
    -- 相似度分析
    embedding VECTOR(1536),  -- 用于语义相似度计算
    similarity_hash TEXT,  -- 简单相似度哈希
    
    -- 生成时间
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 索引
CREATE INDEX idx_gen_plans_user ON generated_plans_history(user_id);
CREATE INDEX idx_gen_plans_project ON generated_plans_history(project_id);
CREATE INDEX idx_gen_plans_time ON generated_plans_history(generated_at DESC);
CREATE INDEX idx_gen_plans_tropes ON generated_plans_history USING GIN(core_tropes);
CREATE INDEX idx_gen_plans_genres ON generated_plans_history USING GIN(genre_combination);
CREATE INDEX idx_gen_plans_selected ON generated_plans_history(user_selected) WHERE user_selected = true;

-- 注释
COMMENT ON TABLE generated_plans_history IS '记录用户生成的方案历史，用于去重和偏好学习';
COMMENT ON COLUMN generated_plans_history.core_tropes IS '方案使用的核心元素，用于相似度比对';
COMMENT ON COLUMN generated_plans_history.genre_combination IS '方案使用的题材组合';
COMMENT ON COLUMN generated_plans_history.embedding IS '语义向量，用于计算方案相似度';
COMMENT ON COLUMN generated_plans_history.similarity_hash IS '简单字符串哈希，用于快速去重';

-- =====================================================
-- 表: user_plan_preferences (用户方案偏好)
-- 说明: 学习用户的偏好，用于个性化推荐
-- =====================================================

CREATE TABLE IF NOT EXISTS user_plan_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) NOT NULL UNIQUE,
    
    -- 偏好统计
    preferred_tropes JSONB DEFAULT '{}'::jsonb,  -- 喜欢的元素及权重
    preferred_genres JSONB DEFAULT '{}'::jsonb,  -- 喜欢的题材及权重
    preferred_settings JSONB DEFAULT '{}'::jsonb,  -- 喜欢的背景设定
    
    -- 避免列表
    avoided_tropes JSONB DEFAULT '[]'::jsonb,  -- 不喜欢的元素
    avoided_combinations JSONB DEFAULT '[]'::jsonb,  -- 不喜欢的组合
    
    -- 统计数据
    total_generated INTEGER DEFAULT 0,  -- 总共生成数量
    total_selected INTEGER DEFAULT 0,  -- 被选择的数量
    regeneration_rate DECIMAL(5,2) DEFAULT 0,  -- 重新生成率
    
    -- 元数据
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 索引
CREATE INDEX idx_user_prefs_user ON user_plan_preferences(user_id);

-- 注释
COMMENT ON TABLE user_plan_preferences IS '用户方案偏好，用于个性化推荐和去重';

-- =====================================================
-- Row Level Security (RLS) 策略
-- =====================================================

-- 启用RLS
ALTER TABLE generated_plans_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_plan_preferences ENABLE ROW LEVEL SECURITY;

-- 用户只能查看自己的历史
CREATE POLICY "Users can view own plan history" ON generated_plans_history
    FOR SELECT USING (user_id = auth.uid());

CREATE POLICY "Users can insert own plan history" ON generated_plans_history
    FOR INSERT WITH CHECK (user_id = auth.uid());

CREATE POLICY "Users can update own plan history" ON generated_plans_history
    FOR UPDATE USING (user_id = auth.uid());

-- 用户偏好只能自己访问
CREATE POLICY "Users can view own preferences" ON user_plan_preferences
    FOR SELECT USING (user_id = auth.uid());

CREATE POLICY "Users can upsert own preferences" ON user_plan_preferences
    FOR ALL USING (user_id = auth.uid())
    WITH CHECK (user_id = auth.uid());

-- 服务角色可以读写所有
CREATE POLICY "Service role can manage plan history" ON generated_plans_history
    FOR ALL USING (auth.role() = 'service_role')
    WITH CHECK (auth.role() = 'service_role');

CREATE POLICY "Service role can manage preferences" ON user_plan_preferences
    FOR ALL USING (auth.role() = 'service_role')
    WITH CHECK (auth.role() = 'service_role');

-- =====================================================
-- 函数: 计算方案相似度哈希
-- =====================================================

CREATE OR REPLACE FUNCTION calculate_plan_hash(
    p_title TEXT,
    p_tropes JSONB,
    p_genres JSONB
) RETURNS TEXT AS $$
DECLARE
    v_hash_input TEXT;
BEGIN
    -- 组合关键字段生成哈希输入
    v_hash_input := LOWER(COALESCE(p_title, '')) || 
                    COALESCE(p_tropes::TEXT, '[]') || 
                    COALESCE(p_genres::TEXT, '[]');
    
    -- 返回MD5哈希
    RETURN MD5(v_hash_input);
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- 函数: 查找相似方案
-- =====================================================

CREATE OR REPLACE FUNCTION find_similar_plans(
    p_user_id UUID,
    p_tropes JSONB,
    p_genres JSONB,
    p_threshold DECIMAL DEFAULT 0.7,
    p_days INTEGER DEFAULT 30
) RETURNS TABLE (
    plan_id UUID,
    similarity_score DECIMAL,
    plan_title TEXT,
    generated_at TIMESTAMP WITH TIME ZONE
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        gph.id as plan_id,
        (
            -- 计算Jaccard相似度: 交集/并集
            CASE 
                WHEN jsonb_array_length(gph.core_tropes) > 0 AND jsonb_array_length(p_tropes) > 0 THEN
                    (SELECT COUNT(*)::DECIMAL FROM jsonb_array_elements_text(gph.core_tropes) elem 
                     WHERE elem IN (SELECT jsonb_array_elements_text(p_tropes))) /
                    (SELECT COUNT(DISTINCT elem)::DECIMAL FROM (
                        SELECT jsonb_array_elements_text(gph.core_tropes) elem
                        UNION
                        SELECT jsonb_array_elements_text(p_tropes) elem
                    ) all_elems)
                ELSE 0.0
            END * 0.4 +
            -- 题材组合相似度
            CASE 
                WHEN jsonb_array_length(gph.genre_combination) > 0 AND jsonb_array_length(p_genres) > 0 THEN
                    (SELECT COUNT(*)::DECIMAL FROM jsonb_array_elements_text(gph.genre_combination) elem 
                     WHERE elem IN (SELECT jsonb_array_elements_text(p_genres))) /
                    (SELECT COUNT(DISTINCT elem)::DECIMAL FROM (
                        SELECT jsonb_array_elements_text(gph.genre_combination) elem
                        UNION
                        SELECT jsonb_array_elements_text(p_genres) elem
                    ) all_elems)
                ELSE 0.0
            END * 0.6
        )::DECIMAL as similarity_score,
        gph.plan_title,
        gph.generated_at
    FROM generated_plans_history gph
    WHERE gph.user_id = p_user_id
        AND gph.generated_at > NOW() - INTERVAL '1 day' * p_days
    HAVING (
        CASE 
            WHEN jsonb_array_length(gph.core_tropes) > 0 AND jsonb_array_length(p_tropes) > 0 THEN
                (SELECT COUNT(*)::DECIMAL FROM jsonb_array_elements_text(gph.core_tropes) elem 
                 WHERE elem IN (SELECT jsonb_array_elements_text(p_tropes))) /
                (SELECT COUNT(DISTINCT elem)::DECIMAL FROM (
                    SELECT jsonb_array_elements_text(gph.core_tropes) elem
                    UNION
                    SELECT jsonb_array_elements_text(p_tropes) elem
                ) all_elems)
            ELSE 0.0
        END * 0.4 +
        CASE 
            WHEN jsonb_array_length(gph.genre_combination) > 0 AND jsonb_array_length(p_genres) > 0 THEN
                (SELECT COUNT(*)::DECIMAL FROM jsonb_array_elements_text(gph.genre_combination) elem 
                 WHERE elem IN (SELECT jsonb_array_elements_text(p_genres))) /
                (SELECT COUNT(DISTINCT elem)::DECIMAL FROM (
                    SELECT jsonb_array_elements_text(gph.genre_combination) elem
                    UNION
                    SELECT jsonb_array_elements_text(p_genres) elem
                ) all_elems)
            ELSE 0.0
        END * 0.6
    ) >= p_threshold
    ORDER BY similarity_score DESC, gph.generated_at DESC
    LIMIT 5;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- 触发器: 自动计算相似度哈希
-- =====================================================

CREATE OR REPLACE FUNCTION set_plan_hash()
RETURNS TRIGGER AS $$
BEGIN
    NEW.similarity_hash := calculate_plan_hash(
        NEW.plan_title,
        NEW.core_tropes,
        NEW.genre_combination
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_set_plan_hash ON generated_plans_history;
CREATE TRIGGER trigger_set_plan_hash
    BEFORE INSERT OR UPDATE ON generated_plans_history
    FOR EACH ROW EXECUTE FUNCTION set_plan_hash();
