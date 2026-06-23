from __future__ import annotations

from dataclasses import dataclass, field

"""Intermediate Representation dataclasses for ManReader.

The IR is intentionally plain Python data: easy to inspect, diff, persist later,
and keep independent from extraction, enrichment, rendering, or validation code.
"""


@dataclass
class DocumentIR:
    """Root IR object for a converted PDF/manual."""

    schema_version: str
    source_path: str
    title: str | None = None
    author: str | None = None
    page_count: int = 0
    pages: list[PageIR] = field(default_factory=list)
    toc: list[dict[str, str]] = field(default_factory=list)
    metadata: dict[str, str] = field(default_factory=dict)
    entities: list[EntityIR] = field(default_factory=list)


@dataclass
class PageIR:
    """IR for one source page, preserving page geometry for later review."""

    id: str
    page_num: int
    width: float | None = None
    height: float | None = None
    blocks: list[BlockIR] = field(default_factory=list)


@dataclass
class BlockIR:
    """IR for an ordered content block extracted from a page."""

    id: str
    type: str
    page_num: int
    order: int
    bbox: tuple[float, float, float, float] | None = None
    text: str | None = None
    style: dict[str, str] = field(default_factory=dict)
    asset: AssetIR | None = None


@dataclass
class AssetIR:
    """IR for an extracted asset that may receive AI or human enrichment."""

    id: str
    sha: str
    kind: str
    path: str
    original_name: str | None = None
    current_name: str | None = None
    ext: str | None = None
    title: str | None = None
    description: str | None = None
    alt_text: str | None = None
    classification: str | None = None
    is_background: bool = False
    is_duplicate: bool = False
    enrichment: dict[str, str] = field(default_factory=dict)


@dataclass
class AIProposal:
    """AI-suggested field changes kept separate from extracted source data."""

    target_id: str
    fields: dict[str, str] = field(default_factory=dict)
    confidence: float | None = None
    backend: str | None = None
    model: str | None = None
    status: str | None = None
    reason: str | None = None


@dataclass
class ReviewItem:
    """Queue entry for proposals that should not be applied automatically."""

    id: str
    target_id: str
    page_num: int | None = None
    kind: str | None = None
    path: str | None = None
    proposal: AIProposal | None = None
    reason: str | None = None
    status: str | None = None


@dataclass
class HumanOverride:
    """Human-authored corrections that should take precedence over AI output."""

    target_id: str
    fields: dict[str, str] = field(default_factory=dict)
    updated_at: str | None = None
    source: str = "human"


@dataclass
class Issue:
    """Problem record for low-confidence enrichment or extraction anomalies."""

    id: str
    target_id: str | None = None
    page_num: int | None = None
    kind: str | None = None
    path: str | None = None
    reason: str | None = None
    message: str | None = None
    confidence: float | None = None


@dataclass
class EntityIR:
    """Semantic entity detected or confirmed in the document.

    Examples:
    - monster
    - npc
    - location
    - spell
    - magic_item

    Entity detection may be deterministic, AI-assisted, or human-confirmed.
    """

    id: str
    name: str
    type: str
    page_num: int | None = None
    aliases: list[str] = field(default_factory=list)
    source_block_ids: list[str] = field(default_factory=list)
    confidence: float | None = None
    source: str | None = None
