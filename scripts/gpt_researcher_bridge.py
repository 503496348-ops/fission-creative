#!/usr/bin/env python3
"""gpt-researcher bridge diagnostics for fission-creative.

This module validates that the long-form research pipeline can be invoked with:
- research plan generation
- parallel/iterative source collection
- evidence hardening and source scoring
- report serialization

It is intentionally lightweight and deterministic in sample mode so it can run in
fresh clones without external network dependencies.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from deep_research import DeepResearchEngine
from modules.research.evidence_hardening import build_evidence_pack


def _make_sample_llm():
    """Return a deterministic LLM stub that matches parser expectations."""

    def _llm(prompt: str) -> str:
        p = prompt.lower()
        if "Generate" in prompt and "search queries" in p:
            return "[\"%s 技术要点\", \"%s 商业模式\", \"%s 论文资料\"]" % ("topic", "topic", "topic")
        if "Extract key learnings" in prompt:
            return (
                "- Learning: 首先定义研究边界。\n"
                "- Learning: 建立可复现的来源审计链。\n"
                "- Learning: 证据需带来源和命中时间。"
            )
        if "knowledge gaps" in p or "what knowledge gaps" in p:
            return "- Gap: 缺少对权威论文的横向比较。\n- Gap: 需补齐发布时间线。"
        if "Generate a structured outline" in prompt:
            return (
                '{"title": "研究报告", "sections": ['
                '{"heading": "背景", "subsections": ["定义与边界"], "key_points": ["定义指标", "确认口径"]},'
                '{"heading": "分析", "subsections": ["来源审计", "证据链"], "key_points": ["来源权重", "风险识别"]},'
                '{"heading": "结论", "subsections": ["行动建议"], "key_points": ["可执行动作"]}'
                '], "estimated_words": 2500}'
            )
        if "select the TOP" in prompt:
            return '["可信来源优先", "来源间闭环", "报告可追溯"]'
        return "- Learning: sample response"

    return _llm


def _make_sample_search(topic: str):
    """Return stable sample search results for each query."""

    def _search(query: str) -> list[dict[str, str]]:
        return [
            {
                "url": f"https://arxiv.org/search/sample?topic={topic}",
                "title": f"{query} 论文资料",
                "snippet": f"关于 {query} 的高质量论文摘要与实现细节。",
            },
            {
                "url": f"https://github.com/sample/{topic.replace(' ', '-')}",
                "title": f"{query} 开源实践",
                "snippet": f"{query} 在开源仓库中的可复用实现与案例。",
            },
        ]

    return _search


def _run_bridge(topic: str, *, sample: bool = False) -> dict[str, Any]:
    llm = _make_sample_llm() if sample else None
    search = _make_sample_search(topic) if sample else None

    engine = DeepResearchEngine(llm_func=llm, search_func=search)
    result = engine.research(topic=topic, max_rounds=2)

    evidence_input = [
        {
            "title": source.title,
            "url": source.url,
            "text": source.snippet,
        }
        for source in result.all_sources
    ]
    evidence_cards = build_evidence_pack(evidence_input)
    top_sources = [
        {
            "url": source.url,
            "title": source.title,
            "score": source.score,
            "domain": source.domain,
            "snippet": source.snippet,
        }
        for source in result.all_sources[:5]
    ]

    payload = {
        "bridge": "ok",
        "topic": topic,
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "rounds": len(result.rounds),
        "queries_total": result.total_queries,
        "sources_total": result.total_sources,
        "context_words": result.context_words,
        "top_sources": top_sources,
        "outline_sections": len(result.outline.get("sections", [])),
        "estimated_words": result.outline.get("estimated_words"),
        "evidence_cards": [card.to_dict() for card in evidence_cards],
    }
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="fission-creative ↔ gpt-researcher bridge diagnostics")
    parser.add_argument("--topic", default="fission creative deep research")
    parser.add_argument("--sample", action="store_true", help="Use deterministic local sample mode")
    parser.add_argument("--json", action="store_true", help="Output JSON payload")
    args = parser.parse_args()

    payload = _run_bridge(args.topic, sample=args.sample)

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print("[gpt-researcher bridge] rounds=%s queries=%s sources=%s" % (
            payload["rounds"], payload["queries_total"], payload["sources_total"]
        ))
        print("outline_sections=%s" % payload["outline_sections"])
        print("evidence_cards=%s" % len(payload["evidence_cards"]))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
