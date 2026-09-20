from pipeline.models import City
from pipeline.geocode import PhotonProvider, geocode_place, in_bbox

PARIS = City(id="paris", name_zh="巴黎", name_en="Paris",
             center_lat=48.8566, center_lng=2.3522,
             bbox=(48.80, 2.20, 48.91, 2.47))  # (min_lat,min_lng,max_lat,max_lng)


def _fake_get(features):
    def get(url, params=None, headers=None, timeout=None):
        class R:
            def raise_for_status(self): pass
            def json(self): return {"features": features}
        assert timeout is not None  # timeout 必传
        return R()
    return get


def test_in_bbox():
    assert in_bbox(48.85, 2.33, PARIS.bbox) is True
    assert in_bbox(35.68, 139.76, PARIS.bbox) is False  # 东京不在巴黎 bbox


def test_geocode_place_accepts_result_in_city():
    feats = [{"geometry": {"coordinates": [2.33263, 48.85414]},  # [lng,lat]
              "properties": {"name": "Café de Flore", "city": "Paris"}}]
    provider = PhotonProvider(http_get=_fake_get(feats))
    coord = geocode_place("Café de Flore", PARIS, provider)
    assert coord == (48.85414, 2.33263)  # 返回 (lat,lng)


def test_geocode_place_rejects_wrong_city():
    # 同名店命中东京 → 落在巴黎 bbox 外 → 拒绝(Review Focus #2)
    feats = [{"geometry": {"coordinates": [139.7, 35.68]},
              "properties": {"name": "Café de Flore", "city": "Tokyo"}}]
    provider = PhotonProvider(http_get=_fake_get(feats))
    assert geocode_place("Café de Flore", PARIS, provider) is None


def test_geocode_place_no_features_returns_none():
    provider = PhotonProvider(http_get=_fake_get([]))
    assert geocode_place("Nowhere", PARIS, provider) is None
