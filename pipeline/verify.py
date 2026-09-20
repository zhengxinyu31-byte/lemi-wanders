"""Build-time gate for content whose accuracy must be checked, not self-rated.

Quotes and street cards are rejected unless they carry real sources and have
been marked verified by the cross-check / adversarial-review pass. LLM
self-rated confidence is deliberately not accepted here.
"""
from __future__ import annotations

from typing import List, Optional

from pipeline.models import Quote, StreetCard

MIN_STREET_SOURCES = 2


def quote_passes(quote: Optional[Quote]) -> bool:
    """Return True if the quote is verified and carries a real source."""
    if quote is None:
        return False
    if not quote.verified:
        return False
    return bool(quote.source.strip()) and bool(quote.source_url.strip())


def street_card_passes(card: Optional[StreetCard]) -> bool:
    """Return True if the street card is verified and cross-checked."""
    if card is None:
        return False
    if not card.verified:
        return False
    return len([s for s in card.sources if s.strip()]) >= MIN_STREET_SOURCES


def filter_street_cards(cards: List[StreetCard]) -> List[StreetCard]:
    """Drop every street card that fails the gate."""
    return [c for c in cards if street_card_passes(c)]
