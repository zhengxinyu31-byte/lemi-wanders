"""Wikimedia Commons image fetching with degradation chain and dedup.

Degradation chain per POI: geo-nearby image (high) → name-search image
(mid) → nothing. A global used-fingerprint set prevents the same image
being reused across POIs in a storyline.
"""
from __future__ import annotations

from typing import Callable, List, Optional
from urllib.parse import urlparse

from pipeline.models import ImageRef

DEFAULT_TIMEOUT = 30
COMMONS_API = "https://commons.wikimedia.org/w/api.php"


def fingerprint(img: ImageRef) -> str:
    """Canonical fingerprint of an image URL (drop query, lowercase host)."""
    parsed = urlparse(img.url)
    return f"{parsed.netloc.lower()}{parsed.path.lower()}"


def pick_image(candidates: List[List[ImageRef]],
               used_fingerprints: set) -> Optional[ImageRef]:
    """Pick the first not-yet-used image following the degradation chain.

    candidates is an ordered list of tiers (e.g. [poi_images, name_images]).
    On success the chosen image's fingerprint is added to used_fingerprints.
    Returns None if every candidate is already used or the chain is empty.
    """
    for tier in candidates:
        for img in tier:
            fp = fingerprint(img)
            if fp not in used_fingerprints:
                used_fingerprints.add(fp)
                return img
    return None


class ImageFetcher:
    """Fetches images from Wikimedia Commons."""

    def __init__(self, http_get: Optional[Callable] = None,
                 timeout: int = DEFAULT_TIMEOUT) -> None:
        self._http_get = http_get
        self.timeout = timeout

    def _get(self):
        if self._http_get is not None:
            return self._http_get
        import requests
        return requests.get

    def _pages_to_imagerefs(self, data: dict, confidence: str) -> List[ImageRef]:
        pages = (data.get("query", {}) or {}).get("pages", {}) or {}
        out: List[ImageRef] = []
        for page in pages.values():
            info_list = page.get("imageinfo") or []
            if not info_list:
                continue
            info = info_list[0]
            meta = info.get("extmetadata", {}) or {}
            out.append(ImageRef(
                url=info.get("url", ""), thumb=info.get("thumburl", info.get("url", "")),
                author=(meta.get("Artist", {}) or {}).get("value", ""),
                license=(meta.get("LicenseShortName", {}) or {}).get("value", ""),
                source_page=page.get("fullurl", ""), confidence=confidence,
            ))
        return out

    def geosearch(self, lat: float, lng: float, radius_m: int = 200) -> List[ImageRef]:
        """Find images geotagged near (lat,lng); confidence=high."""
        params = {
            "action": "query", "format": "json", "generator": "geosearch",
            "ggscoord": f"{lat}|{lng}", "ggsradius": radius_m, "ggslimit": 10,
            "ggsnamespace": 6, "prop": "imageinfo",
            "iiprop": "url|extmetadata", "iiurlwidth": 800, "inprop": "url",
        }
        resp = self._get()(COMMONS_API, params=params,
                           headers={"User-Agent": "lemis-diary/0.1"},
                           timeout=self.timeout)
        resp.raise_for_status()
        return self._pages_to_imagerefs(resp.json(), "high")

    def name_search(self, name: str) -> List[ImageRef]:
        """Search images by name (person/work fallback); confidence=mid."""
        params = {
            "action": "query", "format": "json", "generator": "search",
            "gsrsearch": name, "gsrnamespace": 6, "gsrlimit": 10,
            "prop": "imageinfo", "iiprop": "url|extmetadata",
            "iiurlwidth": 800, "inprop": "url",
        }
        resp = self._get()(COMMONS_API, params=params,
                           headers={"User-Agent": "lemis-diary/0.1"},
                           timeout=self.timeout)
        resp.raise_for_status()
        return self._pages_to_imagerefs(resp.json(), "mid")
