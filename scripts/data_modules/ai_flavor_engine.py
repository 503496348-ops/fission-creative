#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI 味检测与改写引擎 v1.0

融合4个开源竞品的核心能力：
- 33类AI写作模式检测（humanizer, 25.6K⭐）
- 5维度量化评分（stop-slop, 11.8K⭐）
- 12项Quick Checks预交付检查（stop-slop, 11.8K⭐）
- 声纹校准引擎（humanizer, 25.6K⭐）
- 8类结构模式检测（stop-slop, 11.8K⭐）
- 灵魂注入系统（humanizer, 25.6K⭐）
- 质量自检框架（nuwa-skill, 25.3K⭐）

集成方式：检测→评分→改写→复检 闭环
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


# ═══════════════════════════════════════════════════════════════
# Part 1: AI 写作模式分类体系（33类）
# ═══════════════════════════════════════════════════════════════

@dataclass
class AIPattern:
    """单个AI写作模式"""
    category: str       # 内容模式/语言语法/风格/沟通/填充词
    name: str           # 模式名称
    description: str    # 描述
    regex_patterns: List[str] = field(default_factory=list)  # 正则检测
    keywords: List[str] = field(default_factory=list)        # 关键词检测
    severity: str = "medium"  # critical/high/medium/low


# 33类AI写作模式（基于humanizer的Wikipedia分类体系）
AI_PATTERNS: List[AIPattern] = [
    # ── 内容模式（6类）──
    AIPattern(
        category="内容模式", name="百科式定义",
        description="以字典定义开头，如'X是...'、'X指的是...'",
        regex_patterns=[r"^(.{2,8})是.{2,20}(一种|指的是|意味着|定义为)"],
        severity="high"
    ),
    AIPattern(
        category="内容模式", name="万能引言",
        description="使用泛滥的名人名言开头",
        keywords=["正如爱因斯坦所说", "正如莎士比亚所说", "老子曾经说过",
                  "有一句古老的谚语", "正如那句名言"],
        severity="high"
    ),
    AIPattern(
        category="内容模式", name="过度总结",
        description="段末用'总之'、'总而言之'、'综上所述'做机械总结",
        keywords=["总之", "总而言之", "综上所述", "总的来说", "简而言之",
                  "概括来说", "归根结底"],
        severity="medium"
    ),
    AIPattern(
        category="内容模式", name="二元对立框架",
        description="用'不是X，而是Y'的结构制造虚假对立",
        regex_patterns=[r"不是.{2,15}，而是.{2,15}", r"与其说.{2,15}不如说"],
        severity="medium"
    ),
    AIPattern(
        category="内容模式", name="万能过渡",
        description="用'然而'、'但是'、'不过'做机械转折",
        keywords=["然而，", "但是，", "不过，", "尽管如此", "话说回来"],
        severity="low"
    ),
    AIPattern(
        category="内容模式", name="虚假共鸣",
        description="用'我们都经历过'、'每个人都知道'制造假共鸣",
        regex_patterns=[r"我们都.{2,10}过", r"每个人(都|都知道|都有过)",
                        r"你(是否|是不是)也(曾经|有过)"],
        severity="medium"
    ),

    # ── 语言语法模式（7类）──
    AIPattern(
        category="语言语法", name="过度被动语态",
        description="大量使用被动语态，缺乏施动者",
        regex_patterns=[r"被.{1,6}(了|着|过)", r"(被|由|让|叫).{2,10}(所|而)"],
        severity="low"
    ),
    AIPattern(
        category="语言语法", name="名词化堆砌",
        description="把动词变成名词，如'进行分析'代替'分析'",
        keywords=["进行分析", "进行研究", "进行讨论", "进行评估",
                  "做出决定", "做出贡献", "做出努力", "开展工作"],
        severity="medium"
    ),
    AIPattern(
        category="语言语法", name="过度修饰",
        description="形容词/副词堆砌，如'非常重要的、极其关键的'",
        regex_patterns=[r"(非常|极其|十分|相当|格外|特别|尤其)(重要|关键|核心|显著|明显)"],
        severity="medium"
    ),
    AIPattern(
        category="语言语法", name="句式单一",
        description="连续使用相同句式结构（主谓宾/主系表重复3次以上）",
        regex_patterns=[],  # 需要段落级别检测
        severity="medium"
    ),
    AIPattern(
        category="语言语法", name="过度从句",
        description="一句话嵌套3层以上从句",
        regex_patterns=[r"，(而|且|但|却|就|才|也|都|又|再|还|已).{5,30}，(而|且|但|却|就|才|也|都|又|再|还|已)"],
        severity="low"
    ),
    AIPattern(
        category="语言语法", name="假主语",
        description="用'有'、'存在'做假主语回避施动者",
        regex_patterns=[r"^(有|存在着?|存在着这样)", r"^(值得注意的是|需要指出的是|不可否认)"],
        severity="medium"
    ),
    AIPattern(
        category="语言语法", name="数字+名词化",
        description="用数字列表代替流畅叙述",
        regex_patterns=[r"^(第[一二三四五六七八九十]|[1-9][\.\、])"],
        severity="low"
    ),

    # ── 风格模式（6类）──
    AIPattern(
        category="风格", name="中立到无聊",
        description="完全没有观点、立场、情绪的机器人腔",
        keywords=[],  # 需要语义级别检测
        severity="high"
    ),
    AIPattern(
        category="风格", name="过度正式",
        description="口语场景使用书面语，如日常对话用'笔者认为'",
        keywords=["笔者认为", "笔者以为", "笔者发现", "不难看出",
                  "由此可见", "由此可见一斑"],
        severity="medium"
    ),
    AIPattern(
        category="风格", name="节奏均匀",
        description="段落长度、句长高度一致，缺乏节奏变化",
        regex_patterns=[],  # 需要统计检测
        severity="medium"
    ),
    AIPattern(
        category="风格", name="情感标签化",
        description="直接说'他很愤怒'而不是用行为描写表达情绪",
        regex_patterns=[r"(他|她|我)(非常|十分|极其|特别)?(愤怒|高兴|悲伤|开心|难过|兴奋|紧张|害怕)"],
        severity="medium"
    ),
    AIPattern(
        category="风格", name="解释性旁白",
        description="作者跳出叙述解释角色动机，而不是让行为自己说话",
        regex_patterns=[r"(之所以|因为|原因是).{5,30}(所以|于是|因此)"],
        severity="medium"
    ),
    AIPattern(
        category="风格", name="陈词滥调",
        description="使用被用烂的比喻和描写",
        keywords=["心如刀割", "泪如雨下", "怒火中烧", "热血沸腾",
                  "如沐春风", "恍如隔世", "物是人非", "沧海桑田",
                  "时间如白驹过隙", "岁月如梭", "光阴似箭"],
        severity="medium"
    ),

    # ── 沟通模式（3类）──
    AIPattern(
        category="沟通", name="直接对读者喊话",
        description="用'你可能会问'、'让我们来看看'对读者喊话",
        regex_patterns=[r"你(可能|或许|也许|一定)(会|在)(想|问|思考|好奇)",
                        r"让(我们|我)(一起)?来(看看|探讨|了解|分析)"],
        severity="medium"
    ),
    AIPattern(
        category="沟通", name="元叙述",
        description="讨论文章本身而不是讨论内容",
        keywords=["在这篇文章中", "本文将", "接下来我们将",
                  "在下一节中", "如前所述", "正如上文所述"],
        severity="medium"
    ),
    AIPattern(
        category="沟通", name="假装提问",
        description="用修辞性问题做过渡，然后自己回答",
        regex_patterns=[r"[？\?].{0,5}(答案是|其实|事实上|简单来说)"],
        severity="low"
    ),

    # ── 填充词模式（10类）──
    AIPattern(
        category="填充词", name="delve",
        description="AI最爱用的词之一",
        keywords=["深入探讨", "深入挖掘", "深入分析", "深入研究",
                  "delve into", "delve deeper"],
        severity="high"
    ),
    AIPattern(
        category="填充词", name="tapestry",
        description="AI喜欢用的花哨比喻",
        keywords=["交织成", "编织成", "构成了一幅", "如同一幅画卷"],
        severity="medium"
    ),
    AIPattern(
        category="填充词", name="landscape",
        description="AI喜欢用landscape做万能名词",
        keywords=["格局", "全景", "全貌", "宏观视角", "全局视角"],
        severity="low"
    ),
    AIPattern(
        category="填充词", name="navigate",
        description="AI喜欢用navigate代替具体动词",
        keywords=["驾驭", "游刃有余", "如鱼得水", "驾轻就熟"],
        severity="low"
    ),
    AIPattern(
        category="填充词", name="foster",
        description="AI喜欢用foster做万能动词",
        keywords=["培养", "孕育", "催生", "促进", "推动"],
        severity="low"
    ),
    AIPattern(
        category="填充词", name="multifaceted",
        description="AI喜欢用复杂形容词代替简单词",
        keywords=["多方面的", "多层次的", "多维度的", "全方位的",
                  "综合性的", "系统性的"],
        severity="medium"
    ),
    AIPattern(
        category="填充词", name="pivotal",
        description="AI喜欢用pivotal做万能重要性修饰",
        keywords=["至关重要的", "举足轻重的", "不可或缺的", "关键性的"],
        severity="medium"
    ),
    AIPattern(
        category="填充词", name="it's worth noting",
        description="AI喜欢用这个短语做过渡",
        keywords=["值得注意的是", "值得一提的是", "需要指出的是",
                  "不可忽视的是", "不容忽视的是"],
        severity="medium"
    ),
    AIPattern(
        category="填充词", name="in conclusion",
        description="AI喜欢用固定结尾短语",
        keywords=["总而言之", "综上所述", "总的来说", "归根结底",
                  "最后但同样重要的是"],
        severity="medium"
    ),
    AIPattern(
        category="填充词", name="it's important to note",
        description="AI喜欢用这个短语强调",
        keywords=["重要的是要注意", "需要强调的是", "必须指出的是",
                  "显而易见", "毫无疑问"],
        severity="medium"
    ),
]


