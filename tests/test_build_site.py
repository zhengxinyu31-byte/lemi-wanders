import json
import os
from pipeline.models import (
    City, POI, StoryLine, StoryStop, Narrative, ImageRef,
)
from pipeline.build_site import build_city_payload, write_site

PARIS = City(id="paris", name_zh="巴黎", name_en="Paris",
             center_lat=48.8566, center_lng=2.3522, bbox=(48.8, 2.2, 48.91, 2.47))


def _poi():
    return POI(id="cafe", city="paris", country="FR",
               name_zh="花神", name_en="Flore", lat=48.854, lng=2.332,
               address_zh="地址", address_en="addr",
               base_images=[ImageRef("u", "t", "a", "cc", "s", "high")])


def _storyline():
    stop = StoryStop(storyline_id="emily", poi_id="cafe", order=1, narrative=[
        Narrative("scene", "剧情", "scene", "high"),
        Narrative("anecdote", "弱", "weak", "low"),  # 应被过滤
    ])
    return StoryLine(id="emily", city="paris", title_zh="艾米莉", title_en="Emily",
                     theme="Emily in Paris", summary_zh="s", summary_en="s", stops=[stop])


def test_payload_filters_low_confidence_narrative():
    payload = build_city_payload(PARIS, {"cafe": _poi()}, [_storyline()])
    stop0 = payload["storylines"][0]["stops"][0]
    types = [n["type"] for n in stop0["narrative"]]
    assert types == ["scene"]  # low 的 anecdote 不在


def test_payload_includes_bilingual_fields():
    payload = build_city_payload(PARIS, {"cafe": _poi()}, [_storyline()])
    poi = payload["pois"]["cafe"]
    assert poi["name_zh"] == "花神" and poi["name_en"] == "Flore"
    assert payload["city"]["name_en"] == "Paris"


def test_payload_stops_reference_poi_and_coord():
    payload = build_city_payload(PARIS, {"cafe": _poi()}, [_storyline()])
    stop0 = payload["storylines"][0]["stops"][0]
    assert stop0["poi_id"] == "cafe"
    assert payload["pois"]["cafe"]["lat"] == 48.854


def test_write_site_emits_json_and_copies_web(tmp_path):
    web = tmp_path / "web"
    (web / "assets").mkdir(parents=True)
    (web / "templates").mkdir(parents=True)
    (web / "templates" / "city.html").write_text("<html>{{CITY_ID}}</html>", encoding="utf-8")
    (web / "assets" / "app.js").write_text("// app", encoding="utf-8")
    dist = tmp_path / "dist"
    payload = build_city_payload(PARIS, {"cafe": _poi()}, [_storyline()])
    write_site(payload, str(web), str(dist))
    data_file = dist / "data" / "paris.json"
    assert data_file.exists()
    loaded = json.loads(data_file.read_text(encoding="utf-8"))
    assert loaded["city"]["id"] == "paris"
    assert (dist / "assets" / "app.js").exists()
    # placeholder must be replaced with the city id (and no raw token left)
    index_html = (dist / "index.html").read_text(encoding="utf-8")
    assert "paris" in index_html
    assert "{{CITY_ID}}" not in index_html
