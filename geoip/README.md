# GeoIP database directory

Place the licensed or otherwise permitted city-level MMDB database here as:

```text
geoip/GeoLite2-City.mmdb
```

The MMDB file is intentionally excluded from Git.

YUDE Asset Guard uses it only on the server to derive an approximate country, region and city from the public IP observed by the API.

No coordinate-level location is stored by this module.

Set `NETWORK_GEO_REQUIRED=true` in production if the API must refuse startup when the database is missing.