# ═══════════════════════════════════════════════════════════════
# Part 2: 12项 Quick Checks（stop-slop）
# ═══════════════════════════════════════════════════════════════

@dataclass
class QuickCheckResult:
    """单项检查结果"""
    check_name: str
    passed: bool
    issues: List[str] = field(default_factory=list)
    severity: str = "medium"


def _check_adverbs(text: str) -> QuickCheckResult:
    """检查1：副词→杀（地/着/了后面跟副词）"""
    pattern = re.compile(r"[，。！？；\n](.{2,8}地)(.{2,20})[，。！？；\n]")
    matches = pattern.findall(text)
    issues = [f"「{m[0]}{m[1]}」中的副词可删除" for m in matches[:5]]
    return QuickCheckResult("副词检查", len(issues) == 0, issues, "low")


def _check_passive_voice(text: str) -> QuickCheckResult:
    """检查2：被动语态→找施动者"""
    pattern = re.compile(r"(被|由|让|叫|为...所).{1,10}(了|着|过|地)")
    matches = pattern.findall(text)
    issues = [f"被动语态「{m}」→ 改为主动" for m in matches[:5]]
    return QuickCheckResult("被动语态检查", len(issues) == 0, issues, "medium")


def _check_triple_pattern(text: str) -> QuickCheckResult:
    """检查3：三连结构→打破"""
    # 检测连续三个相似结构的句子
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    issues = []
    for i in range(len(lines) - 2):
        if len(lines[i]) > 5 and len(lines[i+1]) > 5 and len(lines[i+2]) > 5:
            # 检查是否句式相似（长度接近 + 结构相似）
            lens = [len(l) for l in lines[i:i+3]]
            if max(lens) - min(lens) < 10:
                issues.append(f"三连句式（行{i+1}-{i+3}）→ 打破节奏")
    return QuickCheckResult("三连结构检查", len(issues) == 0, issues[:3], "medium")


