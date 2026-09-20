# tests/test_frontend.py
import json
import os

WEB = os.path.join(os.path.dirname(__file__), "..", "web")


def test_i18n_files_have_same_keys():
    zh = json.load(open(os.path.join(WEB, "i18n", "zh.json"), encoding="utf-8"))
    en = json.load(open(os.path.join(WEB, "i18n", "en.json"), encoding="utf-8"))
    assert set(zh.keys()) == set(en.keys())  # 两语言 key 必须一致
    assert "switch_language" in zh


def test_board_html_loads_all_modules():
    html = open(os.path.join(WEB, "templates", "board.html"), encoding="utf-8").read()
    for mod in ("core/storage.js", "core/mapkit.js", "game/dice.js",
                "game/card.js", "game/tiles.js", "game/collection.js",
                "game/game.js", "game/ui.js"):
        assert mod in html, f"board.html must load {mod}"
    assert "maplibre-gl" in html
    assert "{{CITY_ID}}" in html


def test_game_css_has_mobile_layout_and_touch_targets():
    css = open(os.path.join(WEB, "assets", "styles", "game.css"),
               encoding="utf-8").read()
    assert "@media" in css, "mobile-first is a hard requirement"
    assert "44px" in css, "touch targets must be at least 44px"


def test_game_css_honours_reduced_motion():
    css = open(os.path.join(WEB, "assets", "styles", "game.css"),
               encoding="utf-8").read()
    assert "prefers-reduced-motion" in css


def test_animation_durations_match_the_spec():
    css = open(os.path.join(WEB, "assets", "styles", "game.css"),
               encoding="utf-8").read()
    for ms in ("100ms", "400ms", "150ms", "350ms"):
        assert ms in css, f"spec timing {ms} missing from game.css"
