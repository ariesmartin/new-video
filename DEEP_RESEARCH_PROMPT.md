# Deep Research 提示词 - 短剧主题库数据收集

## 🎯 研究目标

通过系统性深度研究，收集并整理短剧创作的主题库数据，包括：题材公式、爆款元素、钩子模板、角色原型、市场趋势等。最终输出结构化数据，可直接用于AI短剧生成系统的主题库构建。

---

## 📋 研究任务清单

### 任务 1: 题材（Genre）深度分析

**研究内容**:
1. **复仇逆袭题材**
   - 收集10+部爆款复仇短剧案例
   - 提取核心公式（Setup → Rising → Climax → Resolution）
   - 总结3-5个必备爆款元素（Tropes）
   - 提取5-8个写作关键词
   - 提取3-5个视觉风格关键词
   - 总结3-5个避雷套路

2. **甜宠恋爱题材**
   - 同上结构

3. **悬疑推理题材**
   - 同上结构

4. **其他热门题材**（至少再选2个）
   - 穿越重生、现代都市、古装宫斗、职场商战等

**输出格式**:
```json
{
  "genre_analysis": {
    "revenge": {
      "core_formula": {
        "setup": "铺垫阶段的具体描述",
        "rising": "升级阶段的具体描述",
        "climax": "高潮阶段的具体描述",
        "resolution": "结局阶段的具体描述"
      },
      "emotional_arc": "情绪弧线描述",
      "tropes": [
        {
          "name": "元素名称",
          "description": "详细描述",
          "examples": ["具体例子1", "例子2"],
          "effectiveness_score": 95,
          "usage_timing": "使用时机（第几集）"
        }
      ],
      "writing_keywords": ["关键词1", "关键词2"],
      "visual_keywords": ["视觉词1", "视觉词2"],
      "avoid_patterns": ["避雷1", "避雷2"],
      "target_audience": {
        "age_range": "18-35",
        "gender": "female",
        "psychographics": "心理特征描述"
      },
      "viral_examples": [
        {"title": "爆款剧名", "why_it_works": "成功原因分析"}
      ]
    }
  }
}
```

---

### 任务 2: 爆款元素（Tropes）库构建

**研究内容**:
为每个题材收集15-20个爆款元素，分类如下：

1. **身份类元素**
   - 身份揭露、隐藏大佬、秘密皇室、卧底等
   - 每个元素包含：名称、描述、经典案例、成功率评估

2. **关系类元素**
   - 契约婚姻、冤家变情人、青梅竹马、三角恋等

3. **冲突类元素**
   - 打脸、复仇、背叛、救赎等

4. **设定类元素**
   - 时间循环、灵魂互换、重生、系统等

**输出格式**:
```json
{
  "trope_library": {
    "identity_reveal": {
      "name": "身份揭露",
      "name_en": "Identity Reveal",
      "category": "identity",
      "description": "主角的真实身份在关键时刻被揭露，震惊全场",
      "variations": [
        "隐藏身份型：主角一直隐藏真实身份",
        "失忆恢复型：主角失忆后恢复记忆",
        "双重身份型：主角有两个截然不同的身份"
      ],
      "usage_guidelines": {
        "best_timing": "第10-15集效果最佳",
        "preparation": "需要前期铺垫3-5集",
        "execution": "揭露时机要配合高潮场景"
      },
      "emotional_impact": {
        "satisfaction": 95,
        "surprise": 90,
        "replay_value": 85
      },
      "classic_examples": [
        {"drama": "剧名", "scene": "具体场景描述", "why_effective": "有效原因"}
      ],
      "success_rate": 92,
      "risk_factors": ["过早揭露会削弱效果", "铺垫不足会显得突兀"]
    }
  }
}
```

---

### 任务 3: 钩子模板（Hooks）库构建

**研究内容**:
收集前3秒留存钩子模板，按类型分类：

1. **情境型钩子**（Situation Hooks）
   - 羞辱场景、生死一线、误会冲突等
   - 收集10+模板

2. **悬念型钩子**（Question Hooks）
   - 直接提问、反常识陈述、预言等
   - 收集10+模板

3. **视觉型钩子**（Visual Hooks）
   - 奇观展示、强烈对比、神秘场景等
   - 收集10+模板

