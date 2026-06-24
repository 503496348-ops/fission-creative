"""
Report Publisher — structured report generation with citations.
Inspired by GPT-Researcher's Publisher Agent.

Aggregates research findings into professional reports with
proper citation tracking, section organization, and multiple
output formats (markdown, HTML, JSON).
"""

import json
import re
import time
import logging
from dataclasses import dataclass, field
from typing import Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class Citation:
    """A numbered citation with source info."""
    id: int
    url: str
    title: str
    access_date: str = ""
    domain: str = ""

    def __post_init__(self):
        if not self.access_date:
            self.access_date = datetime.now().strftime("%Y-%m-%d")

    def markdown(self) -> str:
        return f"[{self.id}] {self.title}. {self.url} (accessed {self.access_date})"


@dataclass
class ReportSection:
    """A section of the report."""
    heading: str
    level: int  # 1=h1, 2=h2, etc.
    content: str = ""
    citations: list[int] = field(default_factory=list)  # citation IDs
    subsections: list["ReportSection"] = field(default_factory=list)

    def markdown(self) -> str:
        prefix = "#" * self.level
        lines = [f"{prefix} {self.heading}", ""]

        if self.content:
            # Add citation markers
            content = self.content
            for cid in self.citations:
                content = content.replace(f"[{cid}]", f"[[{cid}]]")
            lines.append(content)
            lines.append("")

        for sub in self.subsections:
            lines.append(sub.markdown())

        return "\n".join(lines)


@dataclass
class Report:
    """A complete research report."""
    title: str
    topic: str
    sections: list[ReportSection] = field(default_factory=list)
    citations: list[Citation] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()

    def markdown(self) -> str:
        """Generate full markdown report."""
        lines = [
            f"# {self.title}",
            "",
            f"**Topic:** {self.topic}",
            f"**Generated:** {self.created_at}",
            f"**Sources:** {len(self.citations)}",
            "",
            "---",
            "",
        ]

        # Table of contents
        lines.append("## Table of Contents")
        lines.append("")
        for i, section in enumerate(self.sections, 1):
            lines.append(f"{i}. {section.heading}")
            for j, sub in enumerate(section.subsections):
                lines.append(f"  {i}.{j+1} {sub.heading}")
        lines.append("")
        lines.append("---")
        lines.append("")

        # Body
        for section in self.sections:
            lines.append(section.markdown())

        # References
        lines.append("## References")
        lines.append("")
        for cite in self.citations:
            lines.append(cite.markdown())

        return "\n".join(lines)

    def html(self) -> str:
        """Generate HTML report."""
        md = self.markdown()
        # Basic markdown to HTML
        html = md
        html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.M)
        html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.M)
        html = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html, flags=re.M)
        html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
        html = re.sub(r'\n\n', '</p><p>', html)
        html = f"<html><body><p>{html}</p></body></html>"
        return html

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "topic": self.topic,
            "sections": [
                {"heading": s.heading, "content": s.content, "citations": s.citations}
                for s in self.sections
            ],
            "citations": [
                {"id": c.id, "url": c.url, "title": c.title}
                for c in self.citations
            ],
            "metadata": self.metadata,
            "created_at": self.created_at,
        }