def _check_em_dash(text: str) -> QuickCheckResult:
    """检查4：em-dash滥用→删除"""
    count = text.count('—') + text.count('——')
    issues = []
    if count > 3:
        issues.append(f"em-dash出现{count}次（>3），减少使用")
    return QuickCheckResult("em-dash检查", len(issues) == 0, issues, "low")


def _check_vague_statements(text: str) -> QuickCheckResult:
    """检查5：模糊声明→具名化"""
    vague = ["某些", "一些", "很多", "大量", "不少", "许多", "往往", "通常"]
    found = [v for v in vague if text.count(v) > 2]
    issues = [f"「{v}」出现{text.count(v)}次→ 用具体数据替代" for v in found]
    return QuickCheckResult("模糊声明检查", len(issues) == 0, issues, "medium")


def _check_filler_words(text: str) -> QuickCheckResult:
    """检查6：填充词过多"""
    fillers = ["其实", "事实上", "实际上", "说实话", "老实说", "坦白说"]
    total = sum(text.count(f) for f in fillers)
    issues = []
    if total > 5:
        issues.append(f"填充词共{total}个（>5）→ 精简")
    return QuickCheckResult("填充词检查", len(issues) == 0, issues, "low")


def _check_sentence_length_uniformity(text: str) -> QuickCheckResult:
    """检查7：句长均匀度→增加变化"""
    sentences = re.split(r'[。！？]', text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 5]
    if len(sentences) < 3:
        return QuickCheckResult("句长变化检查", True, [], "low")
    lengths = [len(s) for s in sentences]
    avg = sum(lengths) / len(lengths)
    variance = sum((l - avg) ** 2 for l in lengths) / len(lengths)
    std = variance ** 0.5
    issues = []
    if std < avg * 0.15:
        issues.append(f"句长标准差{std:.1f}（<平均长15%）→ 增加长短句变化")
    return QuickCheckResult("句长变化检查", len(issues) == 0, issues, "medium")


