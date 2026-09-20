import json
import os
from pipeline.models import (
    City, POI, StoryLine, StoryStop, Narrative, ImageRef,
)
from pipeline.build_site import build_city_payload, write_site
from pipeline.build_site import build_game_payload
from pipeline.models import BoardTile, Card, Quote, StreetCard


def _card(cid, rarity="R", quote=None):
    return Card(id=cid, rarity=rarity, storyline_id="sl", poi_id="p",
                title_zh="标题", title_en="Title",
                body_zh="正文", body_en="Body", quote=quote)


def test_game_payload_includes_board_and_cards():
    tiles = [BoardTile(index=0, type="poi", lat=1.0, lng=2.0, poi_id="p")]
    out = build_game_payload(tiles, [_card("c1")], [], [], night_from_index=13)
    assert out["board"][0]["type"] == "poi"
    assert out["cards"]["c1"]["rarity"] == "R"
    assert out["night_from_index"] == 13


def test_unverified_quote_is_stripped_from_card():
    bad = Quote(text_zh="x", text_original="x", source="",
                source_url="", verified=False)
    out = build_game_payload([], [_card("c1", quote=bad)], [], [], 13)
    assert "quote" not in out["cards"]["c1"]


def test_verified_quote_is_kept():
    good = Quote(text_zh="译文", text_original="orig", source="书, 1890",
                 source_url="https://a.example", verified=True)
    out = build_game_payload([], [_card("c1", quote=good)], [], [], 13)
    assert out["cards"]["c1"]["quote"]["text_original"] == "orig"


def test_unverified_street_card_is_dropped():
    ok = StreetCard(id="s1", category="rule", text_zh="a", text_en="a",
                    near_poi_id="p",
                    sources=["https://a.example", "https://b.example"],
                    verified=True)
    bad = StreetCard(id="s2", category="rule", text_zh="b", text_en="b",
                     near_poi_id="p", sources=["https://a.example"],
                     verified=True)
    out = build_game_payload([], [], [ok, bad], [], 13)
    assert list(out["street_cards"].keys()) == ["s1"]


def test_street_card_sources_not_leaked_to_frontend():
    ok = StreetCard(id="s1", category="rule", text_zh="a", text_en="a",
                    near_poi_id="p",
                    sources=["https://a.example", "https://b.example"],
                    verified=True)
    out = build_game_payload([], [], [ok], [], 13)
    assert "sources" not in out["street_cards"]["s1"]

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
    (web / "templates" / "board.html").write_text("<html>{{CITY_ID}}</html>", encoding="utf-8")
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
