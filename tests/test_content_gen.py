from pipeline.content_gen import (
    build_narrative_prompt, parse_narrative_response, generate_narrative,
)


def test_prompt_mentions_theme_and_poi_and_json():
    system, user = build_narrative_prompt("Emily in Paris", "Café de Flore")
    assert "Emily in Paris" in user
    assert "Café de Flore" in user
    assert "JSON" in system or "json" in system


def test_parse_valid_response():
    raw = '''[
      {"type":"scene","text_zh":"Emily喝咖啡","text_en":"Emily","confidence":"high","reason":"S1E2"},
      {"type":"anecdote","text_zh":"波伏娃","text_en":"Beauvoir","confidence":"mid","reason":"史料"}
    ]'''
    narrs = parse_narrative_response(raw)
    assert len(narrs) == 2
    assert narrs[0].type == "scene"


def test_parse_skips_invalid_type_and_bad_json():
    assert parse_narrative_response("not json at all") == []
    raw = '[{"type":"unknown_type","text_zh":"x","text_en":"x","confidence":"high"}]'
    assert parse_narrative_response(raw) == []  # type 不在枚举内


def test_parse_tolerates_json_wrapped_in_text():
    # LLM 常在 JSON 前后加解释文字
    raw = '好的,结果如下:\n[{"type":"history","text_zh":"h","text_en":"h","confidence":"high"}]\n以上'
    narrs = parse_narrative_response(raw)
    assert len(narrs) == 1 and narrs[0].type == "history"


def test_generate_narrative_filters_low_confidence():
    class FakeClient:
        def complete(self, system, user):
            return '[{"type":"scene","text_zh":"a","text_en":"a","confidence":"low"},'\
                   '{"type":"history","text_zh":"b","text_en":"b","confidence":"high"}]'
    narrs = generate_narrative(FakeClient(), "theme", "poi")
    assert [n.type for n in narrs] == ["history"]  # low 被过滤
