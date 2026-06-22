# AI 味检测与去味指南

> 融合自 humanizer(25.6K⭐)、stop-slop(11.8K⭐)、nuwa-skill(25.3K⭐)、taste-skill(48.9K⭐)

## 什么是"AI味"？

AI味 = LLM生成文本中可被人类直觉感知的"机器感"。表现为：
- 过度正式、缺乏观点、节奏均匀
- 套话连篇、填充词泛滥、结构模板化
- 情感标签化、解释性旁白、虚假共鸣

## 检测引擎

```python
from data_modules.ai_flavor_engine import detect_ai_flavor

report = detect_ai_flavor(text, reference_text=None)
# report.dimension_score — 五维度评分
# report.pattern_hits — 33类AI模式命中
# report.quick_check_results — 12项Quick Checks
# report.structural_patterns — 8类结构模式
```

## 五维度评分（stop-slop标准）

| 维度 | 含义 | 扣分项 |
|------|------|--------|
| 直白度 | 说话直接不绕弯 | 填充词、模糊声明、过度修饰 |
| 节奏 | 长短句交替、有呼吸感 | 句长均匀、三连结构、em-dash |
| 信任感 | 读起来像真人写的 | 万能引言、虚假共鸣、模糊声明 |
| 真实感 | 有情感、有立场、有温度 | 情感标签化、陈词滥调、中立无聊 |
| 密度 | 每句话都有信息量 | 填充词、过度总结、元叙述 |

**总分 < 35/50 → 必须修订**

## 33类AI写作模式速查

### 内容模式（6类）
- 百科式定义：以"X是..."开头
- 万能引言：引用名人名言做装饰
- 过度总结：段末"总之"、"综上所述"
- 二元对立："不是X，而是Y"
- 万能过渡：机械转折词
- 虚假共鸣："我们都经历过"

### 语言语法（7类）
- 过度被动语态
- 名词化堆砌："进行分析"代替"分析"
- 过度修饰："非常重要的"
- 句式单一：连续相同句式
- 过度从句：嵌套3层以上
- 假主语："有"、"存在着"
- 数字列表化

### 风格（6类）
- 中立到无聊：无观点、无情绪
- 过度正式：口语场景用书面语
- 节奏均匀：段落/句长高度一致
- 情感标签化："他很愤怒"
- 解释性旁白：作者跳出叙述解释
- 陈词滥调：被用烂的比喻

### 沟通（3类）
- 直接对读者喊话
- 元叙述：讨论文章本身
- 假装提问：修辞性问题+自答

### 填充词（10类）
- delve、tapestry、landscape、navigate、foster
- multifaceted、pivotal、it's worth noting
- in conclusion、it's important to note

## 声纹校准

```python
from data_modules.ai_flavor_engine import calibrate_voice

profile = calibrate_voice(reference_text)
# profile.avg_sentence_length — 平均句长
# profile.preferred_transitions — 常用过渡词
# profile.vocabulary_level — 用词层级
# profile.paragraph_opening_style — 段首习惯
```

## 12项Quick Checks（自动化检测）

| # | 检查项 | 阈值 | 修复 |
|---|--------|------|------|
| 1 | 副词 | >0处 | 删除 |
| 2 | 被动语态 | >0处 | 改为主动 |
| 3 | 三连结构 | >0处 | 打破节奏 |
| 4 | em-dash | >3次 | 减少使用 |
| 5 | 模糊声明 | >2次 | 用具体数据 |
| 6 | 填充词 | >5个 | 精简 |
| 7 | 句长均匀度 | std<15% | 增加变化 |
| 8 | 过渡词 | >8个 | 减少显式过渡 |
| 9 | 修辞问句 | >5个 | 直接陈述 |
| 10 | 省略号 | >5个 | 减少使用 |
| 11 | 段落长度 | >2.5x均值 | 拆分/合并 |
| 12 | 展示vs告诉 | >0处 | 用行为描写 |
