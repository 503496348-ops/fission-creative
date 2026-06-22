"""
Fission Creative — PDF & Document Processor
=============================================
Inspired by gpt_academic (70K⭐) PDF paper translation and LaTeX processing.

Key capabilities:
- Extract text from PDF documents (academic papers, reference novels)
- Parse LaTeX source files (.tex) preserving structure
- Chapter/section-aware extraction for long documents
- Translate extracted content (integrates with multi_model_query.py)
- Extract metadata: title, abstract, authors, references
- Structure-aware markdown output for downstream story analysis

Brand: AtomCollide-智械工坊
License: GPL v3
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


# ──── Data Structures ────

@dataclass
class DocumentSection:
    """A section/chapter extracted from a document."""
    level: int          # 0=top, 1=chapter, 2=section, 3=subsection
    title: str
    content: str
    page_start: int = 0
    page_end: int = 0
    children: list["DocumentSection"] = field(default_factory=list)

    def to_markdown(self, depth: int = 0) -> str:
        prefix = "#" * min(self.level + 1, 6)
        lines = [f"{prefix} {self.title}\n"]
        if self.content.strip():
            lines.append(self.content.strip() + "\n")
        for child in self.children:
            lines.append(child.to_markdown(depth + 1))
        return "\n".join(lines)

    def word_count(self) -> int:
        total = len(self.content)
        for child in self.children:
            total += child.word_count()
        return total


@dataclass
class ExtractedDocument:
    """Full extraction result from a document."""
    source_path: str
    title: str = ""
    authors: list[str] = field(default_factory=list)
    abstract: str = ""
    sections: list[DocumentSection] = field(default_factory=list)
    references: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    raw_text: str = ""
    page_count: int = 0

    @property
    def total_words(self) -> int:
        return sum(s.word_count() for s in self.sections)

    def to_markdown(self) -> str:
        parts = []
        if self.title:
            parts.append(f"# {self.title}\n")
        if self.authors:
            parts.append(f"**作者**: {', '.join(self.authors)}\n")
        if self.abstract:
            parts.append(f"## 摘要\n{self.abstract}\n")
        for section in self.sections:
            parts.append(section.to_markdown())
        if self.references:
            parts.append("\n## 参考文献\n")
            for i, ref in enumerate(self.references, 1):
                parts.append(f"{i}. {ref}")
        return "\n".join(parts)

    def to_chapters(self) -> list[dict]:
        """Convert to chapter list format compatible with fission-creative."""
        chapters = []
        for i, section in enumerate(self.sections, 1):
            chapters.append({
                "chapter_num": i,
                "title": section.title,
                "content": section.content,
                "word_count": section.word_count(),
                "subsections": [
                    {"title": c.title, "content": c.content}
                    for c in section.children
                ],
            })
        return chapters


# ──── PDF Text Extraction ────

def extract_pdf_text(pdf_path: str) -> tuple[str, int]:
    """Extract text from a PDF file.

    Uses PyMuPDF (fitz) if available, falls back to pdfplumber,
    then to raw binary extraction.

    Returns (full_text, page_count).
    """
    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    # Try PyMuPDF (fastest, best quality)
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(str(path))
        pages = []
        for page in doc:
            pages.append(page.get_text())
        text = "\n\n".join(pages)
        page_count = len(doc)
        doc.close()
        return text, page_count
    except ImportError:
        pass

    # Try pdfplumber (good quality, pure Python)
    try:
        import pdfplumber
        with pdfplumber.open(str(path)) as pdf:
            pages = []
            for page in pdf.pages:
                page_text = page.extract_text() or ""
                pages.append(page_text)
            text = "\n\n".join(pages)
            return text, len(pdf.pages)
    except ImportError:
        pass

    # Try pypdf (lightweight)
    try:
        from pypdf import PdfReader
        reader = PdfReader(str(path))
        pages = []
        for page in reader.pages:
            pages.append(page.extract_text() or "")
        text = "\n\n".join(pages)
        return text, len(reader.pages)
    except ImportError:
        pass

    raise ImportError(
        "No PDF library available. Install one of: "
        "pip install PyMuPDF | pip install pdfplumber | pip install pypdf"
    )


def extract_pdf_metadata(pdf_path: str) -> dict:
    """Extract metadata from a PDF file."""
    try:
        import fitz
        doc = fitz.open(pdf_path)
        meta = doc.metadata or {}
        doc.close()
        return {
            "title": meta.get("title", ""),
            "author": meta.get("author", ""),
            "subject": meta.get("subject", ""),
            "keywords": meta.get("keywords", ""),
            "creator": meta.get("creator", ""),
        }
    except ImportError:
        pass

    try:
        from pypdf import PdfReader
        reader = PdfReader(pdf_path)
        info = reader.metadata
        if info:
            return {
                "title": info.title or "",
                "author": info.author or "",
                "subject": info.subject or "",
                "keywords": info.keywords or "",
            }
    except ImportError:
        pass

    return {}


# ──── LaTeX Parsing ────

_LATEX_SECTION_RE = re.compile(
    r'\\(part|chapter|section|subsection|subsubsection)\*?\{([^}]+)\}'
)
_LATEX_LEVELS = {
    "part": 0, "chapter": 1, "section": 2, "subsection": 3, "subsubsection": 4,
}

_LATEX_ENV_RE = re.compile(
    r'\\begin\{(abstract|document)\}(.*?)\\end\{\1\}',
    re.DOTALL,
)

_LATEX_CITE_RE = re.compile(r'\\bibitem\{([^}]+)\}(.*?)(?=\\bibitem|$)', re.DOTALL)
_LATEX_BIBTEX_RE = re.compile(r'@\w+\{([^,]+),.*?title\s*=\s*\{([^}]+)\}', re.DOTALL)


def strip_latex_commands(text: str) -> str:
    """Remove LaTeX commands, keeping readable text content."""
    # Remove comments (lines starting with %)
    text = re.sub(r'^%.*$', '', text, flags=re.MULTILINE)
    # Remove \command{content} → content (for common text commands)
    for cmd in ['textbf', 'textit', 'emph', 'underline', 'textsc', 'texttt']:
        text = re.sub(rf'\\{cmd}\{{([^}}]*)\}}', r'\1', text)
    # Remove \label, \ref, \cite, \pageref
    text = re.sub(r'\\(?:label|ref|cite|pageref|eqref)\{[^}]*\}', '', text)
    # Remove \footnote{...}
    text = re.sub(r'\\footnote\{[^}]*\}', '', text)
    # Remove remaining \commands (but keep their braces content)
    text = re.sub(r'\\[a-zA-Z]+\*?(?:\[[^\]]*\])?(?:\{([^}]*)\})?', r'\1', text)
    # Clean up leftover backslash commands without braces
    text = re.sub(r'\\[a-zA-Z]+\b', '', text)
    # Clean up special characters
    replacements = {
        '&': '&', '%': '%', '#': '#', '_': '_',
        '~': ' ', '\\\\': '\n', '\\newline': '\n',
        '\\par': '\n\n', '\\quad': ' ', '\\qquad': '  ',
        '\\ldots': '…', '\\dots': '…',
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    # Remove $ math delimiters (keep content)
    text = re.sub(r'\$([^$]*)\$', r'\1', text)
    # Clean up extra whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def parse_latex(source: str) -> ExtractedDocument:
    """Parse a LaTeX source string into structured sections."""
    doc = ExtractedDocument(source_path="<string>")

    # Extract title
    title_match = re.search(r'\\title\{([^}]+)\}', source)
    if title_match:
        doc.title = strip_latex_commands(title_match.group(1))

    # Extract authors
    author_match = re.search(r'\\author\{([^}]+)\}', source)
    if author_match:
        raw_authors = author_match.group(1)
        # Split by \and or comma
        authors = re.split(r'\\and|,', raw_authors)
        doc.authors = [strip_latex_commands(a).strip() for a in authors if a.strip()]

    # Extract abstract
    abs_match = _LATEX_ENV_RE.search(source)
    if abs_match and abs_match.group(1) == "abstract":
        doc.abstract = strip_latex_commands(abs_match.group(2))

    # Extract sections
    sections: list[DocumentSection] = []
    section_matches = list(_LATEX_SECTION_RE.finditer(source))

    for i, match in enumerate(section_matches):
        cmd = match.group(1)
        title = strip_latex_commands(match.group(2))
        level = _LATEX_LEVELS.get(cmd, 2)

        # Content is between this section header and the next
        start = match.end()
        end = section_matches[i + 1].start() if i + 1 < len(section_matches) else len(source)

        # For last section, stop before bibliography
        bib_pos = source.find(r'\begin{thebibliography}')
        if bib_pos > 0 and end > bib_pos:
            end = bib_pos

        content = strip_latex_commands(source[start:end])
        sections.append(DocumentSection(level=level, title=title, content=content))

    # Build hierarchy
    doc.sections = _build_section_hierarchy(sections)

    # Extract references
    bib_match = re.search(r'\\begin\{thebibliography\}(.*?)\\end\{thebibliography\}', source, re.DOTALL)
    if bib_match:
        bib_text = bib_match.group(1)
        for cite_match in _LATEX_CITE_RE.finditer(bib_text):
            ref_text = strip_latex_commands(cite_match.group(2))
            doc.references.append(ref_text)

    # Also try BibTeX
    for bibtex_match in _LATEX_BIBTEX_RE.finditer(source):
        doc.references.append(bibtex_match.group(2))

    doc.raw_text = strip_latex_commands(source)
    return doc


def _build_section_hierarchy(sections: list[DocumentSection]) -> list[DocumentSection]:
    """Build a tree from flat section list based on levels."""
    if not sections:
        return []

    root: list[DocumentSection] = []
    stack: list[DocumentSection] = []

    for section in sections:
        # Pop stack until we find a parent (lower level)
        while stack and stack[-1].level >= section.level:
            stack.pop()

        if stack:
            stack[-1].children.append(section)
        else:
            root.append(section)

        stack.append(section)

    return root


def parse_latex_file(tex_path: str) -> ExtractedDocument:
    """Parse a .tex file."""
    path = Path(tex_path)
    if not path.exists():
        raise FileNotFoundError(f"LaTeX file not found: {tex_path}")
    text = path.read_text(encoding="utf-8")
    doc = parse_latex(text)
    doc.source_path = str(path)
    return doc


# ──── Plain Text / Markdown Parsing ────

_CHAPTER_RE = re.compile(
    r'^(?:'
    r'(?:第[一二三四五六七八九十百千万\d]+[章回节卷])'
    r'|(?:Chapter\s+\d+)'
    r'|(?:CHAPTER\s+\d+)'
    r'|(?:卷[一二三四五六七八九十\d]+)'
    r')\s*[：:\s]*(.*)$',
    re.MULTILINE,
)


def parse_chapters_from_text(text: str, title: str = "") -> ExtractedDocument:
    """Parse chapter-structured text (novel format) into ExtractedDocument."""
    doc = ExtractedDocument(source_path="<text>", title=title, raw_text=text)

    matches = list(_CHAPTER_RE.finditer(text))
    if not matches:
        # No chapter markers found — treat as single section
        doc.sections = [DocumentSection(level=0, title="全文", content=text)]
        return doc

    # First content before chapter 1 → prologue / abstract
    if matches[0].start() > 0:
        prologue = text[:matches[0].start()].strip()
        if prologue:
            doc.sections.append(DocumentSection(level=0, title="前言", content=prologue))

    for i, match in enumerate(matches):
        ch_title = match.group(0).strip()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        content = text[start:end].strip()
        doc.sections.append(DocumentSection(level=1, title=ch_title, content=content))

    return doc


# ──── High-Level API ────

def process_document(file_path: str) -> ExtractedDocument:
    """Auto-detect file type and extract structured content.

    Supported formats: .pdf, .tex, .txt, .md
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    suffix = path.suffix.lower()

    if suffix == ".pdf":
        text, page_count = extract_pdf_text(file_path)
        meta = extract_pdf_metadata(file_path)
        doc = parse_chapters_from_text(text, title=meta.get("title", path.stem))
        doc.source_path = file_path
        doc.page_count = page_count
        doc.metadata = meta
        if meta.get("author"):
            doc.authors = [meta["author"]]
        return doc

    elif suffix == ".tex":
        return parse_latex_file(file_path)

    elif suffix in (".txt", ".md", ".markdown"):
        text = path.read_text(encoding="utf-8")
        doc = parse_chapters_from_text(text, title=path.stem)
        doc.source_path = file_path
        return doc

    else:
        # Try reading as plain text
        try:
            text = path.read_text(encoding="utf-8")
            doc = parse_chapters_from_text(text, title=path.stem)
            doc.source_path = file_path
            return doc
        except UnicodeDecodeError:
            raise ValueError(f"Unsupported file format: {suffix}")


