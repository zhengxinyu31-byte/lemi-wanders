# tests/test_e2e_paris.py
import json
import os
from pipeline.run_paris import main

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_paris_build_offline_produces_dist():
    main(offline=True)  # 不联网配图
    data = os.path.join(ROOT, "dist", "data", "paris.json")
    assert os.path.exists(data)
    payload = json.load(open(data, encoding="utf-8"))
    assert payload["city"]["id"] == "paris"
    assert len(payload["pois"]) >= 6
    # 至少一条故事线,且其 stops 有序、引用真实 POI
    sl = payload["storylines"][0]
    orders = [s["order"] for s in sl["stops"]]
    assert orders == sorted(orders)
    for s in sl["stops"]:
        assert s["poi_id"] in payload["pois"]
    assert os.path.exists(os.path.join(ROOT, "dist", "index.html"))


def test_built_payload_has_playable_board(tmp_path):
    import json
    import os
    import subprocess
    env = dict(os.environ, LEMI_OFFLINE="1")
    subprocess.run(["python", "-m", "pipeline.run_paris"], check=True, env=env)
    d = json.load(open("dist/data/paris.json", encoding="utf-8"))

    assert len(d["board"]) == 20
    assert d["board"][0]["type"] == "poi"
    assert d["board"][-1]["type"] == "poi"
    assert d["night_from_index"] == 13

    # 每个非 POI 格都必须挂到真实内容上,否则玩家会走到空格子
    pools = {"street": d["street_cards"], "chance": d["chance"],
             "easter": d["cards"]}
    for tile in d["board"]:
        if tile["type"] in pools:
            assert tile.get("content_id") in pools[tile["type"]], (
                f"tile {tile['index']} ({tile['type']}) points at missing content")

    assert len(d["cards"]) == 10
    assert len([c for c in d["cards"].values() if c["rarity"] == "R"]) == 7
    assert len(d["street_cards"]) == 5


def test_dist_has_both_mode_pages():
    import os
    assert os.path.isfile("dist/index.html")
    assert os.path.isfile("dist/codex.html")
    for mod in ("core/storage.js", "core/mapkit.js", "game/game.js",
                "codex/codex.js"):
        assert os.path.isfile(os.path.join("dist", "assets", mod)), mod
