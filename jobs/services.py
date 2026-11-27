import requests

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
HEADERS = {"User-Agent": "JobMatcher/1.0 (student project)"}

def geocode(query):
    response = requests.get(
        "https://nominatim.openstreetmap.org/search",
        params={"q": query, "format": "json", "limit": 1, "addressdetails": 1},
        headers={"User-Agent": "JobMatcher/1.0 (student project)"},
        timeout=5,
    )
    response.raise_for_status()
    results = response.json()
    if not results:
        return None
    item = results[0]
    return {
        "name": item["display_name"].split(",")[0],
        "lat": float(item["lat"]),
        "lon": float(item["lon"]),
        "country": (item.get("address") or {}).get("country_code", "").upper(),
    }