class ReportPublisher:
    """
    Aggregates research findings into structured reports.

    Features:
    - Citation deduplication and numbering
    - Section-based organization from research plan outline
    - Multiple output formats (markdown, HTML, JSON)
    - Inline citation insertion
    """

    def __init__(self, write_fn: Optional[callable] = None):
        self.write_fn = write_fn
        self._citation_map: dict[str, int] = {}  # url -> citation ID
        self._next_cite_id = 1

    def publish(
        self,
        topic: str,
        outline: list[str],
        findings: list[dict],
        sources: list[dict],
        title: Optional[str] = None,
    ) -> Report:
        """
        Generate a structured report from research findings.

        Args:
            topic: Research topic
            outline: Document outline (section headings)
            findings: List of finding dicts with text and source info
            sources: List of source dicts with url, title, snippet
            title: Report title (defaults to topic)

        Returns:
            Complete Report object
        """
        report = Report(
            title=title or f"Research Report: {topic}",
            topic=topic,
        )

        # Build citation index
        self._build_citations(sources, report)

        # Parse outline into sections
        sections = self._outline_to_sections(outline, findings)
        report.sections = sections

        # Add metadata
        report.metadata = {
            "total_findings": len(findings),
            "total_sources": len(sources),
            "unique_citations": len(report.citations),
            "sections": len(sections),
        }

        return report

    def _build_citations(self, sources: list[dict], report: Report) -> None:
        """Build deduplicated citation list from sources."""
        for source in sources:
            url = source.get("url", "")
            if not url or url in self._citation_map:
                continue

            cite = Citation(
                id=self._next_cite_id,
                url=url,
                title=source.get("title", url),
                domain=self._extract_domain(url),
            )
            report.citations.append(cite)
            self._citation_map[url] = self._next_cite_id
            self._next_cite_id += 1

    def _outline_to_sections(
        self, outline: list[str], findings: list[dict]
    ) -> list[ReportSection]:
        """Convert outline lines into structured sections with content."""
        sections: list[ReportSection] = []
        current_section: Optional[ReportSection] = None
        current_sub: Optional[ReportSection] = None

        finding_idx = 0

        for line in outline:
            line = line.strip()
            if not line:
                continue

            if line.startswith("# ") and not line.startswith("## "):
                continue  # Skip the title (already in report.title)

            if line.startswith("## "):
                heading = line[3:].strip()
                current_section = ReportSection(heading=heading, level=2)
                sections.append(current_section)
                current_sub = None

                # Assign findings to this section
                if finding_idx < len(findings):
                    relevant = self._find_relevant_findings(heading, findings[finding_idx:])
                    content_parts = []
                    for f in relevant[:3]:
                        text = f.get("text", f.get("snippet", ""))
                        url = f.get("url", "")
                        if text:
                            cite_id = self._citation_map.get(url)
                            cite_marker = f" [{cite_id}]" if cite_id else ""
                            content_parts.append(f"{text}{cite_marker}")
                    current_section.content = "\n\n".join(content_parts)
                    finding_idx += len(relevant)

            elif line.startswith("  - ") or line.startswith("- "):
                # Sub-item
                sub_heading = line.lstrip(" -").strip()
                if current_section:
                    current_sub = ReportSection(heading=sub_heading, level=3)
                    current_section.subsections.append(current_sub)

        return sections

    def _find_relevant_findings(
        self, heading: str, findings: list[dict]
    ) -> list[dict]:
        """Find findings relevant to a section heading."""
        heading_terms = set(heading.lower().split())
        relevant = []

        for f in findings:
            text = (f.get("text", "") + " " + f.get("snippet", "")).lower()
            if any(term in text for term in heading_terms if len(term) > 2):
                relevant.append(f)

        return relevant if relevant else findings[:1]

    def _extract_domain(self, url: str) -> str:
        try:
            from urllib.parse import urlparse
            return urlparse(url).netloc.replace("www.", "")
        except:
            return ""

    def save(self, report: Report, path: str, fmt: str = "markdown") -> str:
        """Save report to file."""
        from hermes_tools import write_file

        if fmt == "markdown":
            content = report.markdown()
            ext = ".md"
        elif fmt == "html":
            content = report.html()
            ext = ".html"
        elif fmt == "json":
            content = json.dumps(report.to_dict(), indent=2, ensure_ascii=False)
            ext = ".json"
        else:
            raise ValueError(f"Unknown format: {fmt}")

        filepath = f"{path}{ext}"
        write_file(filepath, content)
        logger.info(f"Report saved to {filepath}")
        return filepath
