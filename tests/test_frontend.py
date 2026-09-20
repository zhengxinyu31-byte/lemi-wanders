# tests/test_frontend.py
import json
import os

WEB = os.path.join(os.path.dirname(__file__), "..", "web")


def test_i18n_files_have_same_keys():
    zh = json.load(open(os.path.join(WEB, "i18n", "zh.json"), encoding="utf-8"))
    en = json.load(open(os.path.join(WEB, "i18n", "en.json"), encoding="utf-8"))
    assert set(zh.keys()) == set(en.keys())  # 两语言 key 必须一致
    assert "switch_language" in zh


def test_city_html_references_maplibre_and_app():
    html = open(os.path.join(WEB, "templates", "city.html"), encoding="utf-8").read()
    assert "maplibre-gl" in html
    assert "app.js" in html
    assert "__CITY_ID__" in html  # 构建期占位符


def test_app_js_defines_picklang_and_visible():
    js = open(os.path.join(WEB, "assets", "app.js"), encoding="utf-8").read()
    assert "function pickLang" in js
    assert "function visibleForLang" in js
    assert "localStorage" in js
