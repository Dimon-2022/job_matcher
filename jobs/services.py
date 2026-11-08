import requests

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
HEADERS = {"User-Agent": "JobMatcher/1.0 (student project)"}

def geocode(query):
    response = requests.get(
        NOMINATIM_URL,
        params={"q": query, "format": "json", "limit": 1, "accept-language": "en"},
        headers=HEADERS,
        timeout=5
    )
    response.raise_for_status()
    results = response.json()

    if not results:
        return None

    place = results[0]
    return {
        "name": place["display_name"].split(",")[0],
        "lat": float(place["lat"]),
        "lon": float(place["lon"]),
    }