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


def enrich_images(pois, fetcher, used):
    """Fill each POI's base_images with one deduped image via the chain."""
    for poi in pois.values():
        if poi.lat is None or poi.lng is None:
            continue
        try:
            geo = fetcher.geosearch(poi.lat, poi.lng)
        except Exception:
            geo = []
        try:
            named = fetcher.name_search(poi.name_en or poi.name_zh)
        except Exception:
            named = []
        chosen = pick_image([geo, named], used)
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