def _check_transition_words(text: str) -> QuickCheckResult:
    """检查8：过渡词过多"""
    transitions = ["然而", "但是", "不过", "因此", "所以", "于是",
                   "同时", "此外", "另外", "与此同时", "不仅如此"]
    total = sum(text.count(t) for t in transitions)
    issues = []
    if total > 8:
        issues.append(f"过渡词共{total}个（>8）→ 减少显式过渡")
    return QuickCheckResult("过渡词检查", len(issues) == 0, issues, "low")


def _check_rhetorical_questions(text: str) -> QuickCheckResult:
    """检查9：修辞问句过多"""
    count = len(re.findall(r'[？?]', text))
    issues = []
    if count > 5:
        issues.append(f"问号{count}个（>5）→ 减少修辞问句")
    return QuickCheckResult("修辞问句检查", len(issues) == 0, issues, "low")


def _check_ellipsis_overuse(text: str) -> QuickCheckResult:
    """检查10：省略号滥用"""
    count = text.count('…') + text.count('...')
    issues = []
    if count > 5:
        issues.append(f"省略号{count}个（>5）→ 减少使用")
    return QuickCheckResult("省略号检查", len(issues) == 0, issues, "low")


def _check_paragraph_length(text: str) -> QuickCheckResult:
    """检查11：段落长度均匀度"""
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
    if len(paragraphs) < 3:
        return QuickCheckResult("段落长度检查", True, [], "low")
    lengths = [len(p) for p in paragraphs]
    avg = sum(lengths) / len(lengths)
    issues = []
    for i, l in enumerate(lengths):
        if l > avg * 2.5:
            issues.append(f"第{i+1}段过长（{l}字，均值{avg:.0f}）→ 拆分")
        elif l < avg * 0.3 and l > 0:
            issues.append(f"第{i+1}段过短（{l}字，均值{avg:.0f}）→ 合并或扩展")
    return QuickCheckResult("段落长度检查", len(issues) == 0, issues[:3], "medium")


def _check_show_dont_tell(text: str) -> QuickCheckResult:
    """检查12：告诉而非展示"""
    tell_patterns = [
        r"(他|她|我)(感到|觉得|意识到|明白|知道).{2,15}",
        r"(气氛|环境|场面)(很|非常|十分|极其)(紧张|沉重|压抑|热烈|安静)",
    ]
    issues = []
    for p in tell_patterns:
        matches = re.findall(p, text)
        if matches:
            issues.append(f"「{matches[0]}」→ 用行为/感官描写替代直接陈述")
    return QuickCheckResult("展示vs告诉检查", len(issues) == 0, issues[:3], "medium")


