-- =====================================================
-- Migration: 006_add_trend_direction.sql
-- Description: Add trend_direction column to themes table
-- Author: AI Video Engine Team
-- Date: 2026-02-07
-- =====================================================

-- Add trend_direction column to themes table
ALTER TABLE themes 
ADD COLUMN IF NOT EXISTS trend_direction VARCHAR(20) DEFAULT 'stable' 
CHECK (trend_direction IN ('hot', 'up', 'stable', 'down', 'cold'));

-- Add comment
COMMENT ON COLUMN themes.trend_direction IS '趋势方向: hot(热门), up(上升), stable(稳定), down(下降), cold(冷门)';

-- Create index for trend queries
CREATE INDEX IF NOT EXISTS idx_themes_trend ON themes(trend_direction);

-- Update existing themes with default trend_direction based on market_score
UPDATE themes 
SET trend_direction = CASE 
    WHEN market_score >= 90 THEN 'hot'
    WHEN market_score >= 80 THEN 'up'
    WHEN market_score >= 60 THEN 'stable'
    WHEN market_score >= 40 THEN 'down'
    ELSE 'cold'
END
WHERE trend_direction = 'stable' OR trend_direction IS NULL;

-- Verify the column was added
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'themes' AND column_name = 'trend_direction'
    ) THEN
        RAISE NOTICE '✅ trend_direction column added successfully to themes table';
    ELSE
        RAISE EXCEPTION '❌ Failed to add trend_direction column';
    END IF;
END $$;
