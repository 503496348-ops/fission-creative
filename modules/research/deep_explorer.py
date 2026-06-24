"""
Deep Explorer — recursive tree-like topic exploration.
Inspired by GPT-Researcher's deep research mode.

Recursively explores sub-topics, building a knowledge tree
with breadth-first and depth-first hybrid traversal.
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Optional
from collections import deque

logger = logging.getLogger(__name__)


@dataclass
class ExplorationNode:
    """A node in the knowledge exploration tree."""
    topic: str
    depth: int
    findings: list[str] = field(default_factory=list)
    sources: list[dict] = field(default_factory=list)
    children: list["ExplorationNode"] = field(default_factory=list)
    explored: bool = False
    importance: float = 0.5  # 0-1

    @property
    def leaf_count(self) -> int:
        if not self.children:
            return 1
        return sum(c.leaf_count for c in self.children)

    def to_dict(self) -> dict:
        return {
            "topic": self.topic,
            "depth": self.depth,
            "findings": self.findings,
            "sources": self.sources,
            "importance": self.importance,
            "children": [c.to_dict() for c in self.children],
        }


class DeepExplorer:
    """
    Recursive topic explorer that builds a knowledge tree.

    Strategy:
    - Breadth-first at low depths (cover the landscape)
    - Depth-first at high depths (drill into specifics)
    - Importance-based pruning (skip low-value branches)
    - Cycle detection (don't revisit explored topics)
    """

    def __init__(
        self,
        search_fn: Optional[callable] = None,
        analyze_fn: Optional[callable] = None,
        max_depth: int = 3,
        max_breadth: int = 3,
        min_importance: float = 0.3,
    ):
        self.search_fn = search_fn or self._default_search
        self.analyze_fn = analyze_fn or self._default_analyze
        self.max_depth = max_depth
        self.max_breadth = max_breadth
        self.min_importance = min_importance
        self._visited: set[str] = set()
        self._total_nodes = 0

    def explore(self, topic: str) -> ExplorationNode:
        """
        Start deep exploration from a root topic.

        Returns:
            Root ExplorationNode with full knowledge tree.
        """
        self._visited.clear()
        self._total_nodes = 0

        root = ExplorationNode(topic=topic, depth=0)
        self._explore_node(root)

        logger.info(f"Exploration complete: {self._total_nodes} nodes, "
                    f"{root.leaf_count} leaves")
        return root

    def _explore_node(self, node: ExplorationNode) -> None:
        """Recursively explore a node and its sub-topics."""
        if node.depth >= self.max_depth:
            return
        if node.topic.lower() in self._visited:
            return
        if self._total_nodes > 50:  # safety limit
            return

        self._visited.add(node.topic.lower())
        self._total_nodes += 1

        logger.info(f"{'  ' * node.depth}Exploring: {node.topic} (depth={node.depth})")

        # Search for information
        search_results = self.search_fn(node.topic)
        node.findings = search_results.get("findings", [])
        node.sources = search_results.get("sources", [])

        if not node.findings:
            node.explored = True
            return

        # Analyze and discover sub-topics
        sub_topics = self.analyze_fn(node.topic, node.findings)

        # Score and filter sub-topics
        scored_topics = []
        for st in sub_topics:
            if isinstance(st, dict):
                topic = st.get("topic", "")
                importance = st.get("importance", 0.5)
            else:
                topic = str(st)
                importance = 0.5

            if topic.lower() not in self._visited and importance >= self.min_importance:
                scored_topics.append((topic, importance))

        # Sort by importance, take top N
        scored_topics.sort(key=lambda x: x[1], reverse=True)
        for topic, importance in scored_topics[:self.max_breadth]:
            child = ExplorationNode(
                topic=topic,
                depth=node.depth + 1,
                importance=importance,
            )
            node.children.append(child)
            self._explore_node(child)

        node.explored = True

    def _default_search(self, topic: str) -> dict:
        """Default search using Hermes web_search."""
        try:
            from hermes_tools import web_search, web_extract
            results = web_search(topic, limit=3)
            findings = []
            sources = []
            for item in results.get("data", {}).get("web", []):
                findings.append(item.get("description", ""))
                sources.append({"url": item.get("url", ""), "title": item.get("title", "")})
            return {"findings": findings, "sources": sources}
        except Exception as e:
            logger.warning(f"Search failed for '{topic}': {e}")
            return {"findings": [], "sources": []}

    def _default_analyze(self, topic: str, findings: list[str]) -> list[dict]:
        """Default sub-topic discovery using keyword extraction."""
        # Simple heuristic: look for capitalized terms and quoted phrases
        import re
        sub_topics = []
        seen = set()

        for finding in findings:
            # Extract capitalized multi-word terms
            caps = re.findall(r'[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+', finding)
            for cap in caps:
                clean = cap.strip()
                if clean.lower() not in seen and clean.lower() != topic.lower():
                    seen.add(clean.lower())
                    sub_topics.append({"topic": clean, "importance": 0.5})

            # Extract quoted terms
            quoted = re.findall(r'"([^"]+)"', finding)
            for q in quoted:
                if q.lower() not in seen and len(q) > 3:
                    seen.add(q.lower())
                    sub_topics.append({"topic": q, "importance": 0.4})

        return sub_topics[:5]

    def flatten_tree(self, root: ExplorationNode) -> list[dict]:
        """Flatten the tree into a list of all nodes with their paths."""
        flat = []

        def _walk(node: ExplorationNode, path: list[str]) -> None:
            current_path = path + [node.topic]
            flat.append({
                "topic": node.topic,
                "depth": node.depth,
                "path": " → ".join(current_path),
                "findings": node.findings,
                "sources": node.sources,
                "importance": node.importance,
                "is_leaf": len(node.children) == 0,
            })
            for child in node.children:
                _walk(child, current_path)

        _walk(root, [])
        return flat

    def collect_all_findings(self, root: ExplorationNode) -> dict[str, Any]:
        """Collect all findings from the tree into a structured report."""
        flat = self.flatten_tree(root)

        all_findings = []
        all_sources = []
        for node in flat:
            all_findings.extend(node["findings"])
            all_sources.extend(node["sources"])

        # Deduplicate sources by URL
        seen_urls = set()
        unique_sources = []
        for s in all_sources:
            url = s.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_sources.append(s)

        return {
            "topic": root.topic,
            "total_nodes": len(flat),
            "total_findings": len(all_findings),
            "unique_sources": len(unique_sources),
            "max_depth": max(n["depth"] for n in flat) if flat else 0,
            "tree": root.to_dict(),
            "all_sources": unique_sources[:20],
        }
