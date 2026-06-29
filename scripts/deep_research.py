# -*- coding: utf-8 -*-
"""
裂变创作-Fission Creative · Deep Research Engine
AtomCollide-智械工坊 · 2026


能力:
  - DR1: 多查询扩展 (1个主题→N个搜索子查询)
  - DR2: 迭代式搜索→反思→再搜索循环
  - DR3: 来源可信度评估与排序
  - DR4: 结构化大纲生成 (自动分章分节)
  - DR5: 上下文预算管理 (防止token溢出)

Usage:
    from deep_research import DeepResearchEngine
    engine = DeepResearchEngine()
    result = engine.research("AI Agent安全检测框架发展趋势")
"""

import re
import json
import time
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Any, Set
from datetime import datetime, timezone


# ── 常量 ──

MAX_CONTEXT_WORDS = 25000
MAX_QUERIES_PER_ROUND = 5
MAX_ROUNDS = 3
MIN_SOURCES = 3

# URL提取
URL_PATTERN = re.compile(r"https?://[^\s\]\)>\",;]+")

# 查询行模式
QUERY_LINE_PATTERN = re.compile(
    r"^(?:[-*]|\d+[.)])?\s*Query:\s*(?P<query>.+)$", re.IGNORECASE
)
LEARNING_LINE_PATTERN = re.compile(
    r"^(?:[-*]|\d+[.)])?\s*Learning(?:\s*\[(?P<citation>[^\]]+)\])?:\s*(?P<learning>.+)$",
    re.IGNORECASE,
)


@dataclass
class Source:
    """研究来源"""
    url: str
    title: str = ""
    snippet: str = ""
    credibility: float = 0.5  # 0-1
    relevance: float = 0.5  # 0-1
    domain: str = ""
    accessed_at: str = ""

    @property
    def score(self) -> float:
        return self.credibility * 0.6 + self.relevance * 0.4


@dataclass
class ResearchQuery:
    """单次搜索查询"""
    query: str
    round_num: int = 1
    purpose: str = ""  # background/deep/context/verification
    results_count: int = 0


@dataclass
class ResearchRound:
    """一轮研究"""
    round_num: int
    queries: List[ResearchQuery]
    sources_found: List[Source]
    learnings: List[str]
    gaps_identified: List[str]
    duration_sec: float = 0.0


@dataclass
class ResearchResult:
    """研究结果"""
    topic: str
    rounds: List[ResearchRound]
    all_sources: List[Source]
    outline: Dict[str, Any]
    key_findings: List[str]
    total_queries: int
    total_sources: int
    total_duration_sec: float
    context_words: int

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False, default=str)


# ── 域名可信度 ──

DOMAIN_CREDIBILITY: Dict[str, float] = {
    "arxiv.org": 0.95,
    "github.com": 0.90,
    "nature.com": 0.95,
    "science.org": 0.95,
    "ieee.org": 0.90,
    "acm.org": 0.90,
    "scholar.google.com": 0.85,
    "wikipedia.org": 0.70,
    "medium.com": 0.50,
    "reddit.com": 0.40,
    "twitter.com": 0.30,
    "zhihu.com": 0.55,
    "csdn.net": 0.45,
    "juejin.cn": 0.50,
    "segmentfault.com": 0.55,
    "stackoverflow.com": 0.75,
    "docs.python.org": 0.95,
    "docs.microsoft.com": 0.85,
    "cloud.google.com": 0.85,
    "aws.amazon.com": 0.85,
}


def _extract_domain(url: str) -> str:
    """从URL提取域名"""
    match = re.search(r"https?://(?:www\.)?([^/]+)", url)
    return match.group(1) if match else ""


def _assess_credibility(url: str) -> float:
    """评估URL可信度"""
    domain = _extract_domain(url)
    for known, score in DOMAIN_CREDIBILITY.items():
        if known in domain:
            return score
    # Default heuristic
    if domain.endswith(".edu") or domain.endswith(".gov"):
        return 0.85
    if domain.endswith(".org"):
        return 0.70
    return 0.50


