-- Migration: Create market_reports table for caching market analysis
-- Created: 2026-02-05

-- 市场分析报告表
CREATE TABLE IF NOT EXISTS market_reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    report_type VARCHAR(50) NOT NULL DEFAULT 'weekly', -- weekly, daily, on_demand
    genres JSONB NOT NULL DEFAULT '[]'::jsonb, -- 题材推荐列表
    tones JSONB NOT NULL DEFAULT '[]'::jsonb, -- 内容调性列表
    insights TEXT NOT NULL DEFAULT '', -- 市场洞察总结
    target_audience TEXT NOT NULL DEFAULT '', -- 目标受众
    search_queries JSONB DEFAULT '[]'::jsonb, -- 使用的搜索查询
    raw_search_results TEXT, -- 原始搜索结果（可选）
    is_active BOOLEAN NOT NULL DEFAULT true,
    valid_until TIMESTAMP WITH TIME ZONE, -- 有效期（缓存过期时间）
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_market_reports_type ON market_reports(report_type);
CREATE INDEX IF NOT EXISTS idx_market_reports_active ON market_reports(is_active) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_market_reports_created ON market_reports(created_at DESC);

-- 添加注释
COMMENT ON TABLE market_reports IS '市场分析报告缓存表，用于存储AI分析的市场趋势数据';
COMMENT ON COLUMN market_reports.genres IS '题材推荐列表，包含id, name, description, trend等字段';
COMMENT ON COLUMN market_reports.tones IS '内容调性列表，如["爽感", "甜宠", "悬疑"]';
COMMENT ON COLUMN market_reports.valid_until IS '缓存有效期，超过此时间需要重新生成';

-- 创建自动更新updated_at的触发器
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS update_market_reports_updated_at ON market_reports;
CREATE TRIGGER update_market_reports_updated_at
    BEFORE UPDATE ON market_reports
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- 插入默认数据（首次运行时的初始数据）
INSERT INTO market_reports (report_type, genres, tones, insights, target_audience, valid_until)
VALUES (
    'default',
    '[
        {"id": "urban", "name": "现代都市", "description": "职场、爱情、生活", "trend": "up"},
        {"id": "revenge", "name": "逆袭复仇", "description": "打脸、爽文、重生", "trend": "hot"},
        {"id": "fantasy", "name": "奇幻仙侠", "description": "修仙、玄幻、系统", "trend": "stable"},
        {"id": "sweet", "name": "甜宠恋爱", "description": "高甜、治愈、双向奔赴", "trend": "up"},
        {"id": "suspense", "name": "悬疑推理", "description": "烧脑、反转、探案", "trend": "up"}
    ]'::jsonb,
    '["爽感", "甜宠", "悬疑", "治愈", "热血"]'::jsonb,
    '基于当前市场趋势，复仇题材和都市情感题材表现优异。甜宠类内容在节假日期间有明显增长，悬疑类在年轻用户群体中热度上升。',
    '18-35岁女性用户为主，下沉市场增长明显',
    NOW() + INTERVAL '7 days'
)
ON CONFLICT DO NOTHING;
