"""Core data models for Lemi's Diary.

Three-layer decoupling: POI (shared place) / StoryStop (POI × storyline,
carries narrative) / StoryLine. Objective facts live on POI; subjective
narrative lives on StoryStop, so one shared POI can tell different stories
in different storylines.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Tuple

CONFIDENCE_ORDER = {"low": 0, "mid": 1, "high": 2}
NARRATIVE_TYPES = ("scene", "anecdote", "masterpiece", "history")
DEFAULT_THRESHOLD = "mid"


def meets_threshold(confidence: str, threshold: str = DEFAULT_THRESHOLD) -> bool:
    """Return True if confidence is at or above threshold.

    Unknown confidence values are treated as below threshold (do not show).
    """
    if confidence not in CONFIDENCE_ORDER:
        return False
    return CONFIDENCE_ORDER[confidence] >= CONFIDENCE_ORDER[threshold]


@dataclass
class ImageRef:
    """A single image with attribution for licensing compliance."""

    url: str
    thumb: str
    author: str
    license: str
    source_page: str
    confidence: str


@dataclass
class Narrative:
    """One bilingual narrative field with a confidence tag and optional image."""

    type: str
    text_zh: str
    text_en: str
    confidence: str
    image: Optional[ImageRef] = None


@dataclass
class POI:
    """Shared place object; objective info only, shared across storylines."""

    id: str
    city: str
    country: str
    name_zh: str
    name_en: str
    lat: Optional[float]
    lng: Optional[float]
    address_zh: str
    address_en: str
    base_images: List[ImageRef] = field(default_factory=list)
    practical: Optional[Narrative] = None
    default_photo_spot: Optional[Narrative] = None
    wiki_title: str = ""


@dataclass
class StoryStop:
    """One stop on a storyline = POI × storyline; carries the narrative."""

    storyline_id: str
    poi_id: str
    order: int
    narrative: List[Narrative] = field(default_factory=list)
    photo_spot_override: Optional[Narrative] = None


@dataclass
class StoryLine:
    """An ordered themed route of StoryStops through a city."""

    id: str
    city: str
    title_zh: str
    title_en: str
    theme: str
    summary_zh: str
    summary_en: str
    stops: List[StoryStop] = field(default_factory=list)
    poster: Optional[ImageRef] = None


@dataclass
class City:
    """A city container. bbox = (min_lat, min_lng, max_lat, max_lng)."""

    id: str
    name_zh: str
    name_en: str
    center_lat: float
    center_lng: float
    bbox: Tuple[float, float, float, float]
