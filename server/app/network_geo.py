from __future__ import annotations

import ipaddress
import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import geoip2.database
from geoip2.errors import AddressNotFoundError


GEOIP_CITY_DB = os.getenv("GEOIP_CITY_DB", "/geoip/GeoLite2-City.mmdb")
NETWORK_GEO_REQUIRED = os.getenv("NETWORK_GEO_REQUIRED", "false").lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class NetworkLocation:
    country_code: str | None
    country_name: str | None
    region_name: str | None
    city_name: str | None
    latitude: float | None
    longitude: float | None
    accuracy_km: int | None


@lru_cache(maxsize=1)
def _reader() -> geoip2.database.Reader | None:
    path = Path(GEOIP_CITY_DB)
    if not path.exists():
        if NETWORK_GEO_REQUIRED:
            raise RuntimeError(f"GeoIP database not found: {path}")
        return None
    return geoip2.database.Reader(str(path))


def validate_geo_configuration() -> None:
    _reader()


def lookup_network_location(value: str | None) -> NetworkLocation | None:
    if not value:
        return None

    try:
        ip = ipaddress.ip_address(value)
    except ValueError:
        return None

    if not ip.is_global:
        return None

    reader = _reader()
    if reader is None:
        return None

    try:
        response = reader.city(value)
    except (AddressNotFoundError, ValueError):
        return None

    subdivision = response.subdivisions.most_specific
    return NetworkLocation(
        country_code=response.country.iso_code,
        country_name=response.country.name,
        region_name=subdivision.name,
        city_name=response.city.name,
        latitude=response.location.latitude,
        longitude=response.location.longitude,
        accuracy_km=response.location.accuracy_radius,
    )