# 所有Quick Checks
QUICK_CHECKS = [
    _check_adverbs,
    _check_passive_voice,
    _check_triple_pattern,
    _check_em_dash,
    _check_vague_statements,
    _check_filler_words,
    _check_sentence_length_uniformity,
    _check_transition_words,
    _check_rhetorical_questions,
    _check_ellipsis_overuse,
    _check_paragraph_length,
    _check_show_dont_tell,
]


# ═══════════════════════════════════════════════════════════════
# Part 3: 五维度量化评分（stop-slop）
# ═══════════════════════════════════════════════════════════════

@dataclass
class DimensionScore:
    """五维度评分"""
    directness: float = 10.0    # 直白度（1-10）
    rhythm: float = 10.0        # 节奏（1-10）
    trust: float = 10.0         # 信任感（1-10）
    authenticity: float = 10.0  # 真实感（1-10）
    density: float = 10.0       # 密度（1-10）

    @property
    def total(self) -> float:
        return self.directness + self.rhythm + self.trust + self.authenticity + self.density

    @property
    def needs_revision(self) -> bool:
        return self.total < 35  # stop-slop标准：35/50以下必须修订

    def to_dict(self) -> Dict[str, float]:
        return {
            "直白度": round(self.directness, 1),
            "节奏": round(self.rhythm, 1),
            "信任感": round(self.trust, 1),
            "真实感": round(self.authenticity, 1),
            "密度": round(self.density, 1),
            "总分": round(self.total, 1),
            "需修订": self.needs_revision,
        }


def score_text(text: str, detected_patterns: List[AIPattern],
               quick_check_results: List[QuickCheckResult]) -> DimensionScore:
    """基于检测结果计算五维度评分"""
    score = DimensionScore()

    # 直白度：模糊声明、填充词、过度修饰扣分
    vague_count = sum(1 for p in detected_patterns if p.category == "填充词")
    score.directness = max(1, 10 - vague_count * 0.8)

    # 节奏：句长均匀、三连结构、em-dash扣分
    rhythm_issues = sum(1 for r in quick_check_results
                        if not r.passed and r.check_name in ["句长变化检查", "三连结构检查", "em-dash检查"])
    score.rhythm = max(1, 10 - rhythm_issues * 1.5)

    # 信任感：虚假共鸣、万能引言、模糊声明扣分
    trust_issues = sum(1 for p in detected_patterns
                       if p.name in ["万能引言", "虚假共鸣", "模糊声明"])
    score.trust = max(1, 10 - trust_issues * 1.2)

    # 真实感：情感标签化、解释性旁白、陈词滥调扣分
    fake_count = sum(1 for p in detected_patterns
                     if p.name in ["情感标签化", "解释性旁白", "陈词滥调", "中立到无聊"])
    score.authenticity = max(1, 10 - fake_count * 1.5)

    # 密度：填充词、过度总结、元叙述扣分
    filler_count = sum(1 for p in detected_patterns
                       if p.category == "填充词" or p.name in ["过度总结", "元叙述"])
    score.density = max(1, 10 - filler_count * 0.6)

    return score


# ═══════════════════════════════════════════════════════════════
# Part 4: 声纹校准引擎（humanizer）
# ═══════════════════════════════════════════════════════════════

@dataclass
class VoiceProfile:
    """声纹档案（从参考文本中提取）"""
    avg_sentence_length: float = 0.0      # 平均句长
    sentence_length_variance: float = 0.0 # 句长方差
    preferred_transitions: List[str] = field(default_factory=list)  # 常用过渡词
    punctuation_style: Dict[str, float] = field(default_factory=dict)  # 标点偏好
    vocabulary_level: str = "中性"        # 用词层级：口语/中性/书面/学术
    paragraph_opening_style: str = "多样"  # 段首习惯：多样/主语开头/时间状语开头
    rhetorical_devices: List[str] = field(default_factory=list)  # 常用修辞手法

    def to_dict(self) -> Dict:
        return {
            "平均句长": round(self.avg_sentence_length, 1),
            "句长方差": round(self.sentence_length_variance, 1),
            "常用过渡词": self.preferred_transitions[:5],
            "标点偏好": self.punctuation_style,
            "用词层级": self.vocabulary_level,
            "段首习惯": self.paragraph_opening_style,
            "常用修辞": self.rhetorical_devices[:3],
        }


