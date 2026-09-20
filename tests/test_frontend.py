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
                "game/card.js", "game/board_view.js", "game/tiles.js",
                "game/collection.js", "game/game.js", "game/ui.js"):
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
    """时长的真实来源是 base.css 的 token,game.css 通过 var() 引用。"""
    base = open(os.path.join(WEB, "assets", "styles", "base.css"),
                encoding="utf-8").read()
    # 逐条断言 token 定义,改动任一数值都会让测试变红
    for token, ms in (("--t-press", "100ms"), ("--t-dice", "400ms"),
                      ("--t-walk", "1000ms"), ("--t-card-out", "150ms"),
                      ("--t-card-develop", "350ms"), ("--t-card-set", "100ms"),
                      ("--t-info", "3000ms")):
        assert f"{token}: {ms}" in base, f"{token} must be {ms}"

    game = open(os.path.join(WEB, "assets", "styles", "game.css"),
                encoding="utf-8").read()
    # game.css 必须真的引用这些 token,而不是写死或漏用
    for token in ("--t-press", "--t-dice", "--t-walk", "--t-card-out",
                  "--t-card-develop"):
        assert f"var({token})" in game, f"game.css must use var({token})"


def test_codex_css_avoids_vh_units():
    css = open(os.path.join(WEB, "assets", "styles", "codex.css"),
               encoding="utf-8").read()
    import re
    # dvh is fine; bare vh retriggers resize while scrolling on mobile
    assert not re.search(r"\d+vh\b", css), "codex.css must not use vh units"


def test_codex_html_loads_scrollama():
    html = open(os.path.join(WEB, "templates", "codex.html"),
                encoding="utf-8").read()
    assert "scrollama" in html
    assert "essential" in html, "flyTo must pass essential:true"
