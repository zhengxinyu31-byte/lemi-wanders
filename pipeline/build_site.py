"""Assemble the static site: build a clean per-city JSON payload and emit dist/."""
from __future__ import annotations

import json
import os
import shutil
from typing import Dict, List

from pipeline.models import (
    BoardTile, Card, City, ImageRef, Narrative, POI, StoryLine, StreetCard,
)
from pipeline.schema import (
    resolve_photo_spot, stops_for_storyline, visible_narrative,
)
from pipeline.verify import filter_street_cards, quote_passes


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


def _tile_dict(t: BoardTile) -> dict:
    d = {"index": t.index, "type": t.type, "lat": t.lat, "lng": t.lng}
    if t.poi_id:
        d["poi_id"] = t.poi_id
    if t.content_id:
        d["content_id"] = t.content_id
    return d


def _card_dict(c: Card) -> dict:
    d = {"id": c.id, "rarity": c.rarity, "storyline_id": c.storyline_id,
         "poi_id": c.poi_id, "title_zh": c.title_zh, "title_en": c.title_en,
         "body_zh": c.body_zh, "body_en": c.body_en}
    if c.image:
        d["image"] = _image_dict(c.image)
    if quote_passes(c.quote):
        d["quote"] = {"text_zh": c.quote.text_zh,
                      "text_original": c.quote.text_original,
                      "source": c.quote.source,
                      "source_url": c.quote.source_url}
    return d


def _street_dict(s: StreetCard) -> dict:
    # sources 只用于构建时校验,不输出到前端
    return {"id": s.id, "category": s.category,
            "text_zh": s.text_zh, "text_en": s.text_en,
            "near_poi_id": s.near_poi_id}


def build_game_payload(tiles, cards, street_cards, chance,
                       night_from_index: int) -> dict:
    """Build the game-mode payload: board, cards, street cards, quiz."""
    return {
        "board": [_tile_dict(t) for t in tiles],
        "cards": {c.id: _card_dict(c) for c in cards},
        "street_cards": {s.id: _street_dict(s)
                         for s in filter_street_cards(street_cards)},
        "chance": {q["id"]: q for q in chance},
        "night_from_index": night_from_index,
    }
