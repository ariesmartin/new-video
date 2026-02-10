-- Migration: Populate theme_elements for missing themes
-- 为主题缺失的元素库补充数据
-- 
-- This migration adds elements for themes that currently have 0 or few elements:
-- - medical_drama (医疗剧)
-- - sports (体育竞技)  
-- - food_culture (美食文化)
-- Plus additional elements for existing themes to enable cross-theme fusion

-- First, let's get the theme IDs (these need to exist in themes table)
-- Medical Drama 医疗职场
do $$
declare
    medical_theme_id uuid;
    sports_theme_id uuid;
    food_theme_id uuid;
begin
    -- Get theme IDs
    select id into medical_theme_id from themes where slug = 'medical_drama';
    select id into sports_theme_id from themes where slug = 'sports';
    select id into food_theme_id from themes where slug = 'food_culture';

    -- Insert Medical Drama elements (医疗职场)
    if medical_theme_id is not null then
        insert into theme_elements (theme_id, element_type, name, name_en, description, effectiveness_score, weight, usage_guidance, emotional_impact) values
        (medical_theme_id, 'character', '天才医生', 'Genius Doctor', '拥有超常医术的主角，能解决疑难杂症', 90, 1.0, '{"best_timing": "第1-3集展示医术", "preparation": "通过疑难病例建立权威", "execution_tips": "使用专业术语增加真实感"}'::jsonb, '{"satisfaction": 95, "surprise": 80, "replay_value": 85}'::jsonb),
        (medical_theme_id, 'character', '实习医生成长', 'Intern Growth', '从菜鸟到专家的蜕变历程', 88, 0.9, '{"best_timing": "贯穿全剧", "preparation": "初期展现生涩与错误", "execution_tips": "关键手术作为成长转折点"}'::jsonb, '{"satisfaction": 90, "surprise": 70, "replay_value": 88}'::jsonb),
        (medical_theme_id, 'character', '院长权力斗争', 'Hospital Politics', '医院管理层间的明争暗斗', 85, 0.85, '{"best_timing": "中期展开", "preparation": "铺垫医院内部矛盾", "execution_tips": "与医疗案例结合"}'::jsonb, '{"satisfaction": 85, "surprise": 85, "replay_value": 80}'::jsonb),
        (medical_theme_id, 'plot', '医疗事故调查', 'Medical Malpractice', '揭露医疗事故背后的真相', 92, 1.0, '{"best_timing": "第10-15集", "preparation": "前期埋下事故伏笔", "execution_tips": "多重反转，谁是真凶"}'::jsonb, '{"satisfaction": 95, "surprise": 90, "replay_value": 88}'::jsonb),
        (medical_theme_id, 'plot', '罕见病攻克', 'Rare Disease Cure', '团队协作攻克医学难题', 89, 0.95, '{"best_timing": "高潮阶段", "preparation": "详细描述病症严重性", "execution_tips": "情感与专业并重"}'::jsonb, '{"satisfaction": 92, "surprise": 85, "replay_value": 90}'::jsonb),
        (medical_theme_id, 'plot', '医患纠纷', 'Doctor-Patient Conflict', '医患关系中的冲突与和解', 86, 0.85, '{"best_timing": "中后段", "preparation": "建立患者背景故事", "execution_tips": "双方立场都要合理化"}'::jsonb, '{"satisfaction": 85, "surprise": 75, "replay_value": 82}'::jsonb),
        (medical_theme_id, 'plot', '紧急救援', 'Emergency Rescue', '急诊室争分夺秒抢救生命', 91, 0.95, '{"best_timing": "每集开场", "preparation": "快速建立紧迫感", "execution_tips": "快节奏剪辑感"}'::jsonb, '{"satisfaction": 95, "surprise": 88, "replay_value": 85}'::jsonb),
        (medical_theme_id, 'trope', '鬼才手术', 'Miracle Surgery', '看似不可能的手术成功', 88, 0.9, '{"best_timing": "季终高潮", "preparation": "多次手术失败铺垫", "execution_tips": "详细手术过程描写"}'::jsonb, '{"satisfaction": 92, "surprise": 80, "replay_value": 88}'::jsonb),
        (medical_theme_id, 'trope', '医闹反转', 'Medical Dispute Twist', '医闹事件真相大白', 84, 0.8, '{"best_timing": "中后段", "preparation": "前期呈现片面信息", "execution_tips": "真相揭露要有冲击力"}'::jsonb, '{"satisfaction": 88, "surprise": 90, "replay_value": 85}'::jsonb);
    end if;

    -- Insert Sports elements (体育竞技)
    if sports_theme_id is not null then
        insert into theme_elements (theme_id, element_type, name, name_en, description, effectiveness_score, weight, usage_guidance, emotional_impact) values
        (sports_theme_id, 'character', '天才运动员', 'Sports Prodigy', '拥有天赋但性格缺陷的主角', 89, 0.95, '{"best_timing": "开场即展示天赋", "preparation": "通过比赛展现特长", "execution_tips": "缺陷与天赋形成反差"}'::jsonb, '{"satisfaction": 90, "surprise": 80, "replay_value": 85}'::jsonb),
        (sports_theme_id, 'character', '严厉教练', 'Strict Coach', '外冷内热的恩师形象', 88, 0.9, '{"best_timing": "第3-5集", "preparation": "初期展现严厉", "execution_tips": "私下关心揭示温情"}'::jsonb, '{"satisfaction": 88, "surprise": 75, "replay_value": 86}'::jsonb),
        (sports_theme_id, 'character', '宿敌对手', 'Rival Opponent', '亦敌亦友的竞争关系', 87, 0.85, '{"best_timing": "贯穿全剧", "preparation": "从误会到理解", "execution_tips": "相互促进成长"}'::jsonb, '{"satisfaction": 85, "surprise": 78, "replay_value": 88}'::jsonb),
        (sports_theme_id, 'plot', '逆袭夺冠', 'Underdog Victory', '从弱队到冠军的热血历程', 93, 1.0, '{"best_timing": "季终高潮", "preparation": "多次失败积累", "execution_tips": "决赛要跌宕起伏"}'::jsonb, '{"satisfaction": 98, "surprise": 85, "replay_value": 95}'::jsonb),
        (sports_theme_id, 'plot', '伤病复出', 'Comeback from Injury', '克服伤病重返巅峰', 91, 0.95, '{"best_timing": "中期转折", "preparation": "详细描写伤病痛苦", "execution_tips": "复出之战要震撼"}'::jsonb, '{"satisfaction": 95, "surprise": 82, "replay_value": 92}'::jsonb),
        (sports_theme_id, 'plot', '团队磨合', 'Team Building', '从一盘散沙到团结一心', 86, 0.85, '{"best_timing": "前中期", "preparation": "突出个人主义", "execution_tips": "关键事件促成团结"}'::jsonb, '{"satisfaction": 88, "surprise": 70, "replay_value": 85}'::jsonb),
        (sports_theme_id, 'plot', '关键一球', 'Clutch Moment', '决定胜负的关键时刻', 90, 0.9, '{"best_timing": "每场重要比赛", "preparation": "营造紧张氛围", "execution_tips": "慢动作式细节描写"}'::jsonb, '{"satisfaction": 95, "surprise": 88, "replay_value": 90}'::jsonb),
        (sports_theme_id, 'trope', '黑马崛起', 'Dark Horse Rise', '不被看好却一鸣惊人', 89, 0.9, '{"best_timing": "中期爆发", "preparation": "长期铺垫被轻视", "execution_tips": "胜利要酣畅淋漓"}'::jsonb, '{"satisfaction": 92, "surprise": 85, "replay_value": 88}'::jsonb),
        (sports_theme_id, 'trope', '绝杀时刻', 'Buzzer Beater', '最后一秒的绝地反击', 92, 0.95, '{"best_timing": "决赛/关键赛", "preparation": "大比分落后", "execution_tips": "时间紧迫感"}'::jsonb, '{"satisfaction": 96, "surprise": 90, "replay_value": 93}'::jsonb);
    end if;

    -- Insert Food Culture elements (美食文化)
    if food_theme_id is not null then
        insert into theme_elements (theme_id, element_type, name, name_en, description, effectiveness_score, weight, usage_guidance, emotional_impact) values
        (food_theme_id, 'character', '天才厨师', 'Genius Chef', '拥有非凡味觉和创造力', 88, 0.9, '{"best_timing": "开场展示技艺", "preparation": "通过一道菜展现天赋", "execution_tips": "细节描写烹饪过程"}'::jsonb, '{"satisfaction": 90, "surprise": 82, "replay_value": 85}'::jsonb),
        (food_theme_id, 'character', '落魄大厨', 'Fallen Chef', '曾辉煌后落魄，重新崛起', 89, 0.95, '{"best_timing": "开场即低谷", "preparation": "闪回往日荣光", "execution_tips": "复兴过程要励志"}'::jsonb, '{"satisfaction": 92, "surprise": 80, "replay_value": 88}'::jsonb),
        (food_theme_id, 'character', '美食评论家', 'Food Critic', '毒舌但专业的评论家', 85, 0.85, '{"best_timing": "中期出现", "preparation": "前期传闻铺垫", "execution_tips": "严格但公正"}'::jsonb, '{"satisfaction": 86, "surprise": 78, "replay_value": 84}'::jsonb),
        (food_theme_id, 'plot', '厨神大赛', 'Cooking Competition', '厨艺比拼的激烈对决', 91, 0.95, '{"best_timing": "全剧主线", "preparation": "各轮比赛递进难度", "execution_tips": "每轮有创新菜品"}'::jsonb, '{"satisfaction": 94, "surprise": 88, "replay_value": 90}'::jsonb),
        (food_theme_id, 'plot', '失传菜谱', 'Lost Recipe', '寻找失传已久的美食秘方', 90, 0.9, '{"best_timing": "中期任务", "preparation": "传说故事铺垫", "execution_tips": "寻找过程要有趣"}'::jsonb, '{"satisfaction": 92, "surprise": 85, "replay_value": 88}'::jsonb),
        (food_theme_id, 'plot', '餐厅经营', 'Restaurant Management', '从路边摊到米其林', 87, 0.85, '{"best_timing": "副线展开", "preparation": "经营困难展现", "execution_tips": "顾客故事感人"}'::jsonb, '{"satisfaction": 88, "surprise": 75, "replay_value": 86}'::jsonb),
        (food_theme_id, 'plot', '美食治愈', 'Food Healing', '用美食治愈人心创伤', 88, 0.9, '{"best_timing": "情感段落", "preparation": "角色背景故事", "execution_tips": "食物与情感呼应"}'::jsonb, '{"satisfaction": 92, "surprise": 78, "replay_value": 90}'::jsonb),
        (food_theme_id, 'trope', '创新菜式', 'Innovative Dish', '传统与创新的碰撞', 86, 0.85, '{"best_timing": "比赛关键轮", "preparation": "前期保守传统", "execution_tips": "创新要有合理性"}'::jsonb, '{"satisfaction": 88, "surprise": 85, "replay_value": 85}'::jsonb),
        (food_theme_id, 'trope', '神秘食材', 'Mystery Ingredient', '稀有食材带来的转机', 85, 0.8, '{"best_timing": "关键时刻", "preparation": "食材传说铺垫", "execution_tips": "不能过于玄幻"}'::jsonb, '{"satisfaction": 87, "surprise": 88, "replay_value": 84}'::jsonb);
    end if;
