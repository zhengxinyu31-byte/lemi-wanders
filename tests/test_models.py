from pipeline.models import (
    ImageRef, Narrative, POI, StoryStop, StoryLine, City,
    meets_threshold, CONFIDENCE_ORDER, NARRATIVE_TYPES,
)


def test_meets_threshold_default_mid():
    assert meets_threshold("high") is True
    assert meets_threshold("mid") is True
    assert meets_threshold("low") is False


def test_meets_threshold_unknown_is_false():
    # 未知置信度按最保守处理:不展示
    assert meets_threshold("") is False
    assert meets_threshold("garbage") is False


def test_poi_holds_shared_fields_only():
    poi = POI(
        id="cafe-de-flore", city="paris", country="France",
        name_zh="花神咖啡馆", name_en="Café de Flore",
        lat=48.85414, lng=2.33263,
        address_zh="圣日耳曼大道172号", address_en="172 Bd Saint-Germain",
        base_images=[], practical=None, default_photo_spot=None,
    )
    assert poi.id == "cafe-de-flore"
    assert poi.lat == 48.85414


def test_storystop_carries_narrative():
    stop = StoryStop(
        storyline_id="emily-in-paris", poi_id="cafe-de-flore", order=6,
        narrative=[Narrative(type="scene", text_zh="Emily 在此喝咖啡",
                             text_en="Emily has coffee here", confidence="high")],
    )
    assert stop.narrative[0].type == "scene"
    assert stop.order == 6


def test_narrative_types_constant():
    assert "anecdote" in NARRATIVE_TYPES
    assert CONFIDENCE_ORDER["high"] > CONFIDENCE_ORDER["low"]