def calibrate_voice(reference_text: str) -> VoiceProfile:
    """从参考文本中提取声纹档案"""
    profile = VoiceProfile()

    # 句长分析
    sentences = re.split(r'[。！？]', reference_text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 2]
    if sentences:
        lengths = [len(s) for s in sentences]
        profile.avg_sentence_length = sum(lengths) / len(lengths)
        avg = profile.avg_sentence_length
        profile.sentence_length_variance = (
            sum((l - avg) ** 2 for l in lengths) / len(lengths)
        )

    # 过渡词频率
    transitions = ["然而", "但是", "不过", "因此", "所以", "于是",
                   "同时", "此外", "另外", "与此同时", "不仅如此",
                   "话说回来", "反过来说", "换句话说"]
    freq = {t: reference_text.count(t) for t in transitions if reference_text.count(t) > 0}
    profile.preferred_transitions = sorted(freq, key=lambda x: freq[x], reverse=True)[:5]

    # 标点偏好
    punctuation_marks = {
        "逗号": reference_text.count('，'),
        "句号": reference_text.count('。'),
        "感叹号": reference_text.count('！'),
        "问号": reference_text.count('？'),
        "省略号": reference_text.count('…'),
        "破折号": reference_text.count('——'),
    }
    total_punct = sum(punctuation_marks.values())
    if total_punct > 0:
        profile.punctuation_style = {
            k: round(v / total_punct, 3)
            for k, v in punctuation_marks.items() if v > 0
        }

    # 用词层级判断
    oral_markers = ["嘛", "呢", "吧", "啊", "呀", "哦", "嗯", "嘿"]
    formal_markers = ["因此", "然而", "鉴于", "基于", "依据"]
    oral_count = sum(reference_text.count(m) for m in oral_markers)
    formal_count = sum(reference_text.count(m) for m in formal_markers)
    if oral_count > formal_count * 2:
        profile.vocabulary_level = "口语"
    elif formal_count > oral_count * 2:
        profile.vocabulary_level = "书面"
    else:
        profile.vocabulary_level = "中性"

    # 段首习惯
    paragraphs = [p.strip() for p in reference_text.split('\n') if p.strip()]
    if len(paragraphs) >= 3:
        first_chars = [p[0] for p in paragraphs[:10]]
        pronoun_starts = sum(1 for c in first_chars if c in "他她我你它她们他们我们你们")
        if pronoun_starts > len(first_chars) * 0.6:
            profile.paragraph_opening_style = "代词开头为主"
        else:
            profile.paragraph_opening_style = "多样"

    return profile


# ═══════════════════════════════════════════════════════════════
# Part 5: 结构模式检测（stop-slop 8类）
# ═══════════════════════════════════════════════════════════════

@dataclass
class StructuralPattern:
    """结构模式检测结果"""
    pattern_name: str
    description: str
    occurrences: int
    severity: str
    fix_hint: str