**输出格式**:
```json
{
  "hook_templates": {
    "situation_hooks": [
      {
        "id": "extreme_humiliation",
        "name": "极限羞辱",
        "template": "主角正在遭受[极端羞辱]，但[隐藏实力/即将反击]",
        "variables": {
          "humiliation_type": ["被当众退婚", "被开除", "被嘲笑", "被泼咖啡"],
          "hidden_element": ["真实身份", "隐藏实力", "即将反击"]
        },
        "effectiveness_score": 95,
        "applicable_genres": ["revenge", "urban"],
        "examples": [
          {"drama": "剧名", "hook_text": "具体钩子文案", "completion_rate": "完播率数据"}
        ],
        "usage_tips": "使用技巧和建议"
      }
    ]
  }
}
```

---

### 任务 4: 角色原型（Archetypes）分析

**研究内容**:
为每个题材收集5-8个经典角色原型：

1. **主角原型**
   - 复仇型、甜宠型、悬疑型等
   - 每个原型包含：性格特质、核心动机、成长弧线、经典台词风格

2. **反派原型**
   - 傲慢型、阴险型、愚蠢型等

3. **配角原型**
   - 闺蜜、助理、长辈等

**输出格式**:
```json
{
  "character_archetypes": {
    "revenge_protagonist": {
      "name": "复仇女主",
      "name_en": "Revenge Protagonist",
      "role": "protagonist",
      "core_traits": {
        "surface": ["表面特征：柔弱、低调、被欺负"],
        "true": ["真实特质：强大、智慧、隐忍"]
      },
      "motivation": {
        "surface_goal": "表面目标",
        "deep_desire": "深层欲望",
        "fatal_flaw": "致命弱点"
      },
      "character_arc": "角色成长弧线描述",
      "dialogue_style": {
        "before_reveal": "身份揭露前：隐忍、简短",
        "after_reveal": "身份揭露后：霸气、犀利"
      },
      "visual_markers": ["服装变化", "眼神变化", "气场变化"],
      "relationship_dynamics": {
        "with_antagonist": "与反派的关系动态",
        "with_love_interest": "与恋人的关系动态"
      },
      "classic_examples": ["参考角色1", "参考角色2"]
    }
  }
}
```

---

### 任务 5: 市场趋势与热门组合

**研究内容**:
1. **题材趋势分析**
   - 2024-2025年短剧市场趋势
   - 各题材热度排名
   - 新兴题材识别

2. **热门组合（Cross-Genre）**
   - 复仇+甜宠
   - 悬疑+恋爱
   - 穿越+经营
   - 收集10+创新组合

3. **成功要素提取**
   - 从爆款中提取共性成功因素
   - 分析失败案例的常见问题

**输出格式**:
```json
{
  "market_insights": {
    "trending_2024_2025": {
      "hot_genres": [
        {"genre": "题材名", "heat_score": 95, "growth_rate": "增长率"}
      ],
      "emerging_trends": ["新兴趋势1", "趋势2"],
      "audience_preferences": {
        "age_groups": {"18-25": ["题材1", "题材2"]},
        "gender_preferences": {"female": ["甜宠", "复仇"]},
        "platform_differences": {"抖音": "偏好", "快手": "偏好"}
      }
    },
    "trending_combinations": [
      {
        "name": "组合名称",
        "genres": ["题材1", "题材2"],
        "example": "成功案例",
        "heat_score": 92,
        "novelty_score": 85,
        "risk_level": "low/medium/high",
        "why_it_works": "成功原因分析",
        "execution_tips": "执行建议"
      }
    ],
    "success_factors": {
      "common_elements": ["成功要素1", "要素2"],
      "failure_patterns": ["失败模式1", "模式2"]
    }
  }
}
```

---

### 任务 6: 写作与视觉指导

**研究内容**:
1. **五感描写词汇库**
   - 按场景分类（冲突、浪漫、悬疑、日常）
   - 每个场景提供视觉、听觉、触觉、嗅觉、味觉词汇

2. **节奏控制模板**
   - 开局节奏（前3集）
   - 中段节奏（付费点前）
   - 高潮节奏
   - 结局节奏

3. **视觉风格指南**
   - 各题材的镜头风格
   - 色彩方案
   - 景别选择

