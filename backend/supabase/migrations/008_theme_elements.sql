-- Migration: Create theme_elements table for fine-grained tropes
-- 创建细粒度元素表，建立主题与元素的关联

-- 创建元素表
CREATE TABLE IF NOT EXISTS theme_elements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    theme_slug TEXT NOT NULL REFERENCES themes(slug) ON DELETE CASCADE,
    element_name TEXT NOT NULL,           -- 元素名称，如："身份错位"
    element_type TEXT NOT NULL,           -- 元素类型：人设/情节/背景/设定
    description TEXT,                     -- 元素描述
    market_score FLOAT DEFAULT 0,         -- 市场热度分 (0-100)
    overused BOOLEAN DEFAULT FALSE,       -- 是否已过度使用
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_theme_elements_slug ON theme_elements(theme_slug);
CREATE INDEX IF NOT EXISTS idx_theme_elements_type ON theme_elements(element_type);
CREATE INDEX IF NOT EXISTS idx_theme_elements_overused ON theme_elements(overused) WHERE overused = TRUE;
CREATE INDEX IF NOT EXISTS idx_theme_elements_score ON theme_elements(market_score DESC);

-- 添加更新时间触发器
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS update_theme_elements_updated_at ON theme_elements;
CREATE TRIGGER update_theme_elements_updated_at
    BEFORE UPDATE ON theme_elements
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- 添加注释
COMMENT ON TABLE theme_elements IS '主题细粒度元素表，存储每个主题下的具体元素（人设、情节、设定等）';
COMMENT ON COLUMN theme_elements.theme_slug IS '关联的主题slug';
COMMENT ON COLUMN theme_elements.element_name IS '元素名称，如：身份错位、双重人格等';
COMMENT ON COLUMN theme_elements.element_type IS '元素类型：人设(character)/情节(plot)/背景(setting)/设定(mechanic)';
COMMENT ON COLUMN theme_elements.market_score IS '市场热度分数，0-100';
COMMENT ON COLUMN theme_elements.overused IS '是否已被过度使用，如果为true则在推荐时降低权重';

-- 插入复仇逆袭主题的元素
INSERT INTO theme_elements (theme_slug, element_name, element_type, description, market_score, overused) VALUES
('revenge', '身份错位', '人设', '主角身份与表面不符，后期揭晓产生爽感', 95, FALSE),
('revenge', '隐藏大佬', '人设', '表面普通实则实力超群，关键时刻掉马', 92, FALSE),
('revenge', '反派洗白', '情节', '反派角色经历转变获得救赎', 85, FALSE),
('revenge', '双重人格', '人设', '角色具有多重人格，增加戏剧冲突', 78, FALSE),
('revenge', '金手指', '设定', '主角拥有特殊能力或资源助力复仇', 88, FALSE),
('revenge', '打脸', '情节', '反派挑衅后被主角强势反击', 90, TRUE),
('revenge', '身世之谜', '情节', '主角真实身份逐步揭晓', 82, FALSE);

-- 插入甜宠恋爱主题的元素
INSERT INTO theme_elements (theme_slug, element_name, element_type, description, market_score, overused) VALUES
('romance', '替身文学', '情节', '替身与白月光的情感纠葛', 75, TRUE),
('romance', '久别重逢', '情节', '曾经的情侣多年后再次相遇', 88, FALSE),
('romance', '先婚后爱', '情节', '先结婚后恋爱的情感发展', 90, FALSE),
('romance', '契约关系', '情节', '基于契约开始的虚假关系变真情', 82, FALSE),
('romance', '暗恋成真', '情节', '单向暗恋最终得到回应', 85, FALSE),
('romance', '霸总追妻', '情节', '霸道总裁追求女主', 70, TRUE),
('romance', '青梅竹马', '人设', '从小一起长大的情感基础', 80, FALSE);

-- 插入穿越重生主题的元素
INSERT INTO theme_elements (theme_slug, element_name, element_type, description, market_score, overused) VALUES
('transmigration', '系统流', '设定', '主角绑定系统获得任务和奖励', 88, FALSE),
('transmigration', '金手指', '设定', '穿越后拥有的特殊优势', 90, FALSE),
('transmigration', '预知未来', '设定', '重生者知道未来发展', 85, TRUE),
('transmigration', '穿书', '设定', '穿越到书中世界', 82, FALSE),
('transmigration', '马甲', '人设', '多重身份切换', 86, FALSE),
('transmigration', '逆袭', '情节', '从弱势地位逐步崛起', 92, FALSE),
('transmigration', '修仙', '背景', '修仙世界背景', 78, FALSE);