def detect_structural_patterns(text: str) -> List[StructuralPattern]:
    """检测8类AI结构套路"""
    results = []

    # 1. 二元对立 (Not X, It's Y)
    binary = len(re.findall(r"不是.{2,10}，而是.{2,10}", text))
    if binary > 0:
        results.append(StructuralPattern(
            "二元对立", f"检测到{binary}处'不是X，而是Y'结构",
            binary, "medium", "删除虚假对立，直接陈述观点"
        ))

    # 2. 否定铺垫 (Negative Listing)
    neg_listing = len(re.findall(r"(不只是?|不仅仅是?|并非仅仅).{2,15}(更|还|更是|还是)", text))
    if neg_listing > 0:
        results.append(StructuralPattern(
            "否定铺垫", f"检测到{neg_listing}处否定铺垫结构",
            neg_listing, "medium", "直接说是什么，不要先说什么不是"
        ))

    # 3. 戏剧碎片 (Dramatic Fragmentation)
    fragments = len(re.findall(r'[。！？]\s*\n\s*.{1,10}[。！？]', text))
    if fragments > 3:
        results.append(StructuralPattern(
            "戏剧碎片", f"检测到{fragments}处短句碎片",
            fragments, "medium", "合并碎片句，减少刻意的戏剧效果"
        ))

    # 4. 修辞设置 (Rhetorical Setups)
    rhetorical = len(re.findall(r"(你(可能|或许)会问|那么问题来了|有人可能会说)", text))
    if rhetorical > 0:
        results.append(StructuralPattern(
            "修辞设置", f"检测到{rhetorical}处修辞设置",
            rhetorical, "medium", "删除修辞问句，直接进入正题"
        ))

    # 5. 假主语 (False Agency)
    false_agent = len(re.findall(r"^(有|存在着?|值得注意|需要指出|不可否认)", text, re.MULTILINE))
    if false_agent > 0:
        results.append(StructuralPattern(
            "假主语", f"检测到{false_agent}处假主语",
            false_agent, "medium", "找到真正的施动者做主语"
        ))

    # 6. 远距叙述者 (Narrator-from-a-Distance)
    distant = len(re.findall(r"(在这个|在这片|在这段).{2,10}(中|里|时期|年代)", text))
    if distant > 2:
        results.append(StructuralPattern(
            "远距叙述者", f"检测到{distant}处远距叙述",
            distant, "low", "拉近叙述距离，用第一人称或具体场景切入"
        ))

    # 7. 被动语态过度
    passive = len(re.findall(r"(被|由|让|叫).{1,8}(了|着|过|地|所)", text))
    if passive > 5:
        results.append(StructuralPattern(
            "被动语态过度", f"检测到{passive}处被动语态",
            passive, "medium", "改为主动语态，明确施动者"
        ))

    # 8. 节奏模式（三连、em-dash滥用）
    triple = len(re.findall(r"(.{5,20})[，,]\s*(.{5,20})[，,]\s*(.{5,20})[，,。]", text))
    em_dash = text.count('—') + text.count('——')
    if triple > 2 or em_dash > 5:
        results.append(StructuralPattern(
            "节奏模式", f"三连{triple}处，em-dash{em_dash}处",
            max(triple, em_dash // 2), "medium", "打破节奏规律，增加句式变化"
        ))

    return results


# ═══════════════════════════════════════════════════════════════
# Part 6: 统一检测入口
# ═══════════════════════════════════════════════════════════════

@dataclass
class AIFlavorReport:
    """AI味检测完整报告"""
    pattern_hits: List[AIPattern] = field(default_factory=list)
    quick_check_results: List[QuickCheckResult] = field(default_factory=list)
    structural_patterns: List[StructuralPattern] = field(default_factory=list)
    dimension_score: Optional[DimensionScore] = None
    voice_profile: Optional[VoiceProfile] = None
    total_issues: int = 0
    severity_summary: Dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            "模式检测": {
                "命中数": len(self.pattern_hits),
                "命中详情": [
                    {"分类": p.category, "名称": p.name, "严重度": p.severity}
                    for p in self.pattern_hits
                ],
            },
            "Quick Checks": {
                "总检查数": len(self.quick_check_results),
                "通过数": sum(1 for r in self.quick_check_results if r.passed),
                "未通过": [
                    {"检查": r.check_name, "问题": r.issues, "严重度": r.severity}
                    for r in self.quick_check_results if not r.passed
                ],
            },
            "结构模式": [
                {"名称": p.pattern_name, "次数": p.occurrences, "修复建议": p.fix_hint}
                for p in self.structural_patterns
            ],
            "五维度评分": self.dimension_score.to_dict() if self.dimension_score else None,
            "声纹档案": self.voice_profile.to_dict() if self.voice_profile else None,
            "总问题数": self.total_issues,
            "严重度分布": self.severity_summary,
        }


