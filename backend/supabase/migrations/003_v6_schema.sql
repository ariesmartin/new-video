-- =====================================================
-- Migration: 003_v6_schema.sql
-- Description: v6.0 画布架构重构 - 新增 episodes, shot_nodes, shot_connections, scenes 表
-- Author: AI Video Engine Team
-- Date: 2026-02-03
-- =====================================================

-- =====================================================
-- 表: episodes
-- 说明: 剧集管理，每集独立画布
-- 对应: Product-Spec.md Section 1.2.1
-- =====================================================

CREATE TABLE IF NOT EXISTS episodes (
    episode_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    
    -- 基本信息
    episode_number INT NOT NULL,           -- 集数 (Ep.01)
    title VARCHAR(100) NOT NULL,           -- 剧集标题
    summary TEXT,                          -- 剧情摘要
    
    -- 剧本内容 (原 Module B 产物)
    script_text TEXT,                      -- 剧本正文
    script_scenes JSONB DEFAULT '[]'::jsonb,  -- 场景列表结构化数据
    
    -- 小说内容 (原 Module A 产物)
    novel_content TEXT,                    -- 小说章节内容
    word_count INT DEFAULT 0,              -- 字数统计
    
    -- 状态管理
    status VARCHAR(20) DEFAULT 'draft'     -- draft/writing/editing/completed
        CHECK (status IN ('draft', 'writing', 'editing', 'completed')),
    
    -- 画布状态 (v6.0: 每集独立画布)
    canvas_data JSONB DEFAULT '{}'::jsonb,  -- 画布完整状态
    /*
    canvas_data 结构:
    {
      "viewport": { "x": 0, "y": 0, "zoom": 1 },
      "nodes": [...],      -- ShotNode 数组
      "connections": [...] -- Connection 数组
    }
    */
    
    -- 关联分镜 (用于快速查询)
    storyboard_shot_count INT DEFAULT 0,   -- 分镜数量统计
    
    -- 时间戳
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_episodes_project_id ON episodes(project_id);
CREATE INDEX IF NOT EXISTS idx_episodes_episode_number ON episodes(project_id, episode_number);
CREATE INDEX IF NOT EXISTS idx_episodes_status ON episodes(status);

-- 注释
COMMENT ON TABLE episodes IS '剧集表 - v6.0 每集独立画布架构';
COMMENT ON COLUMN episodes.canvas_data IS '画布状态 JSONB: viewport + nodes + connections';


-- =====================================================
-- 表: scenes
-- 说明: 剧本场景管理
-- 对应: 25格 Scene Master 节点关联
-- =====================================================

CREATE TABLE IF NOT EXISTS scenes (
    scene_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    episode_id UUID NOT NULL REFERENCES episodes(episode_id) ON DELETE CASCADE,
    
    -- 场景信息
    scene_number VARCHAR(10) NOT NULL,     -- S01, S02...
    location VARCHAR(200) NOT NULL,        -- 场景头: "内景 - 陈默办公室 - 夜"
    description TEXT,                      -- 场景描述
    
    -- 场景 Master 节点关联
    master_node_id UUID,  -- 将在 shot_nodes 创建后添加外键
    
    -- 统计
    shot_count INT DEFAULT 0,              -- 该场景的分镜数量
    
    -- 时间戳
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_scenes_episode_id ON scenes(episode_id);

-- 注释
COMMENT ON TABLE scenes IS '场景表 - v6.0 场景管理';


-- =====================================================
-- 表: shot_nodes
-- 说明: v6.0 极简分镜节点
-- 对应: Frontend-Design-V3.md ShotNode 定义
-- =====================================================

CREATE TABLE IF NOT EXISTS shot_nodes (
    shot_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    episode_id UUID NOT NULL REFERENCES episodes(episode_id) ON DELETE CASCADE,
    scene_id UUID REFERENCES scenes(scene_id) ON DELETE SET NULL,
    
    -- 节点类型 (v6.0: 只有两种)
    node_type VARCHAR(20) NOT NULL         -- 'shot' | 'scene_master'
        CHECK (node_type IN ('shot', 'scene_master')),
    
    -- 显示信息 (极简)
    shot_number INT NOT NULL,              -- #01, #02...
    title VARCHAR(50) NOT NULL,            -- 景别: "俯视镜头"
    subtitle VARCHAR(100),                 -- 运镜: "旋转(Orbit)"
    
    -- 媒体资源
    thumbnail_url TEXT,                    -- 缩略图 URL (80x45px)
    image_url TEXT,                        -- 完整图片 URL
    
    -- 状态色标 (v6.0 定义)
    status VARCHAR(20) DEFAULT 'pending'   -- pending/processing/completed/approved/revision
        CHECK (status IN ('pending', 'processing', 'completed', 'approved', 'revision')),
    
    -- 画布位置
    position_x FLOAT NOT NULL DEFAULT 0,
    position_y FLOAT NOT NULL DEFAULT 0,
    
    -- 详细内容 (嵌套 JSONB)
    details JSONB DEFAULT '{}'::jsonb,
    /*
    details 结构:
    {
      "dialogue": "对白内容",
      "sound": "音效描述",
      "camera_move": "运镜方式",
      "prompt": "AI 生图提示词",
      "negative_prompt": "负面提示词",
      "resolution": "2K",
      "aspect_ratio": "9:16",
      "style": "影视写实",
      "reference_images": {
        "sketch": "url",
        "material": "url",
        "threeD": "url"
      },
      "generation_params": {
        "seed": 12345,
        "steps": 30,
        "cfg": 7.5
      }
    }
    */
    
    -- 时间戳
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_shot_nodes_episode_id ON shot_nodes(episode_id);
CREATE INDEX IF NOT EXISTS idx_shot_nodes_scene_id ON shot_nodes(scene_id);
CREATE INDEX IF NOT EXISTS idx_shot_nodes_node_type ON shot_nodes(node_type);
CREATE INDEX IF NOT EXISTS idx_shot_nodes_status ON shot_nodes(status);
CREATE INDEX IF NOT EXISTS idx_shot_nodes_position ON shot_nodes(position_x, position_y);

-- GIN 索引用于 details 查询
CREATE INDEX IF NOT EXISTS idx_shot_nodes_details ON shot_nodes USING GIN (details);

-- 注释
COMMENT ON TABLE shot_nodes IS 'v6.0 分镜节点表 - 极简 ShotNode 结构';


-- =====================================================
-- 添加 scenes 表的外键（在 shot_nodes 创建后）
-- =====================================================

-- 添加 master_node_id 外键
ALTER TABLE scenes 
DROP CONSTRAINT IF EXISTS scenes_master_node_id_fkey,
ADD CONSTRAINT scenes_master_node_id_fkey 
FOREIGN KEY (master_node_id) REFERENCES shot_nodes(shot_id) ON DELETE SET NULL;

-- 添加索引
CREATE INDEX IF NOT EXISTS idx_scenes_master_node ON scenes(master_node_id);


-- =====================================================
-- 表: shot_connections
-- 说明: v6.0 节点连线系统
-- 对应: Product-Spec.md Section 1.2.3
-- =====================================================

CREATE TABLE IF NOT EXISTS shot_connections (
    connection_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    episode_id UUID NOT NULL REFERENCES episodes(episode_id) ON DELETE CASCADE,
    
    -- 连线端点
    source_shot_id UUID NOT NULL REFERENCES shot_nodes(shot_id) ON DELETE CASCADE,
    target_shot_id UUID NOT NULL REFERENCES shot_nodes(shot_id) ON DELETE CASCADE,
    
    -- 连线类型 (v6.0 定义)
    connection_type VARCHAR(20) DEFAULT 'sequence'  -- 'sequence' | 'reference'
        CHECK (connection_type IN ('sequence', 'reference')),
    
    -- 创建时间
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_shot_connections_episode_id ON shot_connections(episode_id);
CREATE INDEX IF NOT EXISTS idx_shot_connections_source ON shot_connections(source_shot_id);
CREATE INDEX IF NOT EXISTS idx_shot_connections_target ON shot_connections(target_shot_id);

-- 唯一约束：避免重复连线
CREATE UNIQUE INDEX IF NOT EXISTS idx_shot_connections_unique 
ON shot_connections(source_shot_id, target_shot_id, connection_type);

-- 注释
COMMENT ON TABLE shot_connections IS 'v6.0 节点连线表 - sequence/reference 两种类型';


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

-- Episodes
DROP TRIGGER IF EXISTS update_episodes_updated_at ON episodes;
CREATE TRIGGER update_episodes_updated_at
    BEFORE UPDATE ON episodes
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Shot Nodes
DROP TRIGGER IF EXISTS update_shot_nodes_updated_at ON shot_nodes;
CREATE TRIGGER update_shot_nodes_updated_at
    BEFORE UPDATE ON shot_nodes
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Scenes
DROP TRIGGER IF EXISTS update_scenes_updated_at ON scenes;
CREATE TRIGGER update_scenes_updated_at
    BEFORE UPDATE ON scenes
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();


-- =====================================================
-- RLS 策略 (启用行级安全)
-- =====================================================

-- 注意: 需要在应用层处理权限控制
-- 这里仅启用 RLS，策略由应用层通过 API Key 控制

ALTER TABLE episodes ENABLE ROW LEVEL SECURITY;
ALTER TABLE shot_nodes ENABLE ROW LEVEL SECURITY;
ALTER TABLE scenes ENABLE ROW LEVEL SECURITY;
ALTER TABLE shot_connections ENABLE ROW LEVEL SECURITY;

-- 创建宽松策略（允许所有操作，由 API 层控制权限）
-- 实际项目中应根据需求调整为更严格的策略
CREATE POLICY episodes_all ON episodes FOR ALL USING (true);
CREATE POLICY shot_nodes_all ON shot_nodes FOR ALL USING (true);
CREATE POLICY scenes_all ON scenes FOR ALL USING (true);
CREATE POLICY shot_connections_all ON shot_connections FOR ALL USING (true);


-- =====================================================
-- 迁移完成
-- =====================================================

COMMENT ON TABLE episodes IS 'v6.0 剧集表 - 每集独立画布架构 (Migration 003)';
