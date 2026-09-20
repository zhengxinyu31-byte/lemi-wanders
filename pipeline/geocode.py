"""Geocoding with city-biased Photon and bbox validation.

Providers follow the strategy pattern (abc.ABC). Results must fall inside
the target city's bbox to be accepted, preventing same-name hits in the
wrong city.
"""
from __future__ import annotations

import abc
from typing import Callable, Optional, Tuple

from pipeline.models import City

DEFAULT_TIMEOUT = 30
PHOTON_URL = "https://photon.komoot.io/api"


def in_bbox(lat: float, lng: float, bbox: Tuple[float, float, float, float]) -> bool:
    """Return True if (lat,lng) is inside bbox=(min_lat,min_lng,max_lat,max_lng)."""
    min_lat, min_lng, max_lat, max_lng = bbox
    return min_lat <= lat <= max_lat and min_lng <= lng <= max_lng


class GeocodeProvider(abc.ABC):
    """Strategy interface for a geocoding backend."""

    @abc.abstractmethod
    def geocode(self, query: str, city: City) -> Optional[Tuple[float, float]]:
        """Return (lat, lng) for query near city, or None if not found."""


class PhotonProvider(GeocodeProvider):
    """Photon (OSM) geocoder with city-center bias."""

    def __init__(self, http_get: Optional[Callable] = None,
                 timeout: int = DEFAULT_TIMEOUT) -> None:
        self._http_get = http_get
        self.timeout = timeout

    def _get(self):
        if self._http_get is not None:
            return self._http_get
        import requests
        return requests.get

    def geocode(self, query: str, city: City) -> Optional[Tuple[float, float]]:
        """Query Photon biased to the city center; return first (lat,lng)."""
        params = {"q": query, "limit": 1, "lang": "en",
                  "lon": city.center_lng, "lat": city.center_lat}
        resp = self._get()(PHOTON_URL, params=params,
                           headers={"User-Agent": "lemis-diary/0.1"},
                           timeout=self.timeout)
        resp.raise_for_status()
        feats = resp.json().get("features") or []
        if not feats:
            return None
        lng, lat = feats[0]["geometry"]["coordinates"]  # GeoJSON = [lng, lat]
        return (float(lat), float(lng))


def geocode_place(query: str, city: City,
                  provider: GeocodeProvider) -> Optional[Tuple[float, float]]:
    """Geocode query and accept the result only if it falls in city.bbox."""
    coord = provider.geocode(query, city)
    if coord is None:
        return None
    lat, lng = coord
    if not in_bbox(lat, lng, city.bbox):
        return None
    return (lat, lng)
