"""Load content/ JSON into models and apply confidence filtering."""
from __future__ import annotations

import json
from typing import List, Optional

from pipeline.models import (
    City, ImageRef, Narrative, POI, StoryLine, StoryStop, meets_threshold,
)


def _image_from_dict(d: Optional[dict]) -> Optional[ImageRef]:
    if not d:
        return None
    return ImageRef(
        url=d.get("url", ""), thumb=d.get("thumb", ""),
        author=d.get("author", ""), license=d.get("license", ""),
        source_page=d.get("source_page", ""), confidence=d.get("confidence", "low"),
    )


def _narrative_from_dict(d: Optional[dict]) -> Optional[Narrative]:
    if not d:
        return None
    return Narrative(
        type=d.get("type", ""), text_zh=d.get("text_zh", ""),
        text_en=d.get("text_en", ""), confidence=d.get("confidence", "low"),
        image=_image_from_dict(d.get("image")),
    )


def load_city(path: str) -> City:
    """Load a City from a JSON file."""
    d = json.loads(_read(path))
    bbox = tuple(d["bbox"])  # (min_lat, min_lng, max_lat, max_lng)
    return City(
        id=d["id"], name_zh=d["name_zh"], name_en=d["name_en"],
        center_lat=d["center_lat"], center_lng=d["center_lng"], bbox=bbox,
    )


def load_poi(path: str) -> POI:
    """Load a shared POI from a JSON file."""
    d = json.loads(_read(path))
    return POI(
        id=d["id"], city=d["city"], country=d.get("country", ""),
        name_zh=d["name_zh"], name_en=d["name_en"],
        lat=d.get("lat"), lng=d.get("lng"),
        address_zh=d.get("address_zh", ""), address_en=d.get("address_en", ""),
        base_images=[_image_from_dict(i) for i in d.get("base_images", []) if i],
        practical=_narrative_from_dict(d.get("practical")),
        default_photo_spot=_narrative_from_dict(d.get("default_photo_spot")),
        wiki_title=d.get("wiki_title", ""),
    )


def load_storyline(path: str) -> StoryLine:
    """Load a StoryLine (with its StoryStops) from a JSON file."""
    d = json.loads(_read(path))
    stops = []
    for s in d.get("stops", []):
        stops.append(StoryStop(
            storyline_id=d["id"], poi_id=s["poi_id"], order=s["order"],
            narrative=[_narrative_from_dict(n) for n in s.get("narrative", []) if n],
            photo_spot_override=_narrative_from_dict(s.get("photo_spot_override")),
        ))
    return StoryLine(
        id=d["id"], city=d["city"], title_zh=d["title_zh"], title_en=d["title_en"],
        theme=d.get("theme", ""), summary_zh=d.get("summary_zh", ""),
        summary_en=d.get("summary_en", ""), stops=stops,
        poster=_image_from_dict(d.get("poster")),
    )


def stops_for_storyline(storyline: StoryLine) -> List[StoryStop]:
    """Return this storyline's stops sorted by order."""
    return sorted(storyline.stops, key=lambda s: s.order)


def visible_narrative(stop: StoryStop, threshold: str = "mid") -> List[Narrative]:
    """Return only narrative entries at or above the confidence threshold."""
    return [n for n in stop.narrative if n and meets_threshold(n.confidence, threshold)]


def resolve_photo_spot(poi: POI, stop: StoryStop,
                       threshold: str = "mid") -> Optional[Narrative]:
    """Resolve the photo spot: stop override wins, else POI default; must pass threshold."""
    candidate = stop.photo_spot_override or poi.default_photo_spot
    if candidate and meets_threshold(candidate.confidence, threshold):
        return candidate
    return None


def _read(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()
