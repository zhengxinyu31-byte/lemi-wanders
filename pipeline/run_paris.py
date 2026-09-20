# pipeline/run_paris.py
"""End-to-end build for the Paris / Emily-in-Paris sample.

Loads content/, fetches one image per POI via the degradation chain with
global dedup, assembles the payload, and writes dist/.
"""
from __future__ import annotations

import glob
import os

from pipeline.build_site import build_city_payload, write_site
from pipeline.images import ImageFetcher, pick_image
from pipeline.schema import load_city, load_poi, load_storyline

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _try(fetch):
    """Call a fetch closure, returning [] on any network/parse failure."""
    try:
        return fetch()
    except Exception:
        return []


def enrich_images(pois, fetcher, used):
    """Fill each POI's base_images with one deduped image via the chain.

    Each tier tries Commons first, then falls back to the Wikipedia API
    (some networks block commons.wikimedia.org but allow en.wikipedia.org).
    """
    for poi in pois.values():
        if poi.lat is None or poi.lng is None:
            continue
        # Best: exact Wikipedia article title (curated main image, accurate).
        titled = _try(lambda: fetcher.wiki_title_image(poi.wiki_title)) \
            if poi.wiki_title else []
        geo = _try(lambda: fetcher.geosearch(poi.lat, poi.lng)) \
            or _try(lambda: fetcher.wiki_geosearch(poi.lat, poi.lng))
        name = poi.name_en or poi.name_zh
        named = _try(lambda: fetcher.name_search(name)) \
            or _try(lambda: fetcher.wiki_name_search(name))
        chosen = pick_image([titled, geo, named], used)
        poi.base_images = [chosen] if chosen else []


def main(offline: bool = False) -> None:
    """Build the Paris sample site into dist/."""
    city = load_city(os.path.join(ROOT, "content", "cities", "paris.json"))
    pois = {}
    for path in glob.glob(os.path.join(ROOT, "content", "pois", "*.json")):
        poi = load_poi(path)
        pois[poi.id] = poi
    storylines = [load_storyline(p) for p in
                  glob.glob(os.path.join(ROOT, "content", "storylines", "*.json"))]

    if not offline:
        enrich_images(pois, ImageFetcher(), set())

    payload = build_city_payload(city, pois, storylines)
    write_site(payload, os.path.join(ROOT, "web"), os.path.join(ROOT, "dist"))
    print("Built dist/ for city:", city.id, "POIs:", len(pois))


if __name__ == "__main__":
    main(offline=bool(os.getenv("LEMI_OFFLINE")))
