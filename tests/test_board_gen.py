from pipeline.board_gen import allocate_filler, haversine_km, interpolate


def test_haversine_known_distance():
    # Emily 的公寓 → 先贤祠,实测约 0.21 km
    d = haversine_km((48.8443, 2.3487), (48.8462, 2.3464))
    assert 0.15 < d < 0.30


def test_allocate_filler_gives_every_gap_at_least_one():
    gaps = [0.21, 1.14, 1.25, 0.84, 1.61, 1.94]
    out = allocate_filler(gaps, 13)
    assert sum(out) == 13
    assert min(out) >= 1


def test_allocate_filler_longer_gap_gets_more():
    gaps = [0.21, 1.14, 1.25, 0.84, 1.61, 1.94]
    out = allocate_filler(gaps, 13)
    assert out[5] > out[0]  # 1.94km 段应多于 0.21km 段


def test_allocate_filler_handles_total_equal_to_gap_count():
    assert allocate_filler([1.0, 2.0, 3.0], 3) == [1, 1, 1]


def test_allocate_filler_raises_when_total_too_small():
    try:
        allocate_filler([1.0, 2.0, 3.0], 2)
    except ValueError:
        return
    raise AssertionError("expected ValueError when total < number of gaps")


def test_interpolate_midpoint():
    lat, lng = interpolate((0.0, 0.0), (2.0, 4.0), 0.5)
    assert abs(lat - 1.0) < 1e-9
    assert abs(lng - 2.0) < 1e-9


import glob
import json
import os

from pipeline.board_gen import build_board
from pipeline.schema import load_poi, load_storyline

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FILLER_PLAN = ["street", "chance", "photo", "street", "easter", "street",
               "chance", "photo", "street", "easter", "chance", "street",
               "easter"]


def _load_real():
    pois = {}
    for p in glob.glob(os.path.join(ROOT, "content", "pois", "*.json")):
        poi = load_poi(p)
        pois[poi.id] = poi
    sl = load_storyline(os.path.join(ROOT, "content", "storylines",
                                     "emily-in-paris.json"))
    return sl, pois


def test_real_board_has_twenty_tiles():
    sl, pois = _load_real()
    tiles = build_board(sl, pois, FILLER_PLAN)
    assert len(tiles) == 20


def test_real_board_starts_and_ends_on_poi():
    sl, pois = _load_real()
    tiles = build_board(sl, pois, FILLER_PLAN)
    assert tiles[0].type == "poi"
    assert tiles[0].poi_id == "place-estrapade"
    assert tiles[-1].type == "poi"
    assert tiles[-1].poi_id == "tour-eiffel"


def test_no_two_poi_tiles_adjacent():
    sl, pois = _load_real()
    tiles = build_board(sl, pois, FILLER_PLAN)
    for a, b in zip(tiles, tiles[1:]):
        assert not (a.type == "poi" and b.type == "poi")


def test_indices_are_sequential():
    sl, pois = _load_real()
    tiles = build_board(sl, pois, FILLER_PLAN)
    assert [t.index for t in tiles] == list(range(20))


def test_photo_tiles_get_the_next_pois_id():
    """Photo tiles are dead squares unless attached to a POI. _attach_content
    hangs each photo tile on the next POI down the board ("get your shot ready
    for the next stop"), so resolveTile can find images to show."""
    from pipeline.run_paris import _attach_content
    sl, pois = _load_real()
    tiles = build_board(sl, pois, FILLER_PLAN)
    content_map = {
        "street": ["s1"], "chance": ["c1"], "easter": ["e1"],
    }
    _attach_content(tiles, content_map)
    photos = [t for t in tiles if t.type == "photo"]
    assert photos, "board must contain photo tiles"
    for t in photos:
        assert t.poi_id, f"photo tile {t.index} must carry a poi_id"
        # the assigned POI is the first POI strictly after this tile
        nxt = next(p.poi_id for p in tiles
                   if p.index > t.index and p.type == "poi")
        assert t.poi_id == nxt
