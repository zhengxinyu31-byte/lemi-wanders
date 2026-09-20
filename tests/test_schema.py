from pipeline.models import POI, StoryStop, StoryLine, Narrative
from pipeline.schema import (
    stops_for_storyline, visible_narrative, resolve_photo_spot,
)


def _stop(order, narrs, poi_id="p1", sl="sl1", override=None):
    return StoryStop(storyline_id=sl, poi_id=poi_id, order=order,
                     narrative=narrs, photo_spot_override=override)


def test_stops_sorted_by_order():
    sl = StoryLine(id="sl1", city="paris", title_zh="", title_en="",
                   theme="", summary_zh="", summary_en="",
                   stops=[_stop(3, []), _stop(1, []), _stop(2, [])])
    orders = [s.order for s in stops_for_storyline(sl)]
    assert orders == [1, 2, 3]


def test_visible_narrative_filters_low_confidence():
    stop = _stop(1, [
        Narrative("scene", "高", "high", "high"),
        Narrative("anecdote", "低", "low", "low"),
        Narrative("history", "中", "mid", "mid"),
    ])
    kept = [n.type for n in visible_narrative(stop)]
    assert kept == ["scene", "history"]  # low 被过滤


def test_shared_poi_isolated_between_storylines():
    # 同一 POI 在两条线各有 StoryStop,内容不串味(Review Focus #1)
    emily = _stop(6, [Narrative("scene", "Emily喝咖啡", "Emily", "high")],
                  poi_id="cafe", sl="emily-in-paris")
    philo = _stop(2, [Narrative("anecdote", "波伏娃写作", "Beauvoir", "high")],
                  poi_id="cafe", sl="existentialism")
    assert visible_narrative(emily)[0].text_zh == "Emily喝咖啡"
    assert visible_narrative(philo)[0].text_zh == "波伏娃写作"


def test_resolve_photo_spot_override_wins():
    poi = POI(id="cafe", city="paris", country="FR", name_zh="", name_en="",
              lat=1.0, lng=2.0, address_zh="", address_en="",
              default_photo_spot=Narrative("photo_spot", "默认机位", "default", "high"))
    override = Narrative("photo_spot", "专属机位", "special", "high")
    stop = _stop(1, [], override=override)
    assert resolve_photo_spot(poi, stop).text_zh == "专属机位"


def test_resolve_photo_spot_falls_back_to_poi_default():
    poi = POI(id="cafe", city="paris", country="FR", name_zh="", name_en="",
              lat=1.0, lng=2.0, address_zh="", address_en="",
              default_photo_spot=Narrative("photo_spot", "默认机位", "default", "high"))
    stop = _stop(1, [])
    assert resolve_photo_spot(poi, stop).text_zh == "默认机位"


def test_resolve_photo_spot_low_confidence_returns_none():
    poi = POI(id="cafe", city="paris", country="FR", name_zh="", name_en="",
              lat=1.0, lng=2.0, address_zh="", address_en="",
              default_photo_spot=Narrative("photo_spot", "弱机位", "weak", "low"))
    stop = _stop(1, [])
    assert resolve_photo_spot(poi, stop) is None


import json
import os
import tempfile

from pipeline.schema import load_card, load_chance, load_street_card


def _write(tmpdir, name, obj):
    p = os.path.join(tmpdir, name)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(obj, f)
    return p


def test_load_card_with_quote():
    with tempfile.TemporaryDirectory() as d:
        p = _write(d, "c.json", {
            "id": "paris-tour-eiffel-r", "rarity": "R",
            "storyline_id": "emily-in-paris", "poi_id": "tour-eiffel",
            "title_zh": "埃菲尔铁塔", "title_en": "Eiffel Tower",
            "body_zh": "正文", "body_en": "body",
            "quote": {"text_zh": "译文", "text_original": "orig",
                      "source": "La Vie errante, 1890",
                      "source_url": "https://fr.wikisource.org/x",
                      "verified": True},
        })
        card = load_card(p)
        assert card.rarity == "R"
        assert card.quote is not None
        assert card.quote.verified is True


def test_load_card_without_quote():
    with tempfile.TemporaryDirectory() as d:
        p = _write(d, "c.json", {
            "id": "paris-cafe-de-flore-r", "rarity": "R",
            "storyline_id": "emily-in-paris", "poi_id": "cafe-de-flore",
            "title_zh": "花神咖啡馆", "title_en": "Cafe de Flore",
            "body_zh": "正文", "body_en": "body",
        })
        assert load_card(p).quote is None


def test_load_street_card():
    with tempfile.TemporaryDirectory() as d:
        p = _write(d, "s.json", {
            "id": "paris-bonjour", "category": "etiquette",
            "text_zh": "进店先说 Bonjour", "text_en": "Say Bonjour first",
            "near_poi_id": "place-estrapade",
            "sources": ["https://a.example", "https://b.example"],
            "verified": True,
        })
        s = load_street_card(p)
        assert s.category == "etiquette"
        assert len(s.sources) == 2


def test_load_chance_question():
    with tempfile.TemporaryDirectory() as d:
        p = _write(d, "q.json", {
            "id": "paris-eiffel-petition",
            "question_zh": "铁塔当年被多少艺术家联名反对?",
            "question_en": "How many artists signed the protest?",
            "options_zh": ["7 位", "47 位", "300 位"],
            "options_en": ["7", "47", "300"],
            "answer_index": 1,
            "explain_zh": "1887 年《反对埃菲尔铁塔抗议书》有 47 人签署。",
            "explain_en": "The 1887 protest carried 47 signatures.",
        })
        q = load_chance(p)
        assert q["answer_index"] == 1
        assert len(q["options_zh"]) == 3
