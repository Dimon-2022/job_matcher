import re

COUNTRY_ALIASES = {
    "AT": ("Austria", ["austria", "österreich", "osterreich", "vienna", "wien", "graz", "linz", "salzburg", "innsbruck"]),
    "BE": ("Belgium", ["belgium", "belgië", "belgique", "brussels", "bruxelles", "antwerp", "ghent"]),
    "BG": ("Bulgaria", ["bulgaria", "sofia", "plovdiv", "varna"]),
    "CH": ("Switzerland", ["switzerland", "schweiz", "suisse", "zurich", "zürich", "geneva", "genève", "basel", "bern", "lausanne"]),
    "CZ": ("Czechia", ["czechia", "czech republic", "česko", "cesko", "prague", "praha", "brno", "ostrava", "plzeň", "plzen"]),
    "DE": ("Germany", ["germany", "deutschland", "berlin", "munich", "münchen", "muenchen", "hamburg", "frankfurt",
                       "cologne", "köln", "koeln", "stuttgart", "düsseldorf", "dusseldorf", "leipzig", "dresden",
                       "nuremberg", "nürnberg", "hannover", "bremen", "karlsruhe", "mannheim", "bonn"]),
    "DK": ("Denmark", ["denmark", "danmark", "copenhagen", "københavn", "aarhus"]),
    "EE": ("Estonia", ["estonia", "eesti", "tallinn", "tartu"]),
    "ES": ("Spain", ["spain", "españa", "espana", "madrid", "barcelona", "valencia", "seville", "sevilla", "malaga", "málaga"]),
    "FI": ("Finland", ["finland", "suomi", "helsinki", "espoo", "tampere"]),
    "FR": ("France", ["france", "paris", "lyon", "marseille", "toulouse", "lille", "bordeaux"]),
    "GB": ("United Kingdom", ["united kingdom", "uk", "great britain", "england", "scotland", "london",
                              "manchester", "edinburgh", "birmingham", "bristol", "cambridge", "oxford"]),
    "GR": ("Greece", ["greece", "athens", "thessaloniki"]),
    "HR": ("Croatia", ["croatia", "hrvatska", "zagreb"]),
    "HU": ("Hungary", ["hungary", "magyarország", "budapest", "debrecen", "szeged"]),
    "IE": ("Ireland", ["ireland", "dublin", "galway"]),
    "IT": ("Italy", ["italy", "italia", "rome", "roma", "milan", "milano", "turin", "torino", "bologna"]),
    "LT": ("Lithuania", ["lithuania", "lietuva", "vilnius", "kaunas"]),
    "LU": ("Luxembourg", ["luxembourg"]),
    "LV": ("Latvia", ["latvia", "latvija", "riga"]),
    "NL": ("Netherlands", ["netherlands", "nederland", "holland", "amsterdam", "rotterdam", "utrecht", "eindhoven", "the hague"]),
    "NO": ("Norway", ["norway", "norge", "oslo", "bergen"]),
    "PL": ("Poland", ["poland", "polska", "warsaw", "warszawa", "kraków", "krakow", "wrocław", "wroclaw",
                      "gdańsk", "gdansk", "poznań", "poznan", "łódź", "lodz"]),
    "PT": ("Portugal", ["portugal", "lisbon", "lisboa", "porto"]),
    "RO": ("Romania", ["romania", "românia", "bucharest", "bucurești", "cluj", "iasi", "iași", "timisoara"]),
    "RS": ("Serbia", ["serbia", "srbija", "belgrade", "beograd", "novi sad"]),
    "SE": ("Sweden", ["sweden", "sverige", "stockholm", "gothenburg", "göteborg", "malmö", "malmo"]),
    "SI": ("Slovenia", ["slovenia", "slovenija", "ljubljana"]),
    "SK": ("Slovakia", ["slovakia", "slovensko", "bratislava", "košice", "kosice", "žilina", "zilina",
                        "nitra", "prešov", "presov", "trnava", "banská bystrica", "banska bystrica"]),
    "UA": ("Ukraine", ["ukraine", "україна", "kyiv", "kiev", "lviv", "kharkiv", "odesa", "dnipro"]),
}

COUNTRY_NAMES = {code: name for code, (name, _) in COUNTRY_ALIASES.items()}
COUNTRY_CHOICES = sorted(COUNTRY_NAMES.items(), key=lambda item: item[1])

_PATTERNS = {
    code: re.compile(r"\b(" + "|".join(re.escape(alias) for alias in aliases) + r")\b", re.IGNORECASE)
    for code, (_, aliases) in COUNTRY_ALIASES.items()
}


def detect_country(text):
    if not text:
        return ""
    for code, pattern in _PATTERNS.items():
        if pattern.search(text):
            return code
    return ""


def flag(code):
    if not code or len(code) != 2:
        return ""
    return "".join(chr(0x1F1E6 + ord(letter) - ord("A")) for letter in code.upper())