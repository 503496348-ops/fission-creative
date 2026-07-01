"""Evidence hardening for long-form research packages."""
from __future__ import annotations
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from urllib.parse import urlparse
import re
from typing import Iterable, List, Optional
TRUSTED_SUFFIXES = ('.edu', '.gov', '.org')
CLAIM_RE = re.compile(r'(?<=[。.!?])\s+|\n+')
INJECTION_RE = re.compile(r'(?i)(ignore previous|system prompt|developer instruction|api[_ -]?key|secret|token|jailbreak)')
@dataclass(frozen=True)
class EvidenceCard:
    title: str; url: str; domain: str; excerpt: str; claims: List[str]; source_score: float; injection_risk: bool; captured_at: str
    def to_dict(self) -> dict: return asdict(self)
def normalize_url(url: str) -> str:
    parsed = urlparse((url or '').strip())
    if not parsed.scheme or not parsed.netloc: return ''
    return parsed._replace(fragment='').geturl()
def source_score(url: str, title: str = '') -> float:
    parsed=urlparse(url); domain=parsed.netloc.lower().removeprefix('www.'); score=0.45
    if any(domain.endswith(s) for s in TRUSTED_SUFFIXES): score += 0.2
    if parsed.scheme == 'https': score += 0.1
    if re.search(r'paper|journal|report|whitepaper|docs|research', title, re.I): score += 0.15
    if re.search(r'medium\.com|substack|blog', domain): score -= 0.05
    return round(max(0.0, min(1.0, score)), 2)
def extract_claims(text: str, *, limit: int = 5) -> List[str]:
    cleaned = re.sub(r'\s+', ' ', text or '').strip()
    parts = [p.strip(' -•') for p in CLAIM_RE.split(cleaned) if len(p.strip()) >= 35]
    return parts[:limit]
def build_evidence_card(title: str, url: str, text: str) -> Optional[EvidenceCard]:
    norm=normalize_url(url)
    if not norm: return None
    domain=urlparse(norm).netloc.lower().removeprefix('www.'); excerpt=re.sub(r'\s+', ' ', text or '').strip()[:700]
    return EvidenceCard(title.strip()[:160], norm, domain, excerpt, extract_claims(text), source_score(norm, title), bool(INJECTION_RE.search(text or '')), datetime.now(timezone.utc).isoformat())
def build_evidence_pack(items: Iterable[dict]) -> List[EvidenceCard]:
    cards=[]; seen=set()
    for item in items:
        card=build_evidence_card(item.get('title',''), item.get('url',''), item.get('text') or item.get('content',''))
        if card and card.url not in seen: cards.append(card); seen.add(card.url)
    return sorted(cards, key=lambda c: (c.injection_risk, -c.source_score, c.domain))