**输出格式**:
```json
{
  "writing_guide": {
    "sensory_vocabulary": {
      "conflict_scene": {
        "visual": ["青筋暴起", "眼神锐利", "破碎的玻璃"],
        "auditory": ["沉重的呼吸", "瓷器碎裂", "心跳加速"],
        "tactile": ["掌心出汗", "肌肉紧绷", "灼热感"],
        "olfactory": ["火药味", "血腥味"],
        "gustatory": ["铁锈味", "苦涩"]
      }
    },
    "pacing_templates": {
      "opening": {
        "scene_count": "3-5个场景",
        "pace": "快节奏",
        "hook_requirements": "前3秒必须抛出钩子"
      }
    }
  },
  "visual_guide": {
    "revenge": {
      "shot_types": ["特写", "低角度", "手持"],
      "lighting": ["高对比", "侧光", "阴影"],
      "color_scheme": ["冷色调", "高饱和"],
      "camera_techniques": ["快速剪辑", "跳切"]
    }
  }
}
```

---

## 🔍 研究方法论

### 搜索策略

1. **多源验证**
   - 每个数据点至少从2-3个不同来源验证
   - 优先使用一手数据（平台榜单、实际案例）
   - 交叉验证AI生成数据的准确性

2. **案例分析法**
   - 选择具体爆款短剧作为案例
   - 拆解其结构、元素、钩子
   - 提取可复用的模式

3. **对比分析法**
   - 对比成功与失败案例
   - 识别关键差异因素
   - 总结最佳实践

4. **趋势识别**
   - 分析时间序列数据
   - 识别新兴趋势
   - 预测未来方向

### 数据源建议

**高可信度源**:
- 抖音/快手短剧榜单
- 短剧平台官方数据
- 专业编剧/制作人访谈
- 行业分析报告（艾瑞、克劳锐等）

**辅助参考源**:
- 短剧评论区分析
- 社交媒体讨论
- 长剧/网文的成功模式（可迁移性分析）
- 心理学/叙事学理论

**避免使用**:
- 未经证实的个人观点
- 过时数据（超过2年）
- 单一来源的信息

---

## 📊 输出要求

### 质量要求

1. **准确性**: 所有数据必须准确，有可靠来源
2. **完整性**: 每个字段都要填写，不能留空
3. **实用性**: 数据必须可直接用于AI生成
4. **结构化**: 严格按照JSON格式输出
5. **可验证**: 每个结论都要有案例支撑

### 数量要求

- **题材**: 至少5个核心题材
- **元素**: 每个题材15-20个元素
- **钩子**: 每个类型10+模板
- **角色**: 每个题材5-8个原型
- **组合**: 10+创新组合

### 深度要求

每个数据点都要包含：
- ✅ 定义和描述
- ✅ 具体案例
- ✅ 使用指南
- ✅ 效果评估
- ✅ 风险提示

---

## 🎨 输出格式

最终输出应为**单个JSON文件**，结构如下：

```json
{
  "research_metadata": {
    "version": "1.0.0",
    "research_date": "2026-02-07",
    "researcher": "AI Research Agent",
    "total_themes": 5,
    "total_tropes": 85,
    "total_hooks": 45,
    "data_sources": ["source1", "source2"]
  },
  "genres": { ... },
  "tropes": { ... },
  "hooks": { ... },
  "archetypes": { ... },
  "market_insights": { ... },
  "writing_guide": { ... },
  "visual_guide": { ... }
}
```

---

## ⚠️ 注意事项

1. **版权问题**: 不要直接复制受版权保护的剧本内容，而是提取模式和公式
2. **数据时效**: 优先使用2024-2025年的数据，短剧市场变化很快
3. **文化适配**: 考虑中文短剧市场的特殊性，不要简单套用国外模式
4. **平台差异**: 注意不同平台（抖音vs快手）的受众偏好差异

---

## ✅ 验收标准

研究完成的标准：
- [ ] 5个核心题材的完整分析
- [ ] 每个题材15-20个可复用元素
- [ ] 30+钩子模板（3种类型×10个）
- [ ] 25+角色原型（5个题材×5个）
- [ ] 10+热门组合分析
- [ ] 每个数据点都有案例支撑
- [ ] JSON格式正确，可直接解析
- [ ] 所有字段填写完整

---

**开始研究前，请确认**:
1. 你理解所有任务要求
2. 你明白输出格式
3. 你有足够的研究时间（建议2-4小时）
4. 你确认可以访问所需数据源

**准备好了吗？开始深度研究！** 🔍
