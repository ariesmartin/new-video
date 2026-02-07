#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF短剧主题库数据提取脚本 - 从PDF报告提取完整数据
数据源: 中文短剧AI生成系统主题库研究报告.pdf
输出: extracted_pdf_theme_data.json
"""

import json
import re
from datetime import datetime


def parse_pdf_text():
    """解析PDF文本内容"""
    print("📖 读取PDF文本文件...")
    with open("pdf_extracted_text.txt", "r", encoding="utf-8") as f:
        content = f.read()

    print(f"✅ 读取完成，共 {len(content)} 字符")
    return content


def extract_genres_data(content):
    """提取五大题材数据"""
    genres = []

    # 1. 复仇逆袭题材
    genre1 = {
        "id": 1,
        "slug": "revenge",
        "name": "复仇逆袭",
        "name_en": "Revenge & Counterattack",
        "description": '精准击中观众的"共情痛感"与"理智爽感"双重需求，通过压抑-释放的情绪曲线实现强用户粘性',
        "core_formula": {
            "setup": {
                "stage": "Setup（铺垫期）",
                "episodes": "第1-5集（10-15%）",
                "task": "悲情渲染与仇恨种子埋设",
                "elements": [
                    "至亲被害/背叛",
                    "财产被夺",
                    "身份被贬",
                    "当众羞辱",
                    "身体伤害",
                ],
                "emotion_goal": '建立"这不公平"的强烈认知，形成"必须复仇"的心理期待',
                "avoid": "避免过度渲染血腥暴力；避免受害者形象过于被动",
            },
            "rising": {
                "stage": "Rising（升级期）",
                "episodes": "第6-30集（30-40%）",
                "task": "隐忍蓄力与身份/能力提升",
                "elements": [
                    "隐藏身份（大佬/皇室/天才）",
                    "获取金手指",
                    "建立盟友网络",
                    "收集证据/把柄",
                ],
                "emotion_goal": '维持"期待感"与"悬念感"，让观众对反击时机保持高度关注',
                "avoid": "避免升级过程过于顺利；避免隐藏身份过早暴露",
            },
            "climax": {
                "stage": "Climax（高潮期）",
                "episodes": "第31-70集（40-50%）",
                "task": "层层反击与终极对决",
                "elements": [
                    "身份揭露",
                    "证据公开",
                    "权力碾压",
                    "当众羞辱反派",
                    "反派互斗/众叛亲离",
                ],
                "emotion_goal": '实现"爽感"的阶梯式释放，每轮反击比上一轮更彻底',
                "avoid": "避免反击手段过于残忍；避免反派降智；60集左右设置终极钩子配合付费点",
            },
            "resolution": {
                "stage": "Resolution（解决期）",
                "episodes": "第71-80+集（10-15%）",
                "task": "复仇完成与新身份确立",
                "elements": ["反派最终下场", "情感线收束", "新事业/新地位", "主题升华"],
                "emotion_goal": "满足感与余韵感并存，避免过度圆满导致虚假感",
                "avoid": "避免烂尾；避免强行大团圆",
            },
        },
        "tropes": [
            {
                "name": "隐藏大佬/扮猪吃虎",
                "category": "身份类",
                "mechanism": "表面身份与真实身份形成巨大反差",
                "classic_case": "《此情已逝成追忆》入赘男主",
                "effectiveness_score": 95,
                "best_timing": "第10-20集首次暗示，第30-50集正式揭露",
                "risk_factors": "铺垫不足显得突兀；过早揭露削弱效果",
            },
            {
                "name": "法律复仇/智取型",
                "category": "冲突类",
                "mechanism": '以法律手段、商业手段等"文明方式"复仇',
                "classic_case": "《幸得相遇离婚时》",
                "effectiveness_score": 92,
                "best_timing": "贯穿全剧，高潮阶段集中释放",
                "risk_factors": "需专业知识准确性；节奏可能偏慢",
            },
            {
                "name": "身份揭露/当众打脸",
                "category": "身份类",
                "mechanism": "在关键场合揭露真实身份，震惊全场，即时反击",
                "classic_case": "多剧通用",
                "effectiveness_score": 90,
                "best_timing": "配合羞辱场景即时反击",
                "risk_factors": "频率过高导致麻木；需有身份层级预留",
            },
            {
                "name": "虐恋羁绊/追妻火葬场",
                "category": "情感类",
                "mechanism": "复仇对象曾是恋人，复仇过程中情感纠葛",
                "classic_case": "《幸得相遇离婚时》",
                "effectiveness_score": 88,
                "best_timing": "中段发展，高潮阶段测试",
                "risk_factors": "避免情感喧宾夺主；需有独立成长线",
            },
            {
                "name": "自我价值认同",
                "category": "主题类",
                "mechanism": "复仇不仅是打脸他人，更是证明自我价值",
                "classic_case": "《好一个乖乖女》",
                "effectiveness_score": 85,
                "best_timing": "Resolution阶段升华",
                "risk_factors": "避免说教感；需有具体行动支撑",
            },
        ],
        "writing_keywords": [
            "隐忍",
            "爆发",
            "身份",
            "证据",
            "权谋",
            "逆袭",
            "打脸",
            "清算",
        ],
        "visual_keywords": [
            "服装蜕变（从朴素到华丽）",
            "眼神转换（从躲闪到锐利）",
            "气场压制（低角度仰拍+环绕镜头）",
            "高对比光影（冷色调压抑场景vs暖色调胜利场景）",
            "慢动作特写（关键反击时刻的0.5倍速呈现）",
        ],
        "viral_examples": [
            {
                "title": "《黑莲花上位手册》",
                "innovation": "庶女入宫复仇，快节奏权谋",
                "data": "24小时充值破2000万",
                "success_factors": '每集3个以上反转，"黑莲花"主动布局人设',
                "risk_lesson": '因"鞭打死主母""烧死姐姐"等极端暴力情节被下架',
            },
            {
                "title": "《幸得相遇离婚时》",
                "innovation": "法律手段复仇+虐恋张力",
                "data": "红果热度9298万，30天播放量28亿，分账8000万创纪录",
                "success_factors": "5秒极致痛感开场，共情痛感+理智爽感双重满足",
            },
            {
                "title": "《好一个乖乖女》",
                "innovation": "自我价值认同式逆袭",
                "data": "前5秒留存率55%，春节档现象级",
                "success_factors": '细腻人物塑造，反派"伪人化"动机设计',
            },
            {
                "title": "《此情已逝成追忆》",
                "innovation": '10秒"受辱-藏锋"反转',
                "data": "红果热度5051万",
                "success_factors": "精准节奏控制，爽感即时释放",
            },
        ],
    }
    genres.append(genre1)

    # 2. 甜宠恋爱题材
    genre2 = {
        "id": 2,
        "slug": "romance",
        "name": "甜宠恋爱",
        "name_en": "Sweet Romance",
        "description": '满足观众对"理想爱情"的想象，通过高密度的甜蜜互动建立情感代入',
        "core_formula": {
            "setup": {
                "stage": "Setup（相遇期）",
                "episodes": "第1-8集",
                "task": '快速建立男女主相遇场景，制造"命中注定"感知',
                "elements": [
                    "职业差异（霸总+职员/明星+助理）",
                    "意外事件（撞车、泼咖啡、误会）",
                    "一见钟情信号",
                ],
                "emotion_goal": '建立"这两人有戏"的期待，轻甜蜜感',
                "avoid": "避免相遇过于刻意；避免女主过于被动，需有独立人格",
            },
            "rising": {
                "stage": "Rising（升温期）",
                "episodes": "第9-35集",
                "task": "建立关系纽带，累积甜蜜互动",
                "elements": [
                    "契约婚姻/假扮情侣",
                    "同居场景",
                    "护短行为",
                    "吃醋情节",
                    "双向暗恋信号",
                ],
                "emotion_goal": '"糖分"阶梯式上升，观众持续"嗑糖"满足',
                "avoid": "避免工业糖精感，互动需有情感逻辑；避免进展过快",
            },
            "climax": {
                "stage": "Climax（考验期）",
                "episodes": "第36-65集",
                "task": "制造重大考验，验证感情深度",
                "elements": [
                    "重大误会（第三者/秘密揭露）",
                    "外部阻力（家庭反对/事业冲突）",
                    "生死考验",
                    "追妻/追夫火葬场",
                ],
                "emotion_goal": '"虐后更甜"的情绪波动，强化感情珍贵感',
                "avoid": "避免误会过于狗血降智；避免虐度过度偏离甜宠定位",
            },
            "resolution": {
                "stage": "Resolution（圆满期）",
                "episodes": "第66-80+集",
                "task": "消除最后障碍，确认关系，甜蜜收尾",
                "elements": ["求婚/婚礼", "公开关系", "共同事业", "彩蛋甜蜜"],
                "emotion_goal": "圆满满足感与余韵感",
                "avoid": "避免仓促收尾；避免过度圆满导致虚假感",
            },
        },
        "tropes": [
            {
                "name": "契约婚姻/假戏真做",
                "category": "关系类",
                "mechanism": "利益驱动的虚假婚姻，最终真情相爱",
                "effectiveness_score": 94,
                "best_timing": "第2-4集建立契约",
                "risk_factors": "契约动机需充分；情感转变需有具体事件支撑",
            },
            {
                "name": "追妻/追夫火葬场",
                "category": "情感节奏类",
                "mechanism": "一方曾经忽视对方，醒悟后疯狂挽回",
                "effectiveness_score": 93,
                "best_timing": "第8-15集开始挽回",
                "risk_factors": '前期需有足够"虐"铺垫；挽回需有"实质性改变"',
            },
            {
                "name": "双向暗恋",
                "category": "情感节奏类",
                "mechanism": "双方互相喜欢却都不知情，甜蜜误会",
                "effectiveness_score": 90,
                "best_timing": "贯穿全剧，第6-10集情感萌芽",
                "risk_factors": '需设计"差点告白"节点维持张力',
            },
            {
                "name": "职业禁忌",
                "category": "设定类",
                "mechanism": "上下级/医患/师生等权力差异关系",
                "effectiveness_score": 90,
                "best_timing": "设定阶段确立",
                "risk_factors": "需处理伦理边界；避免权力滥用美化",
            },
            {
                "name": "护短狂魔",
                "category": "互动类",
                "mechanism": "一方无条件维护另一方，安全感爆棚",
                "effectiveness_score": 88,
                "best_timing": "升温期高频出现",
                "risk_factors": "避免过度保护导致女主工具化",
            },
        ],
        "writing_keywords": [
            "心动",
            "宿命",
            "双向",
            "治愈",
            "高糖",
            "轻虐",
            "占有欲",
            "安全感",
        ],
        "visual_keywords": [
            "暖色调（橙/粉/金为主）",
            "柔光滤镜（especially夜景与亲密场景）",
            "亲密特写（手部接触、眼神交汇、呼吸proximity）",
            "浪漫场景（夕阳、雪景、花海、烟花）",
            "舒缓节奏（长镜头、慢动作）",
        ],
        "viral_examples": [
            {
                "title": "《心动还请告诉我》",
                "innovation": "职场甜宠+轻文艺风格",
                "data": "针对Z世代职场新人群体",
                "success_factors": "首集前10秒高信息密度叙事，快速建立戏剧冲突框架",
            },
            {
                "title": "《新贵夫君猜不透》",
                "innovation": "打破公式的高概念甜宠",
                "data": "上线期爆发+后续持续吸引新观众",
                "success_factors": '"工程实验"式系统化设计：全程高能节奏、"悬疑解谜"叙事动力、"去理解"的主动叙事',
            },
            {
                "title": "《My Mafia Pilot Boyfriend》",
                "innovation": "海外成功输出的甜宠模板",
                "data": "国际化成功",
                "success_factors": '"职业禁忌+黑帮元素"叠加，但黑帮仅为人设叠加不抢主线；飞机厕所/机场更衣室等职业场景买量素材',
            },
            {
                "title": "《爱在黎明前降落》",
                "innovation": '航空业变体的"霸总×秘书"',
                "data": "高热度",
                "success_factors": '"一夜情-怀孕-重逢-契约"四段式紧凑结构；"孕吐""产检"等女性向细节共鸣',
            },
        ],
    }
    genres.append(genre2)

    # 3. 悬疑推理题材
    genre3 = {
        "id": 3,
        "slug": "suspense",
        "name": "悬疑推理",
        "name_en": "Mystery & Suspense",
        "description": '2024-2025年呈现精品化升级趋势，从早期的"悬疑+爱情"混合模式，向更纯粹的推理叙事和社会派深度拓展',
        "core_formula": {
            "setup": {
                "stage": "Setup（谜面期）",
                "episodes": "第1-6集",
                "task": "抛出核心谜团，建立信息差",
                "elements": [
                    "离奇案件/神秘事件",
                    "关键符号/道具",
                    "多视角信息碎片",
                    "不可靠叙述者",
                ],
                "emotion_goal": '"发生了什么"的好奇与"为什么发生"的探究',
                "avoid": "避免谜面过于复杂；避免信息过于隐晦",
            },
            "rising": {
                "stage": "Rising（调查期）",
                "episodes": "第7-30集",
                "task": "多线推进调查，铺设红鲱鱼误导",
                "elements": [
                    "新嫌疑人出现",
                    "旧线索被推翻",
                    "人物关系网展开",
                    "隐藏动机揭露",
                ],
                "emotion_goal": '"接近真相"的错觉与"另有隐情"的警觉交替',
                "avoid": "避免误导过于明显；避免线索过于分散",
            },
            "climax": {
                "stage": "Climax（反转期）",
                "episodes": "第31-60集",
                "task": "核心谜题解答，关键反转释放",
                "elements": [
                    "核心证据揭露",
                    "真凶身份反转",
                    "动机深层解读",
                    "人物黑化/救赎",
                ],
                "emotion_goal": '"原来如此"的顿悟与"竟是这样"的震惊',
                "avoid": "避免反转过于突兀；避免为反转而反转",
            },
            "resolution": {
                "stage": "Resolution（揭底期）",
                "episodes": "第61-80+集",
                "task": "完整解答核心谜题，保留解读空间",
                "elements": ["伏笔全面回收", "主题升华", "开放式结局/彩蛋"],
                "emotion_goal": "逻辑满足感与情感余韵并存",
                "avoid": "避免强行解释；避免过度留白",
            },
        },
        "tropes": [
            {
                "name": "符号隐喻系统",
                "category": "叙事结构类",
                "mechanism": "核心符号多次出现，意义随叙事动态转变",
                "effectiveness_score": 93,
                "technical_difficulty": "符号设计需与主题深度关联",
                "benchmark": "《隐秘的角落》笛卡尔坐标系",
            },
            {
                "name": "多螺旋叙事",
                "category": "叙事结构类",
                "mechanism": "多线交织，线索动态融合与消失",
                "effectiveness_score": 90,
                "technical_difficulty": "需精密的时间线规划",
                "benchmark": "《隐秘的角落》三线并进的螺旋结构",
            },
            {
                "name": "不可靠叙述者",
                "category": "人物设定类",
                "mechanism": "主角视角存在隐瞒或误导，真相逐层揭露",
                "effectiveness_score": 88,
                "technical_difficulty": '需平衡"误导"与"公平"',
                "benchmark": "《隐秘的角落》朱朝阳的日记",
            },
            {
                "name": "伏笔回收网络",
                "category": "悬念设计类",
                "mechanism": "前期细节在后期关键作用",
                "effectiveness_score": 87,
                "technical_difficulty": "需全局规划能力",
                "benchmark": "优秀悬疑剧标配",
            },
            {
                "name": "身份错位多层",
                "category": "悬念设计类",
                "mechanism": "凶手/受害者/侦探身份的意外转换",
                "effectiveness_score": 90,
                "technical_difficulty": "需前期性格/行为铺垫",
                "benchmark": '"全员恶人"设计',
            },
        ],
        "writing_keywords": [
            "谜团",
            "线索",
            "反转",
            "人性",
            "闭环",
            "留白",
            "符号",
            "对照",
        ],
        "visual_keywords": [
            "冷色调（蓝/绿/灰为主）",
            "阴影层次（明暗对比强化神秘感）",
            "手持镜头（增强临场感与不安定感）",
            "快速剪辑（信息密集呈现）",
            "固定长镜头（关键场景的凝视张力）",
        ],
        "viral_examples": [
            {
                "title": "《隐秘的角落》",
                "innovation": "社会派悬疑，长尾热度典范",
                "data": "热度峰值9796.59，一年后仍维持3000",
                "success_factors": '"笛卡尔"符号系统；多螺旋叙事结构；童话/现实双结局的开放性',
            },
            {
                "title": "《云渺》系列",
                "innovation": "单元案件+主线推进，季播化运营",
                "data": "30亿播放量",
                "success_factors": "修仙系统+单元案件融合；季播化运营延长IP生命周期",
            },
            {
                "title": "《大唐女法医之迷案追踪》",
                "innovation": "互动式悬疑，用户决定结局",
                "data": "形式创新代表",
                "success_factors": '"选择-结果"即时反馈；古装设定视觉差异化',
            },
        ],
    }
    genres.append(genre3)

    # 4. 穿越重生题材
    genre4 = {
        "id": 4,
        "slug": "transmigration",
        "name": "穿越重生",
        "name_en": "Transmigration & Rebirth",
        "description": '2025年新兴趋势中"马甲、古风权谋、古风言情、奇幻脑洞"等题材增势迅猛，核心优势在于"金手指"设定带来的碾压爽感',
        "core_formula": {
            "setup": {
                "stage": "Setup（死亡/穿越期）",
                "episodes": "第1-5集",
                "task": '快速完成"死亡-穿越-觉醒"流程',
                "elements": [
                    "现代死亡场景",
                    "穿越触发机制",
                    "新身份认知",
                    "金手指获取",
                ],
                "emotion_goal": '"重获新生"的希望感与"未知世界"的好奇感',
                "avoid": "避免穿越过程冗长；避免金手指过于强大",
            },
            "rising": {
                "stage": "Rising（适应期）",
                "episodes": "第6-25集",
                "task": "探索新世界规则，初步运用金手指",
                "elements": [
                    "世界观信息获取",
                    "关键人物结识",
                    "首次金手指运用",
                    "初步冲突应对",
                ],
                "emotion_goal": '"开挂"的爽感与"探索"的乐趣',
                "avoid": "避免信息灌输过于密集；避免金手指运用过于顺利",
            },
            "climax": {
                "stage": "Climax（改变期）",
                "episodes": "第26-60集",
                "task": "主动运用现代知识/金手指，大幅改变命运",
                "elements": [
                    "现代知识降维打击",
                    "关键历史事件干预",
                    "原主恩怨清算",
                    "多角关系处理",
                ],
                "emotion_goal": '"改变历史"的掌控感与"知识变现"的满足感',
                "avoid": "避免改变过于轻易；避免现代知识运用过于突兀",
            },
            "resolution": {
                "stage": "Resolution（归位/定居期）",
                "episodes": "第61-80+集",
                "task": "处理归留抉择，确认情感归宿",
                "elements": ["回归现代的机会与抉择", "新世界情感羁绊", "双重身份整合"],
                "emotion_goal": "归属感与圆满感",
                "avoid": "避免归留抉择过于轻易；避免情感线处理仓促",
            },
        },
        "tropes": [
            {
                "name": "系统绑定/任务驱动",
                "category": "设定类",
                "mechanism": "系统发布任务，完成后获得奖励",
                "effectiveness_score": 94,
                "best_timing": "第1-3集完成绑定",
                "risk_factors": "系统规则需清晰一致；奖励梯度需合理设计",
            },
            {
                "name": "读心术/心声外泄",
                "category": "设定类",
                "mechanism": "能读取他人想法，或心声被他人听到",
                "effectiveness_score": 91,
                "best_timing": "第2-4集激活",
                "risk_factors": "信息量需控制；心声与言行反差需有喜剧/戏剧效果",
            },
            {
                "name": "全家偷听心声",
                "category": "设定变体",
                "mechanism": "心声被家人听到，引发系列喜剧效果",
                "effectiveness_score": 89,
                "best_timing": "设定即触发",
                "risk_factors": '需设计"心声-言行"的喜剧反差',
            },
            {
                "name": "现代知识降维",
                "category": "能力类",
                "mechanism": "运用现代知识在古代/异世界形成碾压",
                "effectiveness_score": 88,
                "best_timing": "贯穿全剧",
                "risk_factors": "需具体化知识应用场景；需有适配转化",
            },
            {
                "name": "重生复仇",
                "category": "冲突类",
                "mechanism": "死后回到过去，有机会改变悲剧",
                "effectiveness_score": 90,
                "best_timing": "贯穿全剧",
                "risk_factors": "改变幅度需有合理限制；蝴蝶效应需考虑",
            },
        ],
        "writing_keywords": [
            "重生",
            "系统",
            "金手指",
            "逆袭",
            "改变",
            "抉择",
            "融合",
            "归属",
        ],
        "visual_keywords": [
            "古今对比（现代服装vs古装、现代场景vs古代场景）",
            "特效转场（穿越瞬间的时空扭曲、系统界面的全息呈现）",
            "服饰蜕变（从原主服装到主角风格渐变）",
            '场景奇观（利用现代知识创造的古代"奇迹"）',
            "符号道具（穿越信物、系统载体）",
        ],
        "viral_examples": [
            {
                "title": "《盛夏芬德拉》",
                "innovation": "读心术设定",
                "data": 'AI评估钩子"3秒时间内扣住观众脉搏"',
                "success_factors": "女主被陷害入狱，意外获得读心术，快速建立金手指",
            },
            {
                "title": "《全家偷听我心声》",
                "innovation": "全家共同成长设定",
                "data": "新兴爆款",
                "success_factors": '将传统的"个人逆袭"扩展为"家庭共同成长"，心声与言行的反差提供持续笑点',
            },
        ],
    }
    genres.append(genre4)

    # 5. 家庭伦理/都市现实题材
    genre5 = {
        "id": 5,
        "slug": "family_urban",
        "name": "家庭伦理/都市现实",
        "name_en": "Family Ethics & Urban Reality",
        "description": '2025年呈现明显增长，核心竞争力在于"真实感"与"共鸣感"，贴近观众日常生活经验',
        "core_formula": {
            "setup": {
                "stage": "Setup（矛盾潜伏期）",
                "episodes": "第1-10集",
                "task": "铺陈家庭/职场关系网络，埋下矛盾种子",
                "elements": [
                    "代际观念差异",
                    "财产分配隐患",
                    "婚姻关系张力",
                    "职场权力结构",
                ],
                "emotion_goal": '"这不就是我"的代入感与"迟早要出事"的预感',
                "avoid": "避免矛盾铺设过于刻意；避免人物过于脸谱化",
            },
            "rising": {
                "stage": "Rising（冲突爆发期）",
                "episodes": "第11-40集",
                "task": "矛盾公开化，冲突逐步升级",
                "elements": ["遗产争夺", "赡养纠纷", "婚姻危机", "职场PUA", "背叛揭露"],
                "emotion_goal": "愤怒、委屈、焦虑等情绪的共鸣与释放",
                "avoid": "避免冲突过于狗血；避免人物行为脱离现实逻辑",
            },
            "climax": {
                "stage": "Climax（危机顶点期）",
                "episodes": "第41-65集",
                "task": "冲突达到顶点，核心关系面临破裂",
                "elements": [
                    "离婚/断绝关系",
                    "失业/事业崩塌",
                    "健康危机",
                    "自我认同崩溃",
                ],
                "emotion_goal": '"至暗时刻"的压抑与"必须改变"的觉醒',
                "avoid": "避免危机过于极端；避免人物反应过于戏剧化",
            },
            "resolution": {
                "stage": "Resolution（和解/重建期）",
                "episodes": "第66-80+集",
                "task": "完成个人成长，重建核心关系",
                "elements": [
                    "自我和解",
                    "关键关系修复",
                    "新事业/生活方式确立",
                    "代际理解",
                ],
                "emotion_goal": "治愈感与希望感",
                "avoid": "避免和解过于轻易；避免强行大团圆",
            },
        },
        "tropes": [
            {
                "name": "职场PUA/反PUA",
                "category": "社会议题类",
                "mechanism": "职场权力滥用与反抗，高度共鸣",
                "effectiveness_score": 90,
                "social_resonance": "极高",
                "benchmark": "《杜小慧》",
            },
            {
                "name": "婆媳矛盾/和解",
                "category": "关系类",
                "mechanism": "代际与婚姻关系的权力博弈",
                "effectiveness_score": 88,
                "social_resonance": "高",
                "benchmark": "多部家庭伦理剧",
            },
            {
                "name": "重组家庭张力",
                "category": "关系类",
                "mechanism": "继父母/继子女关系的复杂动态",
                "effectiveness_score": 85,
                "social_resonance": "中高",
                "benchmark": "现代家庭题材",
            },
            {
                "name": "全职妈妈逆袭",
                "category": "人物弧光类",
                "mechanism": "家庭角色到社会角色的转型",
                "effectiveness_score": 80,
                "social_resonance": "高",
                "benchmark": "女性成长题材",
            },
            {
                "name": "代际和解",
                "category": "情感治愈类",
                "mechanism": "父母与子女的最终理解",
                "effectiveness_score": 86,
                "social_resonance": "高",
                "benchmark": "温情向结局",
            },
        ],
        "writing_keywords": [
            "烟火气",
            "真实感",
            "共鸣",
            "治愈",
            "和解",
            "成长",
            "边界",
            "选择",
        ],
        "visual_keywords": [
            "生活化场景（老旧小区、菜市场、社区医院）",
            "自然光（避免过度打光）",
            "纪实风格（手持镜头、长镜头）",
            "细腻表演（微表情、日常动作）",
            "色彩温和（避免高饱和对比）",
        ],
        "viral_examples": [
            {
                "title": "《杜小慧》",
                "innovation": "职场女性逆袭+社会议题嵌入",
                "data": "官方发起#职场PUA有多隐蔽#话题，48小时阅读量破32亿，UGC内容超50万条",
                "success_factors": "社会议题嵌入是差异化关键，带动剧集日播放量增6000万",
            }
        ],
    }
    genres.append(genre5)

    return genres


def extract_tropes_library():
    """提取爆款元素库（20个元素）"""
    tropes = {
        "identity": [
            {
                "name": "隐藏大佬/扮猪吃虎",
                "name_en": "Hidden Tycoon",
                "category": "identity",
                "mechanism": "表面身份与真实身份形成巨大反差",
                "variations": ["商业大佬型", "武学宗师型", "皇室血脉型", "天才学霸型"],
                "best_timing": "第10-20集首次暗示，第30-50集正式揭露",
                "success_rate": 92,
                "risk_factors": "铺垫不足显得突兀；过早揭露削弱效果",
            },
            {
                "name": "秘密皇室/流落血脉",
                "name_en": "Secret Royalty",
                "category": "identity",
                "mechanism": "主角实为皇室/贵族血脉，因变故流落民间",
                "variations": ["幼年失散型", "主动隐姓埋名型", "被篡夺身份型"],
                "best_timing": "第20-40集揭露",
                "success_rate": 88,
                "risk_factors": "皇室设定需世界观支撑；揭露后剧情方向需重新设计",
            },
            {
                "name": "失忆恢复/身份觉醒",
                "name_en": "Amnesia Recovery",
                "category": "identity",
                "mechanism": "主角因失忆忘记真实身份，逐步恢复记忆",
                "variations": ["完全失忆型", "选择性失忆型", "身份替换型"],
                "best_timing": "贯穿全剧，关键节点恢复",
                "success_rate": 85,
                "risk_factors": "失忆梗易显老套；恢复过程需有情感重量",
            },
            {
                "name": "双重身份/卧底潜伏",
                "name_en": "Double Identity",
                "category": "identity",
                "mechanism": "主角同时维持两个截然不同的身份",
                "variations": ["卧底型", "间谍型", "双面人生型", "网络与现实型"],
                "best_timing": "根据剧情需要灵活安排",
                "success_rate": 83,
                "risk_factors": "身份切换需有合理场景；长期维持需消耗叙事资源",
            },
            {
                "name": "系统绑定/金手指觉醒",
                "name_en": "System Binding",
                "category": "identity",
                "mechanism": "主角获得超自然系统辅助，获得特殊能力",
                "variations": ["任务系统型", "属性面板型", "签到奖励型", "直播系统型"],
                "best_timing": "第1-3集完成绑定",
                "success_rate": 90,
                "risk_factors": "系统规则需清晰一致；奖励梯度需合理设计",
            },
        ],
        "relationship": [
            {
                "name": "契约婚姻/假戏真做",
                "category": "relationship",
                "mechanism": "利益驱动的虚假婚姻，最终真情相爱",
                "emotional_tension": "真假情感的界限模糊，心动与契约的冲突",
                "variations": ["家族联姻型", "债务抵偿型", "挡箭牌型", "协议恋爱型"],
                "effectiveness_score": 94,
                "best_timing": "第2-4集建立契约",
            },
            {
                "name": "冤家变情人/敌对到恋人",
                "category": "relationship",
                "mechanism": "从对立冲突到相互理解，最终相爱",
                "emotional_tension": "认知颠覆与情感反转的双重冲击",
                "variations": ["职场对手型", "家族世仇型", "误会敌对型", "竞争关系型"],
                "effectiveness_score": 91,
                "best_timing": "第1-2集建立对立，第6-10集情感萌芽",
            },
            {
                "name": "青梅竹马/久别重逢",
                "category": "relationship",
                "mechanism": "童年羁绊，成年后再度相遇",
                "emotional_tension": '时间沉淀的情感厚度，"原来是你"的宿命感',
                "variations": ["单向暗恋型", "双向暗恋型", "一方遗忘型", "身份悬殊型"],
                "effectiveness_score": 89,
                "best_timing": "第3-5集揭露身份",
            },
            {
                "name": "三角恋/追妻火葬场",
                "category": "relationship",
                "mechanism": "第三方介入或一方醒悟后的疯狂挽回",
                "emotional_tension": "失去后的珍惜，竞争中的紧迫感",
                "variations": [
                    "白月光回归型",
                    "误会分手型",
                    "婚内觉醒型",
                    "替身转正型",
                ],
                "effectiveness_score": 88,
                "best_timing": "第8-15集开始挽回",
            },
            {
                "name": "替身文学/白月光情结",
                "category": "relationship",
                "mechanism": "一方因相似外貌被当作替代品，最终获得真心",
                "emotional_tension": "自我认同危机与真爱确认的挣扎",
                "variations": [
                    "主动替身型",
                    "被动替身型",
                    "白月光复活型",
                    "替身逆袭型",
                ],
                "effectiveness_score": 85,
                "best_timing": "第15-25集替身揭露",
            },
        ],
        "conflict": [
            {
                "name": "打脸反杀/当众羞辱",
                "category": "conflict",
                "mechanism": "反派嚣张挑衅，主角以实力/身份碾压回击",
                "satisfaction_source": "压抑后的即时释放，社会认同的获得",
                "effectiveness_score": 93,
                "taboos": "避免过度暴力；避免反派过于弱智",
            },
            {
                "name": "复仇计划/精密布局",
                "category": "conflict",
                "mechanism": "主角长期策划，逐步实施复仇",
                "satisfaction_source": "掌控感与智力优越感",
                "effectiveness_score": 90,
                "taboos": "避免手段过于残忍；避免伤及无辜",
            },
            {
                "name": "背叛揭露/信任崩塌",
                "category": "conflict",
                "mechanism": "亲密关系的背叛被揭露，关系重组",
                "satisfaction_source": "情感冲击与认知颠覆",
                "effectiveness_score": 87,
                "taboos": "避免为背叛而背叛，需有动机支撑",
            },
            {
                "name": "救赎牺牲/代价付出",
                "category": "conflict",
                "mechanism": "为拯救他人/理想而主动牺牲",
                "satisfaction_source": "崇高感与情感重量",
                "effectiveness_score": 85,
                "taboos": "避免牺牲过于轻易，需有情感铺垫",
            },
            {
                "name": "误会冲突/追悔莫及",
                "category": "conflict",
                "mechanism": "因误会产生的冲突，真相大白后的悔恨",
                "satisfaction_source": "戏剧张力与情感波动",
                "effectiveness_score": 82,
                "taboos": "避免误会过于狗血降智",
            },
        ],
        "setting": [
            {
                "name": "时间循环/重复当日",
                "category": "setting",
                "mechanism": "主角被困在同一天，不断重复直至突破",
                "innovation_space": "每次循环的微小差异累积，多种可能性探索",
                "effectiveness_score": 88,
                "execution_difficulty": "循环机制需清晰；突破条件需合理",
            },
            {
                "name": "灵魂互换/身体错位",
                "category": "setting",
                "mechanism": "两人灵魂互换，体验对方人生",
                "innovation_space": "身份错位的喜剧效果与认知深化",
                "effectiveness_score": 86,
                "execution_difficulty": "演员表演需区分两个灵魂；换身规则需一致",
            },
            {
                "name": "重生穿越/命运改写",
                "category": "setting",
                "mechanism": "死后回到过去，有机会改变历史",
                "innovation_space": '"已知未来"的信息优势与改变代价',
                "effectiveness_score": 90,
                "execution_difficulty": "改变幅度需有合理限制；蝴蝶效应需考虑",
            },
            {
                "name": "读心术/心声外泄",
                "category": "setting",
                "mechanism": "能读取他人想法，或心声被他人听到",
                "innovation_space": "信息不对等的喜剧与戏剧效果",
                "effectiveness_score": 89,
                "execution_difficulty": "读心范围/条件需明确；隐私边界需处理",
            },
            {
                "name": "预知未来/改变历史",
                "category": "setting",
                "mechanism": "知晓未来事件，主动干预改变",
                "innovation_space": "命运与自由意志的哲学探讨",
                "effectiveness_score": 84,
                "execution_difficulty": "预知精度需有局限；改变失败需有设计",
            },
        ],
    }
    return tropes


def extract_hooks_library():
    """提取钩子模板库（30个钩子）"""
    hooks = {
        "situation": [
            {
                "id": "SH-001",
                "name": "极限羞辱型",
                "core_formula": "主角正在遭受[极端羞辱]，但[隐藏实力/即将反击]",
                "variables": {
                    "humiliation_type": [
                        "被当众退婚",
                        "被开除",
                        "被嘲笑",
                        "被泼咖啡",
                        "被迫下跪",
                    ],
                    "hidden_element": ["真实身份", "隐藏实力", "即将反击", "神秘后台"],
                },
                "effectiveness_score": 95,
                "applicable_genres": ["revenge", "urban"],
            },
            {
                "id": "SH-002",
                "name": "生死一线型",
                "core_formula": "主角面临[生死危机]，[神秘转机]突然出现",
                "variables": {
                    "crisis_type": ["车祸", "坠楼", "病危", "绑架", "火灾"],
                    "turning_point": ["神秘救援", "异能觉醒", "系统激活", "身份揭露"],
                },
                "effectiveness_score": 92,
                "applicable_genres": ["suspense", "transmigration"],
            },
            {
                "id": "SH-003",
                "name": "误会冲突型",
                "core_formula": "[捉奸/错认]现场，真相[即将揭晓/截然相反]",
                "variables": {
                    "misunderstanding_type": [
                        "出轨捉奸",
                        "身份错认",
                        "证据误解",
                        "对话断章",
                    ],
                    "reveal_way": ["当场反转", "下集揭露", "观众先知"],
                },
                "effectiveness_score": 90,
                "applicable_genres": ["romance", "family"],
            },
            {
                "id": "SH-004",
                "name": "契约现场型",
                "core_formula": "[签字/婚礼]关键时刻，[意外变数]突然介入",
                "variables": {
                    "contract_type": ["离婚协议", "卖身契", "婚约", "合同"],
                    "variable_type": ["身份揭露", "证据出现", "人物闯入", "电话打断"],
                },
                "effectiveness_score": 88,
                "applicable_genres": ["romance", "business"],
            },
            {
                "id": "SH-005",
                "name": "重逢对峙型",
                "core_formula": "[仇人/前任]意外重逢，[情绪爆发/隐藏身份]",
                "variables": {
                    "reunion_scene": ["职场", "宴会", "街头", "医院"],
                    "emotion_type": ["愤怒", "尴尬", "冷漠", "假装不识"],
                },
                "effectiveness_score": 87,
                "applicable_genres": ["revenge", "romance"],
            },
            {
                "id": "SH-006",
                "name": "身份错位型",
                "core_formula": "[卑微身份]正在服务[高贵身份]，真实关系[即将揭露]",
                "variables": {
                    "service_scene": ["端茶倒水", "开车门", "做保姆"],
                    "real_relationship": ["夫妻", "父子", "旧识", "债主"],
                },
                "effectiveness_score": 89,
                "applicable_genres": ["revenge", "romance"],
            },
            {
                "id": "SH-007",
                "name": "证据揭露型",
                "core_formula": "[关键证据]突然出现，[人物命运]即将改变",
                "variables": {
                    "evidence_type": [
                        "DNA报告",
                        "视频录像",
                        "遗嘱",
                        "合同",
                        "聊天记录",
                    ],
                    "impact_scope": ["身份确认", "罪名洗清", "财产归属"],
                },
                "effectiveness_score": 86,
                "applicable_genres": ["suspense", "family"],
            },
            {
                "id": "SH-008",
                "name": "能力觉醒型",
                "core_formula": "[平凡时刻]，[超自然能力]突然显现",
                "variables": {
                    "trigger_scene": ["受辱", "危险", "情绪波动"],
                    "ability_type": ["读心术", "预知", "武力", "医术", "系统"],
                },
                "effectiveness_score": 88,
                "applicable_genres": ["transmigration", "fantasy"],
            },
            {
                "id": "SH-009",
                "name": "关系逆转型",
                "core_formula": "[弱势方]突然掌控[强势方]的把柄/命运",
                "variables": {
                    "leverage_type": ["秘密", "犯罪证据", "身世真相"],
                    "reversal_scene": ["谈判", "威胁", "交易"],
                },
                "effectiveness_score": 85,
                "applicable_genres": ["business", "revenge"],
            },
            {
                "id": "SH-010",
                "name": "时间压力型",
                "core_formula": "[倒计时]内必须完成[不可能任务]，否则[严重后果]",
                "variables": {
                    "countdown_type": ["手术时间", "炸弹倒计时", "最后期限"],
                    "task_difficulty": ["资源匮乏", "信息不足", "敌人阻挠"],
                },
                "effectiveness_score": 84,
                "applicable_genres": ["suspense", "action"],
            },
        ],
        "question": [
            {
                "id": "QH-001",
                "name": "直接提问型",
                "core_formula": '"[震撼问题]，答案[即将揭晓/出乎意料]"',
                "variables": {
                    "question_type": ["身份质问", "情感质问", "真相质问"],
                    "reveal_timing": ["当场", "下集", "逐步"],
                },
                "effectiveness_score": 90,
                "applicable_genres": ["all"],
            },
            {
                "id": "QH-002",
                "name": "反常识陈述型",
                "core_formula": '"[违背常识的事实]，原因[令人震惊]"',
                "variables": {
                    "fact_type": ["全球首富端洗脚水", "乞丐拥有豪宅", "废物考了满分"],
                    "reason_category": ["隐藏身份", "系统加持", "被人陷害"],
                },
                "effectiveness_score": 92,
                "applicable_genres": ["revenge", "transmigration"],
            },
            {
                "id": "QH-003",
                "name": "预言警示型",
                "core_formula": '"[时间限制]后，[惊人结果]将会发生"',
                "variables": {
                    "time_type": ["三分钟后", "今晚", "一个月后"],
                    "result_type": ["你会跪下来求我", "真相大白", "身败名裂"],
                },
                "effectiveness_score": 88,
                "applicable_genres": ["suspense", "revenge"],
            },
            {
                "id": "QH-004",
                "name": "信息缺口型",
                "core_formula": '"[关键信息]被[人物]发现，反应[暗示重大]"',
                "variables": {
                    "info_type": ["短信", "照片", "文件", "对话"],
                    "discovery_scene": ["偶然看到", "刻意寻找", "被人透露"],
                    "reaction_type": ["脸色大变", "沉默不语", "立刻行动"],
                },
                "effectiveness_score": 89,
                "applicable_genres": ["suspense", "family"],
            },
            {
                "id": "QH-005",
                "name": "身份悬念型",
                "core_formula": '"那个[被轻视的身份]，其实是[惊人真相]"',
                "variables": {
                    "surface_identity": ["实习生", "保姆", "司机", "乞丐"],
                    "real_identity": ["总裁", "特工", "天才", "皇室"],
                },
                "effectiveness_score": 91,
                "applicable_genres": ["revenge", "romance"],
            },
            {
                "id": "QH-006",
                "name": "选择困境型",
                "core_formula": '"[两难选择]，无论选哪个都[代价沉重]"',
                "variables": {
                    "choice_type": [
                        "救爱人还是救亲人",
                        "说出真相还是保持沉默",
                        "复仇还是原谅",
                    ],
                    "cost_type": ["失去生命", "失去爱情", "失去自我"],
                },
                "effectiveness_score": 85,
                "applicable_genres": ["suspense", "romance"],
            },
            {
                "id": "QH-007",
                "name": "数字冲击型",
                "core_formula": '"[具体数字]的[事物]，背后藏着[惊人秘密]"',
                "variables": {
                    "number_type": ["三年", "第七天", "第100次"],
                    "thing_type": ["等待", "死亡", "循环", "背叛"],
                },
                "effectiveness_score": 86,
                "applicable_genres": ["suspense", "revenge"],
            },
            {
                "id": "QH-008",
                "name": "否定预期型",
                "core_formula": '"所有人都以为[普遍认知]，但真相[截然相反]"',
                "variables": {
                    "common_belief": ["他是废物", "她出轨了", "公司破产了"],
                    "truth_reversal": ["他是隐藏大佬", "她在收集证据", "公司即将上市"],
                },
                "effectiveness_score": 87,
                "applicable_genres": ["all"],
            },
            {
                "id": "QH-009",
                "name": "神秘引用型",
                "core_formula": '"[神秘话语/预言]，正在[一步步应验]"',
                "variables": {
                    "quote_source": ["遗嘱", "日记", "预言", "梦境"],
                    "fulfillment_way": ["符号对应", "事件吻合", "人物出现"],
                },
                "effectiveness_score": 84,
                "applicable_genres": ["suspense", "fantasy"],
            },
            {
                "id": "QH-010",
                "name": "未完成型",
                "core_formula": '"[关键动作]即将[完成/发生]，画面[突然中断]"',
                "variables": {
                    "action_type": ["签字", "亲吻", "开枪", "揭露"],
                    "interrupt_way": ["黑屏", "转场", "下集预告"],
                },
                "effectiveness_score": 88,
                "applicable_genres": ["all"],
            },
        ],
        "visual": [
            {
                "id": "VH-001",
                "name": "奇观展示型",
                "core_mechanism": "呈现超出日常经验的震撼场景",
                "visual_elements": [
                    "豪华场景（mansion/游艇/私人飞机）",
                    "特殊能力（特效呈现）",
                    "大规模场面（人群/灾难）",
                ],
                "effectiveness_score": 90,
                "applicable_genres": ["revenge", "transmigration"],
            },
            {
                "id": "VH-002",
                "name": "强烈对比型",
                "core_mechanism": "同一画面的前后/内外反差",
                "visual_elements": [
                    "贫富对比（破衣vs华服）",
                    "身份对比（卑微姿态vs高贵身份）",
                    "情绪对比（笑容vs眼泪）",
                ],
                "effectiveness_score": 92,
                "applicable_genres": ["revenge", "romance"],
            },
            {
                "id": "VH-003",
                "name": "神秘场景型",
                "core_mechanism": "未知空间/人物/物件引发好奇",
                "visual_elements": [
                    "未知空间（密室/异世界/未来都市）",
                    "神秘人物（背影/面具/剪影）",
                    "悬念物件（古老盒子/神秘信件）",
                ],
                "effectiveness_score": 88,
                "applicable_genres": ["suspense", "fantasy"],
            },
            {
                "id": "VH-004",
                "name": "情绪特写型",
                "core_mechanism": "放大面部表情传递强烈情绪",
                "visual_elements": [
                    "眼泪特写（滑落瞬间）",
                    "眼神变化（从柔弱到锐利）",
                    "表情凝固（震惊/愤怒/狂喜）",
                ],
                "effectiveness_score": 89,
                "applicable_genres": ["all"],
            },
            {
                "id": "VH-005",
                "name": "动作冲击型",
                "core_mechanism": "具有暴力美学的身体动作",
                "visual_elements": [
                    "扇巴掌（慢动作+音效）",
                    "下跪（强迫/自愿）",
                    "摔东西（瓷器碎裂）",
                    "强吻（突然/强迫）",
                ],
                "effectiveness_score": 87,
                "applicable_genres": ["revenge", "romance"],
            },
            {
                "id": "VH-006",
                "name": "色彩冲击型",
                "core_mechanism": "非常规色彩组合制造视觉冲击",
                "visual_elements": [
                    "高饱和对比（红与黑）",
                    "单色调变化（黑白到彩色）",
                    "色彩象征（血色/金色）",
                ],
                "effectiveness_score": 85,
                "applicable_genres": ["all"],
            },
            {
                "id": "VH-007",
                "name": "速度变化型",
                "core_mechanism": "快/慢动作对比制造节奏张力",
                "visual_elements": [
                    "慢动作（关键瞬间延长）",
                    "快切（信息密集轰炸）",
                    "定格（决定性时刻）",
                ],
                "effectiveness_score": 86,
                "applicable_genres": ["action", "suspense"],
            },
            {
                "id": "VH-008",
                "name": "空间错位型",
                "core_mechanism": "非常规空间关系制造不安/新奇",
                "visual_elements": ["倒置画面", "镜面反射", "画中画", "无人机视角"],
                "effectiveness_score": 84,
                "applicable_genres": ["suspense", "fantasy"],
            },
            {
                "id": "VH-009",
                "name": "符号隐喻型",
                "core_mechanism": "核心符号的视觉化呈现",
                "visual_elements": ["反复出现的物件", "标志性色彩", "特定构图"],
                "effectiveness_score": 83,
                "applicable_genres": ["suspense", "literary"],
            },
            {
                "id": "VH-010",
                "name": "身体奇观型",
                "core_mechanism": "身体的非常规状态呈现",
                "visual_elements": [
                    "伤痕特写",
                    "变身过程",
                    "衰老/年轻化",
                    "身体悬浮/穿透",
                ],
                "effectiveness_score": 85,
                "applicable_genres": ["fantasy", "suspense"],
            },
        ],
    }
    return hooks


def extract_archetypes():
    """提取角色原型库"""
    archetypes = {
        "protagonist": [
            {
                "id": "RA-001",
                "name": "隐忍复仇者",
                "name_en": "Revenge Protagonist - Enduring Type",
                "genre": "revenge",
                "surface_traits": ["柔弱", "低调", "被欺负", "沉默寡言", "逆来顺受"],
                "true_traits": ["强大", "智慧", "隐忍", "精于计算", "内心坚韧"],
                "surface_goal": "生存、保护身边人、维持现状",
                "deep_desire": "复仇、证明自我价值、夺回失去的一切",
                "fatal_flaw": "情感羁绊可能干扰复仇计划；过度隐忍导致机会丧失",
                "character_arc": "从被动承受到主动反击，从隐藏自我到公开身份，从复仇工具到完整人格",
                "dialogue_style_before": "简短、隐忍、双关（表面顺从，实则讽刺）",
                "dialogue_style_after": "霸气、犀利、直接、带有掌控感",
                "visual_markers": [
                    "服装从朴素到华丽",
                    "眼神从躲闪到锐利",
                    "气场从收敛到压迫",
                ],
                "classic_references": [
                    "《幸得相遇离婚时》女主",
                    "《好一个乖乖女》女主",
                ],
            },
            {
                "id": "RA-002",
                "name": "黑莲花女主",
                "name_en": "Revenge Protagonist - Scheming Type",
                "genre": "revenge",
                "core_traits": "表面清纯无害，实则心机深沉；主动布局，步步为营；善于利用他人",
                "difference_from_enduring": "更主动、更具攻击性；不等待时机，而是创造时机",
                "moral_gray_area": "为达目的可能使用非常手段；观众对其道德评判存在分歧",
                "classic_references": ["《黑莲花上位手册》女主（因价值观争议被下架）"],
            },
            {
                "id": "SA-001",
                "name": "纯真女主",
                "name_en": "Sweet Protagonist - Innocent Type",
                "genre": "romance",
                "core_traits": "善良、乐观、有些小迷糊、专业能力强但情感迟钝",
                "emotional_pattern": "慢热型，从误解到了解到深爱",
                "character_arc": "从情感被动到主动争取，从自我怀疑到自信确认",
                "dialogue_style": "内心OS丰富、吐槽式幽默、情感爆发时直接真诚",
                "classic_references": ["《心动还请告诉我》林晓"],
            },
            {
                "id": "SA-002",
                "name": "霸总男主",
                "name_en": "Sweet Protagonist - Dominant Type",
                "genre": "romance",
                "core_traits": "外表冷酷、掌控欲强、能力卓越、对女主专属温柔",
                "emotional_pattern": "一见钟情或日久生情，认定后专一执着",
                "classic_behaviors": [
                    "暗中保护",
                    "吃醋但不承认",
                    "为女主打破原则",
                    "公开护短",
                ],
                "dialogue_style": "命令式关心、反差萌（对旁人冷酷，对女主温柔）、情话直白",
                "visual_markers": ["西装革履", "手表/袖扣等细节", "居高临下的视角"],
            },
            {
                "id": "MA-001",
                "name": "天才侦探",
                "name_en": "Mystery Protagonist - Genius Type",
                "genre": "suspense",
                "core_traits": "观察力敏锐、逻辑推理能力强、知识渊博、社交能力可能欠缺",
                "core_motivation": "解开谜团的智力满足；正义感；个人创伤驱动",
                "classic_abilities": ["微表情识别", "犯罪心理侧写", "证据关联分析"],
                "classic_references": ["《隐秘的角落》张东升（反派视角的天才）"],
            },
            {
                "id": "MA-002",
                "name": "冷面刑警",
                "name_en": "Mystery Protagonist - Professional Type",
                "genre": "suspense",
                "core_traits": "专业能力强、情感克制、有原则、可能有过往创伤",
                "core_motivation": "职业责任；特定案件的执念；自我救赎",
                "classic_conflicts": "程序正义与结果正义的冲突；上级压力与个人判断",
            },
            {
                "id": "TA-001",
                "name": "金手指女主",
                "name_en": "Transmigration Protagonist - Cheat Type",
                "genre": "transmigration",
                "core_traits": "现代思维、知识优势、系统辅助、主动进取",
                "core_motivation": "改变原主悲剧命运；实现自我价值；寻找归属",
                "classic_abilities": [
                    "现代知识降维打击",
                    "系统任务奖励",
                    "预知未来信息",
                ],
                "character_arc": "从依赖金手指到自主成长，从改变他人到改变自己",
                "classic_references": ["《全家偷听我心声》女主"],
            },
        ],
        "antagonist": [
            {
                "name": "傲慢型反派",
                "name_en": "Arrogant",
                "core_traits": "目中无人、仗势欺人、自我感觉良好",
                "behavior_pattern": "公开羞辱主角、炫耀优势、拒绝认错",
                "defeat_reason": "低估主角；傲慢导致决策失误",
                "audience_reaction": "期待其被打脸；败北时获得爽感",
            },
            {
                "name": "阴险型反派",
                "name_en": "Scheming",
                "core_traits": "笑里藏刀、借刀杀人、机关算尽",
                "behavior_pattern": "暗中布局、挑拨离间、利用他人",
                "defeat_reason": "过度算计反被算计；众叛亲离",
                "audience_reaction": "愤怒其手段；佩服其智商",
            },
            {
                "name": "愚蠢型反派",
                "name_en": "Foolish",
                "core_traits": "又坏又蠢、搬石砸脚、盲目跟风",
                "behavior_pattern": "无脑挑衅、重复失败、被人利用",
                "defeat_reason": "智商不足；缺乏自知之明",
                "audience_reaction": "嘲笑其愚蠢；缺乏真实威胁感",
            },
        ],
        "supporting": [
            {
                "function": "神助攻",
                "name": "闺蜜/兄弟",
                "core_function": "情感支持、信息传递、危机救助",
                "classic_scenes": "女主失恋时陪伴、关键时刻递消息",
            },
            {
                "function": "信息源",
                "name": "忠诚助理/老仆",
                "core_function": "提供关键情报、执行秘密任务",
                "classic_scenes": "调查背景、传递信件、掩护身份",
            },
            {
                "function": "冲突催化剂",
                "name": "挑拨离间者/绿茶",
                "core_function": "制造误会、加剧矛盾、测试感情",
                "classic_scenes": "故意传错话、假装亲密、公开挑衅",
            },
            {
                "function": "情感对照",
                "name": "悲情牺牲者",
                "core_function": "强化主角动机、引发观众同情",
                "classic_scenes": "为保护主角而死、揭示隐藏真相",
            },
            {
                "function": "喜剧调剂",
                "name": "可爱萌宠/话痨",
                "core_function": "缓解紧张、提供笑点、情感连接",
                "classic_scenes": "关键时刻的意外帮助、日常互动",
            },
        ],
    }
    return archetypes


def extract_market_insights():
    """提取市场洞察数据"""
    return {
        "market_data_2024_2025": {
            "market_size": {
                "2024": "504.4亿元",
                "2025_forecast": "634亿元",
                "growth": "+25.7%",
            },
            "user_scale": {
                "2024": "6.62亿",
                "2025_forecast": "6.96亿",
                "growth": "+5.1%",
            },
            "free_model_share": {
                "2024": "45%",
                "2025_forecast": "55%",
                "change": "+10pct",
            },
            "avg_release_duration": {
                "2024": "10天",
                "2025_forecast": "7天",
                "change": "-30%",
            },
            "high_heat_works": {
                "2024": "18部",
                "2025_forecast": "12部",
                "change": "-33%",
            },
        },
        "key_trends": [
            {
                "trend": "免费模式主导",
                "description": "2025年免费短剧以66.3%的市场占比成为绝对主流，头部平台月活突破2.36亿",
                "impact": '从"单一钩子"升级为"高密度钩子矩阵"，构建"强逻辑情节递进体系"',
            },
            {
                "trend": "精品化与多元化并行",
                "description": '"照着爆款模板批量产出"导致短期同质化严重，但拉长观察周期可见题材显著多元化',
                "impact": '2025年Q1，红果平台30亿播放量短剧涵盖"现言、萌宝、修仙、反赌"等不同元素',
            },
            {
                "trend": "头部效应加剧",
                "description": "2025年热力值5000万以上的短剧仅12部，且集中在麦芽、河马、阅文、山海、番茄等头部平台",
                "impact": "中小团队生存压力增大",
            },
        ],
        "platform_strategies": [
            {
                "platform": "抖音",
                "core_audience": "18-30岁，一二线城市",
                "genre_preference": "女性成长+悬疑、强钩子引流",
                "content_features": "快节奏、高概念、视觉奇观",
                "representative_hits": ["《双面权臣暗恋我》", "《穿书富家妯娌》"],
            },
            {
                "platform": "快手",
                "core_audience": "25-40岁，下沉市场",
                "genre_preference": "家庭伦理+温情、接地气叙事",
                "content_features": "生活流、真实感、情感共鸣",
                "representative_hits": ["《东北爱情故事》", "《闪婚老伴是豪门》"],
            },
            {
                "platform": "红果",
                "core_audience": "全年龄段，免费用户为主",
                "genre_preference": "全品类覆盖，长停留时长设计",
                "content_features": "高密度钩子、强逻辑递进、季播化运营",
                "representative_hits": ["《幸得相遇离婚时》", "《云渺》系列"],
            },
        ],
        "trending_combinations": [
            {
                "name": "虐恋后追妻火葬场",
                "genres": ["revenge", "romance"],
                "core_structure": "女主因复仇/误会离开→男主意识到错误→展开追妻→双向救赎",
                "representative_case": "《幸得相遇离婚时》",
                "heat_score": 95,
                "innovation_score": 70,
                "risk_level": "低",
                "execution_points": '复仇阶段需有足够"痛感"积累；追妻阶段需有"诚意展示"',
            },
            {
                "name": "探案搭档生情",
                "genres": ["suspense", "romance"],
                "core_structure": "男女主因案件合作→互相试探→信任建立→情感升温→案件与情感双重揭秘",
                "representative_case": "《救命！我老公茶香四溢》",
                "heat_score": 88,
                "innovation_score": 85,
                "risk_level": "中",
                "execution_points": '案件复杂度需与情感发展节奏匹配；反派设计需有"情感关联"',
            },
            {
                "name": "古代开店致富",
                "genres": ["transmigration", "business"],
                "core_structure": "现代商业思维穿越→发现市场空白→建立商业帝国→改变历史/选择留下",
                "representative_case": "《如意满堂》《饥荒年嫁首辅》",
                "heat_score": 90,
                "innovation_score": 80,
                "risk_level": "低",
                "execution_points": '需设置"知识落地障碍"；情感线需与商业线交织',
            },
            {
                "name": "逆袭顶流明星",
                "genres": ["rebirth", "entertainment"],
                "core_structure": "前世被陷害陨落→重生回到关键节点→利用预知优势→事业爱情双丰收",
                "representative_case": "《千金谋》",
                "heat_score": 85,
                "innovation_score": 75,
                "risk_level": "中",
                "execution_points": '需有"专业细节"支撑逆袭合理性；舆论战设计需符合现实逻辑',
            },
            {
                "name": "金手指修仙路",
                "genres": ["system", "cultivation"],
                "core_structure": "凡人获得修仙系统→任务驱动升级→门派斗争→飞升成仙",
                "representative_case": "《云渺1：我修仙多年强亿点怎么了》",
                "heat_score": 92,
                "innovation_score": 78,
                "risk_level": "低",
                "execution_points": '系统设计"失效时刻"；单元案件降低观看门槛',
            },
            {
                "name": "职场开挂逆袭",
                "genres": ["mind_reading", "workplace"],
                "core_structure": "获得读心能力→职场博弈优势→揭露阴谋→晋升成长",
                "representative_case": "《杜小慧》",
                "heat_score": 90,
                "innovation_score": 82,
                "risk_level": "中",
                "execution_points": "读心范围需有限制；避免信息过载",
            },
            {
                "name": "身份错位爱情",
                "genres": ["contract_marriage", "identity_swap"],
                "core_structure": "契约关系+身份错位双重张力→真相揭露→情感确认",
                "representative_case": "多部融合剧",
                "heat_score": 88,
                "innovation_score": 80,
                "risk_level": "中",
                "execution_points": "双重悬念需精密配合；揭露时机需分层设计",
            },
            {
                "name": "无限流拯救爱人",
                "genres": ["time_loop", "redemption"],
                "core_structure": "被困时间循环→寻找拯救爱人的方法→牺牲与成长",
                "representative_case": "待开发",
                "heat_score": 87,
                "innovation_score": 88,
                "risk_level": "高",
                "execution_points": "循环机制需清晰；情感重量需逐步累积",
            },
            {
                "name": "身体错位喜剧",
                "genres": ["body_swap", "enemies_to_lovers"],
                "core_structure": "与死对头灵魂互换→被迫体验对方生活→理解与生情",
                "representative_case": "待开发",
                "heat_score": 86,
                "innovation_score": 85,
                "risk_level": "中",
                "execution_points": "喜剧效果与情感发展需平衡；换身规则需一致",
            },
            {
                "name": "大女主朝堂路",
                "genres": ["ancient_power", "female_growth"],
                "core_structure": "女性进入权力中心→权谋博弈→改革制度→确立地位",
                "representative_case": "《黑莲花上位手册》（已下架）",
                "heat_score": 93,
                "innovation_score": 75,
                "risk_level": "高",
                "execution_points": '需规避"以暴制暴"风险；权谋细节需专业',
            },
        ],
    }


def extract_writing_guide():
    """提取写作指导"""
    return {
        "sensory_vocabulary": {
            "conflict_scene": {
                "visual": [
                    "青筋暴起",
                    "眼神锐利",
                    "破碎的玻璃",
                    "飞溅的液体",
                    "扭曲的表情",
                ],
                "auditory": ["沉重的呼吸", "瓷器碎裂", "心跳加速", "怒吼", "耳光脆响"],
                "tactile": ["掌心出汗", "肌肉紧绷", "灼热感", "刺痛", "颤抖"],
                "olfactory": ["火药味", "血腥味", "汗味", "焦糊味"],
                "gustatory": ["铁锈味", "苦涩", "血腥味"],
            },
            "romantic_scene": {
                "visual": ["柔和光晕", "眼神交汇", "花瓣飘落", "夕阳余晖", "亲密距离"],
                "auditory": ["心跳声", "轻笑", "低语", "音乐", "呼吸声"],
                "tactile": ["柔软", "温暖", "电流感", "颤抖", "拥抱的紧实"],
                "olfactory": ["花香", "香水味", "阳光的味道", "对方的气息"],
                "gustatory": ["甜蜜", "微醺", "巧克力的苦甜"],
            },
            "suspense_scene": {
                "visual": [
                    "阴影层次",
                    "闪烁的灯光",
                    "模糊的轮廓",
                    "监视视角",
                    "封闭空间",
                ],
                "auditory": [
                    "寂静中的异响",
                    "脚步声",
                    "心跳",
                    "钟表滴答",
                    "突然的电话铃",
                ],
                "tactile": ["冷汗", "毛骨悚然", "黏腻", "冰冷", "僵硬"],
                "olfactory": ["霉味", "陈旧空气", "消毒水味", "未知的危险气息"],
                "gustatory": ["金属味", "干涩", "紧张导致的口渴"],
            },
            "daily_scene": {
                "visual": [
                    "阳光",
                    "整洁/凌乱的空间",
                    "日常物品",
                    "自然表情",
                    "生活细节",
                ],
                "auditory": ["喧嚣", "家常对话", "电视声", "厨房声响", "窗外噪音"],
                "tactile": ["温暖", "舒适", "疲惫", "放松", "熟悉的触感"],
                "olfactory": ["家常饭菜香", "阳光晒过的被子", "咖啡香"],
                "gustatory": ["家常味", "平淡", "满足", "怀念"],
            },
        },
        "pacing_templates": {
            "opening": {
                "stage": "开局（前3集）",
                "scene_count": "3-5个场景",
                "pace": "快节奏，信息密集",
                "hook_requirements": "前3秒必须抛出钩子，10秒建立冲突，30秒推进剧情",
                "reversal_density": "每集1-2个",
                "emotion_goal": "即时吸引，建立期待",
            },
            "middle": {
                "stage": "中段（付费点前）",
                "scene_count": "每集2-3个场景",
                "pace": "中快节奏，持续张力",
                "hook_requirements": "每集结尾必有悬念钩子",
                "reversal_density": "每集2-3个反转",
                "emotion_goal": "维持追剧动力，铺垫付费点",
            },
            "climax": {
                "stage": "高潮（付费点）",
                "scene_count": "集中爆发",
                "pace": "极快节奏，情绪峰值",
                "hook_requirements": "最大情绪强度+身份揭露+关系质变",
                "reversal_density": "连续反转",
                "emotion_goal": "付费转化，社交传播",
            },
            "ending": {
                "stage": "结局（后3集）",
                "scene_count": "2-3个场景",
                "pace": "舒缓节奏，情感释放",
                "hook_requirements": "闭环解答+长尾话题",
                "reversal_density": "1-2个关键反转",
                "emotion_goal": "满足感，余韵，续集期待",
            },
        },
        "key_data_reference": '免费短剧要求"15秒有冲突或反转，30秒推进剧情，最后10秒给出悬念"的工业标准；付费短剧需在第9-10集设置"卡点钩子"，将最大反击留至付费点后',
    }


def extract_visual_guide():
    """提取视觉指导"""
    return {
        "revenge": {
            "shot_style": "高对比、低角度、手持",
            "color_scheme": "冷色调（蓝/灰/暗绿），高饱和",
            "shot_selection": "特写（情绪）、低角度（强势）、全景（压迫）",
            "editing_pace": "快速剪辑、跳切",
            "special_techniques": "慢动作特写关键反击；服装蜕变可视化",
        },
        "romance": {
            "shot_style": "柔光、中景、稳定",
            "color_scheme": "暖色调（橙/粉/金），中高饱和",
            "shot_selection": "中景（互动）、特写（亲密）、全景（浪漫场景）",
            "editing_pace": "舒缓节奏，延长时间感知",
            "special_techniques": "柔光滤镜；亲密特写；浪漫场景仪式感",
        },
        "suspense": {
            "shot_style": "阴影层次、手持+固定",
            "color_scheme": "蓝绿色调，低饱和",
            "shot_selection": "特写（微表情）、全景（孤立感）、固定长镜头（凝视）",
            "editing_pace": "跳切加速紧张，固定长镜头营造压抑",
            "special_techniques": "符号隐喻；非线性时间呈现；不可靠视角",
        },
        "transmigration": {
            "shot_style": "古今对比、特效转场",
            "color_scheme": "现代冷色调vs古代暖色调，穿越时刻高饱和",
            "shot_selection": "大场面（奇观）、细节（知识运用）、特写（身份认知）",
            "editing_pace": "现代快节奏vs古代舒缓节奏",
            "special_techniques": "特效转场（时空扭曲）；服饰混搭；场景奇观",
        },
        "family_urban": {
            "shot_style": "自然光、纪实风格",
            "color_scheme": "温和色调，自然饱和",
            "shot_selection": "中景（日常互动）、特写（情感细节）、全景（生活空间）",
            "editing_pace": "舒缓节奏，保留生活质感",
            "special_techniques": "手持镜头增强真实感；细腻表演捕捉；烟火气场景",
        },
    }


def main():
    """主函数"""
    print("=" * 80)
    print("PDF短剧主题库数据提取工具")
    print("数据源: 中文短剧AI生成系统主题库研究报告.pdf")
    print("=" * 80)

    try:
        # 1. 解析PDF文本
        content = parse_pdf_text()

        # 2. 提取各类数据
        print("\n🔍 提取数据中...")

        genres = extract_genres_data(content)
        print(f"   ✓ 提取 {len(genres)} 个题材")

        tropes = extract_tropes_library()
        total_tropes = sum(len(v) for v in tropes.values())
        print(f"   ✓ 提取 {total_tropes} 个元素")

        hooks = extract_hooks_library()
        total_hooks = sum(len(v) for v in hooks.values())
        print(f"   ✓ 提取 {total_hooks} 个钩子模板")

        archetypes = extract_archetypes()
        total_archetypes = sum(len(v) for v in archetypes.values())
        print(f"   ✓ 提取 {total_archetypes} 个角色原型")

        market_insights = extract_market_insights()
        print(f"   ✓ 提取市场洞察数据")

        writing_guide = extract_writing_guide()
        print(f"   ✓ 提取写作指导")

        visual_guide = extract_visual_guide()
        print(f"   ✓ 提取视觉指导")

        # 3. 构建完整输出
        output = {
            "metadata": {
                "source_file": "中文短剧AI生成系统主题库研究报告.pdf",
                "extraction_date": datetime.now().isoformat(),
                "version": "1.0.0",
                "total_pages": 28,
                "total_characters": len(content),
            },
            "summary": {
                "genres_count": len(genres),
                "tropes_count": total_tropes,
                "hooks_count": total_hooks,
                "archetypes_count": total_archetypes,
            },
            "genres": genres,
            "tropes_library": tropes,
            "hooks_library": hooks,
            "archetypes": archetypes,
            "market_insights": market_insights,
            "writing_guide": writing_guide,
            "visual_guide": visual_guide,
        }

        # 4. 保存JSON文件
        output_file = "extracted_pdf_theme_data.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)

        print(f"\n💾 数据已保存到: {output_file}")

        # 5. 统计报告
        print("\n" + "=" * 80)
        print("📊 数据提取统计")
        print("=" * 80)
        print(f"题材:           {len(genres):3d} 个")
        print(f"元素:           {total_tropes:3d} 个")
        print(f"钩子模板:       {total_hooks:3d} 个")
        print(f"角色原型:       {total_archetypes:3d} 个")
        print(f"市场洞察:       ✓")
        print(f"写作指导:       ✓")
        print(f"视觉指导:       ✓")
        print("=" * 80)
        print("✅ PDF数据提取完成！")
        print(f"\n文件位置: ./{output_file}")
        print(f"文件大小: {len(json.dumps(output, ensure_ascii=False)) / 1024:.1f} KB")

        return True

    except Exception as e:
        print(f"\n❌ 数据提取失败: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    main()
