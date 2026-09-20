from pipeline.models import ImageRef
from pipeline.images import pick_image, fingerprint, ImageFetcher


def _img(url, conf="high"):
    return ImageRef(url=url, thumb=url, author="a", license="CC",
                    source_page="s", confidence=conf)


def test_fingerprint_normalizes_url():
    a = fingerprint(_img("https://X.org/A.JPG?width=100"))
    b = fingerprint(_img("https://x.org/A.JPG"))
    assert a == b  # 去 query + 统一小写 host 后一致


def test_pick_image_takes_first_unused():
    used = set()
    poi_imgs = [_img("https://x.org/flore.jpg")]
    name_imgs = [_img("https://x.org/beauvoir.jpg")]
    got = pick_image([poi_imgs, name_imgs], used)
    assert got.url == "https://x.org/flore.jpg"
    assert len(used) == 1


def test_pick_image_skips_used_and_falls_back():
    used = {fingerprint(_img("https://x.org/flore.jpg"))}
    poi_imgs = [_img("https://x.org/flore.jpg")]       # 已用,跳过
    name_imgs = [_img("https://x.org/beauvoir.jpg")]   # 用这张
    got = pick_image([poi_imgs, name_imgs], used)
    assert got.url == "https://x.org/beauvoir.jpg"


def test_pick_image_returns_none_when_all_used():
    used = {fingerprint(_img("https://x.org/a.jpg"))}
    got = pick_image([[_img("https://x.org/a.jpg")]], used)
    assert got is None


def test_geosearch_maps_response_to_imagerefs():
    def fake_get(url, params=None, headers=None, timeout=None):
        class R:
            def raise_for_status(self): pass
            def json(self):
                return {"query": {"pages": {"1": {
                    "title": "File:Flore.jpg",
                    "imageinfo": [{"url": "https://x.org/Flore.jpg",
                                   "thumburl": "https://x.org/t/Flore.jpg",
                                   "extmetadata": {
                                       "Artist": {"value": "Jane"},
                                       "LicenseShortName": {"value": "CC BY"}}}],
                    "fullurl": "https://commons/Flore"}}}}
        return R()
    f = ImageFetcher(http_get=fake_get)
    imgs = f.geosearch(48.854, 2.332)
    assert imgs and imgs[0].confidence == "high"
    assert imgs[0].url == "https://x.org/Flore.jpg"
