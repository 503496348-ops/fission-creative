"""
Parallel Researcher — multi-source parallel search with aggregation.
Inspired by GPT-Researcher's parallelized execution agents.

Searches multiple sources simultaneously, deduplicates results,
ranks by relevance, and aggregates into structured findings.
"""

import time
import hashlib
import logging
from dataclasses import dataclass, field
from typing import Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class Source:
    """A research source with metadata."""
    url: str
    title: str
    snippet: str
    full_text: Optional[str] = None
    relevance_score: float = 0.0
    domain: str = ""
    published_date: Optional[str] = None
    source_type: str = "web"  # web | paper | doc | api

    @property
    def content_hash(self) -> str:
        content = f"{self.title}{self.snippet}"
        return hashlib.md5(content.encode()).hexdigest()[:12]

    def to_dict(self) -> dict:
        return {
            "url": self.url,
            "title": self.title,
            "snippet": self.snippet,
            "relevance": self.relevance_score,
            "domain": self.domain,
            "type": self.source_type,
        }


@dataclass
class ResearchResult:
    """Aggregated research results for a query."""
    query: str
    sources: list[Source] = field(default_factory=list)
    summary: str = ""
    key_findings: list[str] = field(default_factory=list)
    search_time: float = 0.0

    def top_sources(self, n: int = 5) -> list[Source]:
        return sorted(self.sources, key=lambda s: s.relevance_score, reverse=True)[:n]


class SearchProvider:
    """Base class for search providers."""

    def search(self, query: str, num_results: int = 5) -> list[Source]:
        raise NotImplementedError


class WebSearchProvider(SearchProvider):
    """Web search using Hermes web_search tool."""

    def search(self, query: str, num_results: int = 5) -> list[Source]:
        from hermes_tools import web_search
        try:
            results = web_search(query, limit=num_results)
            sources = []
            for item in results.get("data", {}).get("web", []):
                sources.append(Source(
                    url=item.get("url", ""),
                    title=item.get("title", ""),
                    snippet=item.get("description", ""),
                    domain=self._extract_domain(item.get("url", "")),
                ))
            return sources
        except Exception as e:
            logger.warning(f"Web search failed for '{query}': {e}")
            return []

    def _extract_domain(self, url: str) -> str:
        try:
            from urllib.parse import urlparse
            return urlparse(url).netloc.replace("www.", "")
        except:
            return ""


class DocumentSearchProvider(SearchProvider):
    """Local document search."""

    def __init__(self, doc_paths: list[str]):
        self.doc_paths = doc_paths

    def search(self, query: str, num_results: int = 5) -> list[Source]:
        from hermes_tools import search_files
        sources = []
        for path in self.doc_paths:
            try:
                results = search_files(query, path=path, limit=num_results)
                for match in results.get("matches", []):
                    sources.append(Source(
                        url=match.get("path", ""),
                        title=match.get("path", "").split("/")[-1],
                        snippet=match.get("content", "")[:200],
                        source_type="doc",
                    ))
            except Exception:
                continue
        return sources[:num_results]


