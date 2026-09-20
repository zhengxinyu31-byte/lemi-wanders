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