def extract_for_writing_reference(file_path: str, max_chars: int = 50000) -> str:
    """Extract document content formatted as a writing reference.

    Output is optimized for use as context in story generation:
    - Title and metadata
    - Chapter structure
    - Key content (truncated to max_chars)
    """
    doc = process_document(file_path)
    output = []

    output.append(f"# 参考文档: {doc.title or Path(file_path).stem}")
    if doc.authors:
        output.append(f"**来源**: {', '.join(doc.authors)}")
    output.append(f"**字数**: {doc.total_words} | **页数**: {doc.page_count or 'N/A'}")
    output.append("")

    if doc.abstract:
        output.append(f"## 摘要\n{doc.abstract}\n")

    output.append("## 内容结构\n")
    char_count = 0
    for section in doc.sections:
        section_md = section.to_markdown()
        if char_count + len(section_md) > max_chars:
            output.append(f"\n> ⚠️ 内容截断（已达{max_chars}字限制）")
            break
        output.append(section_md)
        char_count += len(section_md)

    return "\n".join(output)


# ──── Plugin Integration ────

try:
    from plugin_architecture import PluginRegistry, Plugin

    def _pdf_extract(text: str, args: dict) -> str:
        """Plugin: extract and structure content from a PDF/LaTeX file."""
        file_path = args.get("file_path", "").strip()
        if not file_path:
            # If text itself looks like a file path
            if os.path.isfile(text.strip()):
                file_path = text.strip()
            else:
                return "⚠️ 请提供文件路径。用法: file_path=/path/to/file.pdf"

        max_chars = int(args.get("max_chars", 50000))
        try:
            return extract_for_writing_reference(file_path, max_chars=max_chars)
        except Exception as e:
            return f"❌ 文档处理失败: {e}"

    def _latex_parse(text: str, args: dict) -> str:
        """Plugin: parse LaTeX source and convert to structured markdown."""
        file_path = args.get("file_path", "").strip()
        if file_path and os.path.isfile(file_path):
            doc = parse_latex_file(file_path)
        else:
            # Treat input text as LaTeX
            doc = parse_latex(text)
        return doc.to_markdown()

    def _chapter_split(text: str, args: dict) -> str:
        """Plugin: split text by chapter markers into structured format."""
        title = args.get("title", "未命名")
        doc = parse_chapters_from_text(text, title=title)

        output = [f"# 章节拆分结果 — {title}\n"]
        output.append(f"共发现 {len(doc.sections)} 个章节\n")
        for ch in doc.sections:
            wc = ch.word_count()
            output.append(f"- **{ch.title}** ({wc}字)")
        output.append("\n---\n")
        for ch in doc.sections:
            output.append(ch.to_markdown())
        return "\n".join(output)

    PluginRegistry.register(Plugin(
        name="pdf_extract",
        info="文档提取：从PDF/LaTeX/TXT中提取结构化内容",
        function=_pdf_extract,
        category="工具",
        hotkey="Ctrl+D",
        advanced_args=True,
        args_reminder="file_path: 文件路径; max_chars: 最大字符数(默认50000)",
    ))
    PluginRegistry.register(Plugin(
        name="latex_parse",
        info="LaTeX解析：将LaTeX源码转为结构化Markdown",
        function=_latex_parse,
        category="工具",
        hotkey="Ctrl+L",
        advanced_args=True,
        args_reminder="file_path: .tex文件路径(或直接输入LaTeX源码)",
    ))
    PluginRegistry.register(Plugin(
        name="chapter_split",
        info="章节拆分：按章节标记拆分文本为结构化格式",
        function=_chapter_split,
        category="工具",
        hotkey="Ctrl+S",
        advanced_args=True,
        args_reminder="title: 文档标题(默认'未命名')",
    ))

except ImportError:
    pass  # Standalone usage


# ──── CLI ────

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python pdf_processor.py <file_path> [--format markdown|chapters|reference]")
        print("  Supported: .pdf, .tex, .txt, .md")
        print("\nOptional dependencies:")
        print("  pip install PyMuPDF     # Best PDF extraction")
        print("  pip install pdfplumber  # Pure Python PDF extraction")
        print("  pip install pypdf       # Lightweight PDF extraction")
        sys.exit(1)

    file_path = sys.argv[1]
    fmt = "reference"

    if "--format" in sys.argv:
        idx = sys.argv.index("--format")
        fmt = sys.argv[idx + 1]

    doc = process_document(file_path)

    if fmt == "markdown":
        print(doc.to_markdown())
    elif fmt == "chapters":
        import json
        print(json.dumps(doc.to_chapters(), ensure_ascii=False, indent=2))
    else:
        print(extract_for_writing_reference(file_path))
