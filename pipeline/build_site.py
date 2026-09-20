"""Assemble the static site: build a clean per-city JSON payload and emit dist/."""
from __future__ import annotations

import json
import os
import shutil
from typing import Dict, List

from pipeline.models import City, ImageRef, Narrative, POI, StoryLine
from pipeline.schema import (
    resolve_photo_spot, stops_for_storyline, visible_narrative,
)


def _image_dict(img: ImageRef) -> dict:
    return {"url": img.url, "thumb": img.thumb, "author": img.author,
            "license": img.license, "source_page": img.source_page}


def _narrative_dict(n: Narrative) -> dict:
    d = {"type": n.type, "text_zh": n.text_zh, "text_en": n.text_en}
    if n.image:
        d["image"] = _image_dict(n.image)
    return d


def _poi_dict(poi: POI, threshold: str) -> dict:
    from pipeline.models import meets_threshold
    images = [_image_dict(i) for i in poi.base_images
              if meets_threshold(i.confidence, threshold)]
    out = {"id": poi.id, "name_zh": poi.name_zh, "name_en": poi.name_en,
           "lat": poi.lat, "lng": poi.lng,
           "address_zh": poi.address_zh, "address_en": poi.address_en,
           "base_images": images}
    if poi.practical and meets_threshold(poi.practical.confidence, threshold):
        out["practical"] = _narrative_dict(poi.practical)
    return out


def build_city_payload(city: City, pois: Dict[str, POI],
                       storylines: List[StoryLine], threshold: str = "mid") -> dict:
    """Build the front-end payload for a city with all confidence filtering applied."""
    sl_out = []
    for sl in storylines:
        stops_out = []
        for stop in stops_for_storyline(sl):
            poi = pois.get(stop.poi_id)
            spot = resolve_photo_spot(poi, stop, threshold) if poi else None
            stops_out.append({
                "poi_id": stop.poi_id, "order": stop.order,
                "narrative": [_narrative_dict(n) for n in visible_narrative(stop, threshold)],
                "photo_spot": _narrative_dict(spot) if spot else None,
            })
        sl_out.append({
            "id": sl.id, "title_zh": sl.title_zh, "title_en": sl.title_en,
            "theme": sl.theme, "summary_zh": sl.summary_zh, "summary_en": sl.summary_en,
            "poster": _image_dict(sl.poster) if sl.poster else None,
            "stops": stops_out,
        })
    return {
        "city": {"id": city.id, "name_zh": city.name_zh, "name_en": city.name_en,
                 "center_lat": city.center_lat, "center_lng": city.center_lng},
        "pois": {pid: _poi_dict(p, threshold) for pid, p in pois.items()},
        "storylines": sl_out,
    }


def write_site(payload: dict, web_dir: str, dist_dir: str) -> None:
    """Write payload JSON into dist/data/ and copy web/ assets + city page into dist/."""
    os.makedirs(os.path.join(dist_dir, "data"), exist_ok=True)
    city_id = payload["city"]["id"]
    with open(os.path.join(dist_dir, "data", f"{city_id}.json"), "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    # copy assets + i18n
    for sub in ("assets", "i18n"):
        src = os.path.join(web_dir, sub)
        if os.path.isdir(src):
            shutil.copytree(src, os.path.join(dist_dir, sub), dirs_exist_ok=True)

    # render city page (replace placeholder with city id)
    tpl_path = os.path.join(web_dir, "templates", "city.html")
    with open(tpl_path, "r", encoding="utf-8") as f:
        html = f.read().replace("{{CITY_ID}}", city_id)
    with open(os.path.join(dist_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(html)