def detect_ai_flavor(text: str, reference_text: Optional[str] = None) -> AIFlavorReport:
    """
    统一检测入口：对文本进行全面的AI味检测。

    Args:
        text: 待检测文本
        reference_text: 参考文本（用于声纹校准，可选）

    Returns:
        AIFlavorReport: 完整检测报告
    """
    report = AIFlavorReport()

    # 1. 33类AI模式检测
    for pattern in AI_PATTERNS:
        hit = False

        # 正则检测
        for regex in pattern.regex_patterns:
            if re.search(regex, text):
                hit = True
                break

        # 关键词检测
        if not hit and pattern.keywords:
            for kw in pattern.keywords:
                if kw in text:
                    hit = True
                    break

        if hit:
            report.pattern_hits.append(pattern)

    # 2. 12项Quick Checks
    for check_fn in QUICK_CHECKS:
        result = check_fn(text)
        report.quick_check_results.append(result)

    # 3. 8类结构模式检测
    report.structural_patterns = detect_structural_patterns(text)

    # 4. 五维度评分
    report.dimension_score = score_text(text, report.pattern_hits, report.quick_check_results)

    # 5. 声纹校准（可选）
    if reference_text:
        report.voice_profile = calibrate_voice(reference_text)

    # 6. 汇总
    severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for p in report.pattern_hits:
        severity_counts[p.severity] = severity_counts.get(p.severity, 0) + 1
    for r in report.quick_check_results:
        if not r.passed:
            severity_counts[r.severity] = severity_counts.get(r.severity, 0) + 1
    for sp in report.structural_patterns:
        severity_counts[sp.severity] = severity_counts.get(sp.severity, 0) + 1

    report.severity_summary = severity_counts
    report.total_issues = sum(severity_counts.values())

    return report


# ═══════════════════════════════════════════════════════════════
# Part 7: CLI 入口
# ═══════════════════════════════════════════════════════════════

def main():
    """CLI入口：python ai_flavor_engine.py <text_file> [--reference <ref_file>]"""
    import argparse
    import json
    import sys

    parser = argparse.ArgumentParser(description="AI味检测引擎")
    parser.add_argument("text_file", help="待检测文本文件路径")
    parser.add_argument("--reference", help="参考文本文件路径（声纹校准）", default=None)
    parser.add_argument("--format", choices=["json", "text"], default="text", help="输出格式")
    args = parser.parse_args()

    text = open(args.text_file, encoding="utf-8").read()
    ref_text = open(args.reference, encoding="utf-8").read() if args.reference else None

    report = detect_ai_flavor(text, ref_text)

    if args.format == "json":
        print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
    else:
        print(f"\n{'='*60}")
        print(f"AI 味检测报告")
        print(f"{'='*60}")

        print(f"\n📊 五维度评分：")
        if report.dimension_score:
            d = report.dimension_score.to_dict()
            for k, v in d.items():
                if k != "需修订":
                    bar = "█" * int(v) + "░" * (10 - int(v))
                    print(f"  {k}: {bar} {v}/10")
            print(f"  {'需修订':　>6}: {'是 ⚠️' if d['需修订'] else '否 ✅'}")

        print(f"\n🔍 模式检测（{len(report.pattern_hits)}项命中）：")
        for p in report.pattern_hits:
            icon = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}.get(p.severity, "⚪")
            print(f"  {icon} [{p.category}] {p.name}")

        print(f"\n✅ Quick Checks（{sum(1 for r in report.quick_check_results if r.passed)}/{len(report.quick_check_results)}通过）：")
        for r in report.quick_check_results:
            icon = "✅" if r.passed else "❌"
            print(f"  {icon} {r.check_name}")
            for issue in r.issues:
                print(f"     → {issue}")

        print(f"\n🏗️ 结构模式（{len(report.structural_patterns)}项）：")
        for sp in report.structural_patterns:
            print(f"  ⚠️ {sp.pattern_name}: {sp.description}")
            print(f"     → {sp.fix_hint}")

        if report.voice_profile:
            print(f"\n🎤 声纹档案：")
            v = report.voice_profile.to_dict()
            for k, val in v.items():
                print(f"  {k}: {val}")

        print(f"\n📈 总计: {report.total_issues}个问题")
        print(f"  严重度分布: {report.severity_summary}")


if __name__ == "__main__":
    main()
