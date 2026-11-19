from __future__ import annotations

import re

from catalog.models import Station


def _patterns_for_station(station: Station) -> list[str]:
    patterns: list[str] = [station.slug.replace("-", " "), station.name.lower()]
    bare = re.sub(r"[^a-z0-9\s]", " ", station.name.lower())
    patterns.append(bare)
    if "/" in station.name:
        for part in station.name.split("/"):
            patterns.append(part.strip().lower())
    if station.slug == "mumbai-bkc":
        patterns.extend(["bkc", "bandra kurla", "mumbai bkc"])
    if station.slug == "anand-nadiad":
        patterns.extend(["anand", "nadiad"])
    if station.slug == "bilimora":
        patterns.extend(["bilimora", "surat–bilimora", "surat-bilimora"])
    return [p for p in patterns if len(p) >= 3]


def guess_related_station(title: str, summary: str = "") -> Station | None:
    text = f"{title} {summary}".lower()
    stations = list(Station.objects.all())
    best: tuple[int, Station] | None = None

    for station in stations:
        for pattern in _patterns_for_station(station):
            if pattern and pattern in text:
                score = len(pattern)
                if best is None or score > best[0]:
                    best = (score, station)

    return best[1] if best else None