-- 插入悬疑推理主题的元素
INSERT INTO theme_elements (theme_slug, element_name, element_type, description, market_score, overused) VALUES
('suspense', '时间循环', '设定', '同一天不断重复寻找真相', 88, FALSE),
('suspense', '密室逃脱', '情节', '被困密闭空间解密求生', 82, FALSE),
('suspense', '多重反转', '情节', '剧情多次出人意料的转折', 90, FALSE),
('suspense', '烧脑推理', '情节', '需要观众一起思考的复杂案件', 85, FALSE),
('suspense', '心理博弈', '情节', '角色间的心理较量', 80, FALSE);

-- 插入无限流主题的元素
INSERT INTO theme_elements (theme_slug, element_name, element_type, description, market_score, overused) VALUES
('infinite_flow', '副本求生', '情节', '在不同副本中完成任务求生', 92, FALSE),
('infinite_flow', '团队协作', '人设', '团队成员各司其职配合闯关', 85, FALSE),
('infinite_flow', '智斗', '情节', '依靠智慧而非蛮力过关', 88, FALSE),
('infinite_flow', '规则怪谈', '设定', '副本中存在诡异规则', 86, FALSE),
('infinite_flow', '成长流', '情节', '主角在副本中不断变强', 84, FALSE);

-- 插入赛博朋克主题的元素
INSERT INTO theme_elements (theme_slug, element_name, element_type, description, market_score, overused) VALUES
('cyberpunk', 'AI觉醒', '设定', '人工智能产生自我意识', 88, FALSE),
('cyberpunk', '义体改造', '设定', '人体机械化改造', 82, FALSE),
('cyberpunk', '黑客攻防', '情节', '网络空间的攻防战', 85, FALSE),
('cyberpunk', '企业阴谋', '情节', '大公司背后的黑暗秘密', 86, FALSE),
('cyberpunk', '反乌托邦', '背景', '高科技低生活的压抑世界', 80, FALSE);

-- 插入职场商战主题的元素
INSERT INTO theme_elements (theme_slug, element_name, element_type, description, market_score, overused) VALUES
('business_war', '权谋斗争', '情节', '职场中的权力博弈', 88, FALSE),
('business_war', '商业并购', '情节', '企业收购与反收购', 85, FALSE),
('business_war', '创业逆袭', '情节', '从零开始创业成功', 90, FALSE),
('business_war', '卧底潜伏', '情节', '隐藏身份进入对手公司', 82, FALSE),
('business_war', '谈判博弈', '情节', '商业谈判中的智慧较量', 84, FALSE);

-- 插入规则怪谈主题的元素
INSERT INTO theme_elements (theme_slug, element_name, element_type, description, market_score, overused) VALUES
('rules_horror', '诡异规则', '设定', '必须遵守的奇怪规则', 92, FALSE),
('rules_horror', '恐怖解谜', '情节', '在恐怖环境中寻找线索', 88, FALSE),
('rules_horror', '逻辑悖论', '设定', '规则间的矛盾与破解', 86, FALSE),
('rules_horror', 'san值', '设定', '精神值设定增加恐怖感', 80, FALSE);

-- 插入末世求生主题的元素
INSERT INTO theme_elements (theme_slug, element_name, element_type, description, market_score, overused) VALUES
('apocalypse', '丧尸围城', '背景', '丧尸末世的生存挑战', 88, FALSE),
('apocalypse', '资源争夺', '情节', '稀缺资源的争夺与分配', 85, FALSE),
('apocalypse', '基地建设', '情节', '建立幸存者基地', 82, FALSE),
('apocalypse', '人性考验', '情节', '极端环境下的人性选择', 90, FALSE);

-- 插入家庭伦理主题的元素
INSERT INTO theme_elements (theme_slug, element_name, element_type, description, market_score, overused) VALUES
('family_urban', '代际冲突', '情节', '不同年代观念的碰撞', 85, FALSE),
('family_urban', '婆媳关系', '情节', '传统的婆媳矛盾与和解', 78, TRUE),
('family_urban', '女性觉醒', '人设', '女性自我意识的觉醒', 90, FALSE),
('family_urban', '职场妈妈', '人设', '事业与家庭的平衡', 86, FALSE);

-- 验证数据
SELECT 
    t.name as theme_name,
    COUNT(e.id) as element_count,
    AVG(e.market_score) as avg_score
FROM themes t
LEFT JOIN theme_elements e ON t.slug = e.theme_slug
GROUP BY t.name
ORDER BY element_count DESC;
