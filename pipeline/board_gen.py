"""Generate the board: POI squares in storyline order, filler squares between.

POI spacing on a real storyline is very uneven (0.21 km between Emily's flat
and the Panthéon, 1.94 km from the bridge to the tower). Allocating filler
purely by distance would give the shortest gap zero squares, putting two POI
squares back to back. Every gap therefore gets at least one filler square,
and the remainder is distributed by distance.
"""
from __future__ import annotations

import math
from typing import Dict, List, Tuple

from pipeline.models import BoardTile, POI, StoryLine
from pipeline.schema import stops_for_storyline

EARTH_RADIUS_KM = 6371.0


def haversine_km(a: Tuple[float, float], b: Tuple[float, float]) -> float:
    """Great-circle distance in km between two (lat, lng) points."""
    lat1, lat2 = math.radians(a[0]), math.radians(b[0])
    dlat = lat2 - lat1
    dlng = math.radians(b[1] - a[1])
    h = (math.sin(dlat / 2) ** 2
         + math.cos(lat1) * math.cos(lat2) * math.sin(dlng / 2) ** 2)
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(h))


def allocate_filler(gaps: List[float], total: int) -> List[int]:
    """Split `total` filler squares across gaps: one each, rest by distance.

    Uses the largest-remainder method for the distance-weighted part so the
    counts sum exactly to `total`.
    """
    if total < len(gaps):
        raise ValueError(
            f"need at least one filler per gap: total={total} gaps={len(gaps)}")
    counts = [1] * len(gaps)
    remaining = total - len(gaps)
    if remaining == 0:
        return counts
    span = sum(gaps)
    raw = [g / span * remaining for g in gaps]
    extra = [int(r) for r in raw]
    short = remaining - sum(extra)
    order = sorted(range(len(raw)), key=lambda i: raw[i] - extra[i], reverse=True)
    for i in order[:short]:
        extra[i] += 1
    return [c + e for c, e in zip(counts, extra)]


def interpolate(a: Tuple[float, float], b: Tuple[float, float],
                frac: float) -> Tuple[float, float]:
    """Linearly interpolate between two (lat, lng) points."""
    return (a[0] + (b[0] - a[0]) * frac, a[1] + (b[1] - a[1]) * frac)


def build_board(storyline: StoryLine, pois: Dict[str, POI],
                filler_plan: List[str], total_filler: int = 13) -> List[BoardTile]:
    """Build the ordered board for a storyline.

    filler_plan is the ordered list of filler tile types to consume, e.g.
    ["street", "chance", "photo", "easter", ...]. It must contain at least
    total_filler entries; extras are ignored.
    """
    stops = stops_for_storyline(storyline)
    coords = [(pois[s.poi_id].lat, pois[s.poi_id].lng) for s in stops]
    gaps = [haversine_km(coords[i], coords[i + 1]) for i in range(len(coords) - 1)]
    counts = allocate_filler(gaps, total_filler)

    tiles: List[BoardTile] = []
    cursor = 0
    for i, stop in enumerate(stops):
        lat, lng = coords[i]
        tiles.append(BoardTile(index=len(tiles), type="poi",
                               lat=lat, lng=lng, poi_id=stop.poi_id))
        if i >= len(counts):
            continue
        n = counts[i]
        for k in range(n):
            frac = (k + 1) / (n + 1)
            flat, flng = interpolate(coords[i], coords[i + 1], frac)
            ttype = filler_plan[cursor % len(filler_plan)]
            cursor += 1
            tiles.append(BoardTile(index=len(tiles), type=ttype,
                                   lat=flat, lng=flng))
    return tiles