class ParallelResearcher:
    """
    Executes parallel searches across multiple providers and queries.

    Features:
    - Concurrent search across multiple providers
    - Result deduplication by content hash
    - Relevance scoring and ranking
    - Source aggregation and summarization
    """

    def __init__(
        self,
        providers: Optional[list[SearchProvider]] = None,
        max_workers: int = 4,
        dedup_threshold: float = 0.8,
    ):
        self.providers = providers or [WebSearchProvider()]
        self.max_workers = max_workers
        self.dedup_threshold = dedup_threshold

    def research(
        self,
        queries: list[str],
        results_per_query: int = 5,
        extract_content: bool = False,
    ) -> list[ResearchResult]:
        """
        Execute parallel research across all queries and providers.

        Args:
            queries: List of search queries
            results_per_query: Number of results per query per provider
            extract_content: Whether to extract full page content

        Returns:
            List of ResearchResult, one per query
        """
        results = []

        with ThreadPoolExecutor(max_workers=self.max_workers) as pool:
            futures = {}
            for query in queries:
                for provider in self.providers:
                    future = pool.submit(
                        self._search_single, query, provider, results_per_query
                    )
                    futures[future] = query

            # Group results by query
            query_sources: dict[str, list[Source]] = defaultdict(list)
            for future in as_completed(futures):
                query = futures[future]
                try:
                    sources = future.result()
                    query_sources[query].extend(sources)
                except Exception as e:
                    logger.error(f"Search failed for '{query}': {e}")

        # Process each query's results
        for query in queries:
            sources = query_sources.get(query, [])
            start = time.time()

            # Deduplicate
            sources = self._deduplicate(sources)

            # Score relevance
            sources = self._score_relevance(query, sources)

            # Extract content if requested
            if extract_content:
                sources = self._extract_content(sources)

            result = ResearchResult(
                query=query,
                sources=sources,
                search_time=time.time() - start,
            )

            # Generate key findings
            result.key_findings = self._extract_findings(result)

            results.append(result)

        return results

    def _search_single(
        self, query: str, provider: SearchProvider, num_results: int
    ) -> list[Source]:
        """Execute a single search."""
        return provider.search(query, num_results)

    def _deduplicate(self, sources: list[Source]) -> list[Source]:
        """Remove duplicate sources by content hash."""
        seen: set[str] = set()
        unique = []
        for source in sources:
            h = source.content_hash
            if h not in seen:
                seen.add(h)
                unique.append(source)
        return unique

    def _score_relevance(self, query: str, sources: list[Source]) -> list[Source]:
        """Score and rank sources by relevance to query."""
        query_terms = set(query.lower().split())

        for source in sources:
            score = 0.0
            text = f"{source.title} {source.snippet}".lower()

            # Term overlap
            term_hits = sum(1 for t in query_terms if t in text)
            score += (term_hits / max(len(query_terms), 1)) * 0.6

            # Title match bonus
            if any(t in source.title.lower() for t in query_terms):
                score += 0.2

            # Domain authority heuristic
            trusted_domains = {"arxiv.org", "github.com", "nature.com", "science.org", "ieee.org"}
            if source.domain in trusted_domains:
                score += 0.2

            source.relevance_score = min(score, 1.0)

        return sorted(sources, key=lambda s: s.relevance_score, reverse=True)

    def _extract_content(self, sources: list[Source]) -> list[Source]:
        """Extract full page content for top sources."""
        from hermes_tools import web_extract
        top = [s for s in sources if s.relevance_score > 0.3][:3]
        urls = [s.url for s in top if s.url.startswith("http")]

        if not urls:
            return sources

        try:
            results = web_extract(urls)
            url_content = {
                r["url"]: r.get("content", "")
                for r in results.get("results", [])
            }
            for source in sources:
                if source.url in url_content:
                    source.full_text = url_content[source.url][:5000]
        except Exception as e:
            logger.warning(f"Content extraction failed: {e}")

        return sources

    def _extract_findings(self, result: ResearchResult) -> list[str]:
        """Extract key findings from top sources."""
        findings = []
        for source in result.top_sources(3):
            if source.snippet:
                findings.append(f"[{source.title}] {source.snippet[:150]}")
        return findings

    def aggregate_all(self, results: list[ResearchResult]) -> dict[str, Any]:
        """Aggregate all research results into a single structured output."""
        all_sources = []
        all_findings = []
        for r in results:
            all_sources.extend(r.sources)
            all_findings.extend(r.key_findings)

        # Deduplicate across queries
        seen = set()
        unique_sources = []
        for s in all_sources:
            if s.content_hash not in seen:
                seen.add(s.content_hash)
                unique_sources.append(s)

        return {
            "total_queries": len(results),
            "total_sources": len(unique_sources),
            "top_sources": [s.to_dict() for s in sorted(unique_sources, key=lambda x: x.relevance_score, reverse=True)[:10]],
            "key_findings": all_findings[:15],
            "domains_covered": list(set(s.domain for s in unique_sources if s.domain)),
        }