end $$;

-- Now add cross-theme fusion elements to enable theme mixing
-- These are elements that work across multiple themes

-- Cross-theme elements for revenge (复仇可结合职场、医疗等)
do $$
declare
    revenge_id uuid;
    romance_id uuid;
    business_id uuid;
    cyberpunk_id uuid;
begin
    select id into revenge_id from themes where slug = 'revenge';
    select id into romance_id from themes where slug = 'romance';
    select id into business_id from themes where slug = 'business_war';
    select id into cyberpunk_id from themes where slug = 'cyberpunk';

    -- Additional revenge elements that fuse with other genres
    if revenge_id is not null then
        insert into theme_elements (theme_id, element_type, name, name_en, description, effectiveness_score, weight, usage_guidance, emotional_impact) values
        (revenge_id, 'character', '职场复仇', 'Workplace Revenge', '职场中的复仇与反击', 88, 0.9, '{"best_timing": "中期展开", "preparation": "职场欺压铺垫", "execution_tips": "专业能力碾压"}'::jsonb, '{"satisfaction": 90, "surprise": 82, "replay_value": 86}'::jsonb),
        (revenge_id, 'plot', '商业复仇', 'Business Revenge', '商业战场上的复仇布局', 89, 0.9, '{"best_timing": "中后期", "preparation": "商业利益冲突", "execution_tips": "商业手段要专业"}'::jsonb, '{"satisfaction": 91, "surprise": 85, "replay_value": 88}'::jsonb)
        on conflict do nothing;
    end if;

    -- Romance elements for cross-fusion
    if romance_id is not null then
        insert into theme_elements (theme_id, element_type, name, name_en, description, effectiveness_score, weight, usage_guidance, emotional_impact) values
        (romance_id, 'plot', '职场恋爱', 'Workplace Romance', '职场中的甜蜜爱情', 87, 0.88, '{"best_timing": "中前期", "preparation": "日常工作互动", "execution_tips": "避免办公室政治干扰"}'::jsonb, '{"satisfaction": 88, "surprise": 75, "replay_value": 86}'::jsonb),
        (romance_id, 'plot', '破镜重圆', 'Reconciliation', '分手后重新在一起', 90, 0.95, '{"best_timing": "后期", "preparation": "分手原因要深刻", "execution_tips": "和解要水到渠成"}'::jsonb, '{"satisfaction": 92, "surprise": 80, "replay_value": 90}'::jsonb)
        on conflict do nothing;
    end if;

    -- Cyberpunk elements
    if cyberpunk_id is not null then
        insert into theme_elements (theme_id, element_type, name, name_en, description, effectiveness_score, weight, usage_guidance, emotional_impact) values
        (cyberpunk_id, 'character', '赛博侦探', 'Cyber Detective', '高科技时代的侦探', 89, 0.92, '{"best_timing": "开场", "preparation": "案件引入", "execution_tips": "科技与人性结合"}'::jsonb, '{"satisfaction": 91, "surprise": 88, "replay_value": 89}'::jsonb),
        (cyberpunk_id, 'plot', '意识上传', 'Consciousness Upload', '人类意识数字化', 91, 0.95, '{"best_timing": "中期高潮", "preparation": "科技伦理铺垫", "execution_tips": "哲学思考要深"}'::jsonb, '{"satisfaction": 93, "surprise": 90, "replay_value": 91}'::jsonb),
        (cyberpunk_id, 'plot', '虚拟逃脱', 'Virtual Escape', '从虚拟世界逃离', 88, 0.9, '{"best_timing": "后期", "preparation": "虚拟世界沉浸", "execution_tips": "真假难辨"}'::jsonb, '{"satisfaction": 90, "surprise": 92, "replay_value": 88}'::jsonb)
        on conflict do nothing;
    end if;

    -- Business war elements
    if business_id is not null then
        insert into theme_elements (theme_id, element_type, name, name_en, description, effectiveness_score, weight, usage_guidance, emotional_impact) values
        (business_id, 'character', '商业间谍', 'Corporate Spy', '潜入对手公司的间谍', 87, 0.88, '{"best_timing": "中期", "preparation": "身份伪装", "execution_tips": "双重身份压力"}'::jsonb, '{"satisfaction": 89, "surprise": 88, "replay_value": 87}'::jsonb),
        (business_id, 'plot', '并购攻防', 'M&A Battle', '公司收购与反收购大战', 90, 0.93, '{"best_timing": "中后期", "preparation": "股价波动", "execution_tips": "商战要专业真实"}'::jsonb, '{"satisfaction": 91, "surprise": 85, "replay_value": 89}'::jsonb)
        on conflict do nothing;
    end if;
end $$;

-- Create index for efficient fusion queries
CREATE INDEX IF NOT EXISTS idx_theme_elements_cross_fusion 
ON theme_elements(element_type, effectiveness_score DESC) 
WHERE is_active = true;

-- Verify insertion
SELECT 
    t.slug as theme_slug,
    t.name as theme_name,
    COUNT(e.id) as element_count,
    AVG(e.effectiveness_score) as avg_score
FROM themes t
LEFT JOIN theme_elements e ON t.id = e.theme_id
WHERE t.slug IN ('medical_drama', 'sports', 'food_culture', 'cyberpunk', 'business_war', 'revenge', 'romance')
GROUP BY t.slug, t.name
ORDER BY element_count DESC;