class DeepResearchEngine:
    """深度研究引擎"""

    def __init__(self, llm_func=None, search_func=None):
        """
        Args:
            llm_func: LLM调用函数 (prompt: str) -> str
            search_func: 搜索函数 (query: str) -> List[dict]
        """
        self.llm = llm_func or self._mock_llm
        self.search = search_func or self._mock_search

    def _mock_llm(self, prompt: str) -> str:
        """Mock LLM for testing"""
        return f"[Mock LLM] Analysis of: {prompt[:100]}..."

    def _mock_search(self, query: str) -> List[dict]:
        """Mock search for testing"""
        return [
            {"url": f"https://example.com/result{i}", "title": f"Result {i} for {query}",
             "snippet": f"This is a relevant result about {query}"}
            for i in range(3)
        ]

    # ── DR1: 多查询扩展 ──

    def expand_queries(self, topic: str, num_queries: int = MAX_QUERIES_PER_ROUND,
                       context: str = "") -> List[str]:
        """
        将一个主题扩展为多个搜索查询。

        Args:
            topic: 研究主题
            num_queries: 期望查询数
            context: 已有上下文（避免重复）

        Returns:
            扩展后的查询列表
        """
        prompt = f"""Generate {num_queries} diverse search queries for deep research on: "{topic}"

{f'Already covered (avoid duplicates): {context[:500]}' if context else ''}

Requirements:
- Cover different angles: technical, market, academic, practical, comparative
- Each query should be specific and searchable
- Return as JSON array of strings

Example format:
["query 1", "query 2", "query 3"]"""

        response = self.llm(prompt)

        # Parse response
        try:
            # Try JSON parse
            queries = json.loads(response)
            if isinstance(queries, list):
                return [str(q) for q in queries[:num_queries]]
        except json.JSONDecodeError:
            pass

        # Fallback: extract from lines
        queries = []
        for line in response.split("\n"):
            line = line.strip()
            if line.startswith(("- ", "* ", "1.", "2.", "3.", "4.", "5.")):
                q = re.sub(r"^[-*\d.)\s]+", "", line).strip()
                if q and len(q) > 5:
                    queries.append(q)

        return queries[:num_queries] if queries else [topic]

    # ── DR2: 迭代研究循环 ──

    def research(self, topic: str, max_rounds: int = MAX_ROUNDS) -> ResearchResult:
        """
        对主题进行迭代式深度研究。

        Args:
            topic: 研究主题
            max_rounds: 最大研究轮数

        Returns:
            完整研究结果
        """
        start_time = time.time()
        rounds: List[ResearchRound] = []
        all_sources: List[Source] = []
        all_learnings: List[str] = []
        covered_context = ""

        for round_num in range(1, max_rounds + 1):
            round_start = time.time()

            # Expand queries
            if round_num == 1:
                queries_str = self.expand_queries(topic, context=covered_context)
            else:
                # Use gaps from previous round to guide new queries
                prev_gaps = rounds[-1].gaps_identified if rounds else []
                gap_context = " ".join(prev_gaps) if prev_gaps else ""
                queries_str = self.expand_queries(topic, context=f"{covered_context}\nGaps: {gap_context}")

            queries = [ResearchQuery(query=q, round_num=round_num) for q in queries_str]

            # Execute searches
            round_sources: List[Source] = []
            round_learnings: List[str] = []

            for rq in queries:
                results = self.search(rq.query)
                rq.results_count = len(results)

                for r in results:
                    url = r.get("url", "")
                    source = Source(
                        url=url,
                        title=r.get("title", ""),
                        snippet=r.get("snippet", "")[:500],
                        credibility=_assess_credibility(url),
                        domain=_extract_domain(url),
                        accessed_at=datetime.now(timezone.utc).isoformat(),
                    )
                    round_sources.append(source)

                # Extract learnings from snippets
                snippets = [r.get("snippet", "") for r in results if r.get("snippet")]
                if snippets:
                    combined = " | ".join(snippets)[:2000]
                    learning_prompt = f"""Extract key learnings from these search results about "{rq.query}":
{combined}

Format: bullet points, each starting with "- Learning: "
Focus on facts, data points, and actionable insights."""

                    learning_response = self.llm(learning_prompt)
                    for line in learning_response.split("\n"):
                        m = LEARNING_LINE_PATTERN.match(line.strip())
                        if m:
                            round_learnings.append(m.group("learning"))

            # Identify gaps
            gap_prompt = (
                f"Based on research on '{topic}' (round {round_num}), what knowledge gaps remain?\n\n"
                f"Current findings:\n"
                + "\n".join("- " + l for l in round_learnings[:10])
                + "\n\nIdentify 3-5 specific questions that still need answers.\n"
                "Format: bullet points, each starting with 'Gap: '"
            )

            gap_response = self.llm(gap_prompt)
            gaps = []
            for line in gap_response.split("\n"):
                line = line.strip()
                if line.startswith(("- Gap:", "* Gap:")):
                    gaps.append(line.split(":", 1)[1].strip())

            # Deduplicate sources
            seen_urls: Set[str] = {s.url for s in all_sources}
            new_sources = [s for s in round_sources if s.url not in seen_urls]
            all_sources.extend(new_sources)
            all_learnings.extend(round_learnings)
            covered_context += " " + " ".join(round_learnings[:5])

            research_round = ResearchRound(
                round_num=round_num,
                queries=queries,
                sources_found=new_sources,
                learnings=round_learnings,
                gaps_identified=gaps,
                duration_sec=time.time() - round_start,
            )
            rounds.append(research_round)

            # Early termination if no new gaps
            if not gaps and round_num > 1:
                break

        # Generate outline
        outline = self._generate_outline(topic, all_learnings)

        # Key findings
        key_findings = self._extract_key_findings(topic, all_learnings)

        return ResearchResult(
            topic=topic,
            rounds=rounds,
            all_sources=sorted(all_sources, key=lambda s: s.score, reverse=True),
            outline=outline,
            key_findings=key_findings,
            total_queries=sum(len(r.queries) for r in rounds),
            total_sources=len(all_sources),
            total_duration_sec=time.time() - start_time,
            context_words=len(covered_context.split()),
        )

    # ── DR4: 结构化大纲生成 ──

    def _generate_outline(self, topic: str, learnings: List[str]) -> Dict[str, Any]:
        """从研究成果生成结构化大纲"""
        learnings_text = "\n".join(f"- {l}" for l in learnings[:20])

        prompt = f"""Generate a structured outline for a comprehensive article about: "{topic}"

Key findings from research:
{learnings_text}

Return as JSON:
{{
  "title": "Article title",
  "sections": [
    {{"heading": "Section 1", "subsections": ["Sub 1.1", "Sub 1.2"], "key_points": ["point 1"]}},
    {{"heading": "Section 2", "subsections": [], "key_points": []}}
  ],
  "estimated_words": 3000
}}"""

        response = self.llm(prompt)
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {
                "title": topic,
                "sections": [
                    {"heading": "概述", "subsections": [], "key_points": learnings[:3]},
                    {"heading": "核心分析", "subsections": [], "key_points": learnings[3:6]},
                    {"heading": "结论与展望", "subsections": [], "key_points": learnings[6:9]},
                ],
                "estimated_words": 3000,
            }

    # ── DR3: 来源排序 ──

    def _extract_key_findings(self, topic: str, learnings: List[str]) -> List[str]:
        """提取关键发现"""
        if not learnings:
            return []

        prompt = f"""From these research findings about "{topic}", select the TOP 5 most important:

{chr(10).join('- ' + l for l in learnings[:30])}

Return as JSON array of strings, each being a concise key finding."""

        response = self.llm(prompt)
        try:
            findings = json.loads(response)
            if isinstance(findings, list):
                return [str(f) for f in findings[:5]]
        except json.JSONDecodeError:
            pass

        return learnings[:5]

    # ── 格式化输出 ──

    def format_report(self, result: ResearchResult) -> str:
        """格式化研究结果为可读报告"""
        lines = [
            f"📊 深度研究报告: {result.topic}",
            f"⏱️ 耗时: {result.total_duration_sec:.1f}秒 | 轮数: {len(result.rounds)} | "
            f"查询: {result.total_queries} | 来源: {result.total_sources}",
            "",
        ]

        # Key findings
        if result.key_findings:
            lines.append("🔑 关键发现:")
            for i, f in enumerate(result.key_findings, 1):
                lines.append(f"  {i}. {f}")
            lines.append("")

        # Outline
        if result.outline and result.outline.get("sections"):
            lines.append(f"📝 建议大纲: {result.outline.get('title', result.topic)}")
            for i, sec in enumerate(result.outline["sections"], 1):
                lines.append(f"  {i}. {sec['heading']}")
                for sub in sec.get("subsections", []):
                    lines.append(f"     - {sub}")
            lines.append("")

        # Top sources
        top_sources = sorted(result.all_sources, key=lambda s: s.score, reverse=True)[:5]
        if top_sources:
            lines.append("📚 Top来源:")
            for s in top_sources:
                lines.append(f"  [{s.score:.2f}] {s.title or s.url} ({s.domain})")

        return "\n".join(lines)


# ── CLI ──

if __name__ == "__main__":
    import sys
    topic = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "AI Agent安全检测框架"
    engine = DeepResearchEngine()
    result = engine.research(topic, max_rounds=2)
    print(engine.format_report(result))
