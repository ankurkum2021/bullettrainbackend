from django.http import Http404, JsonResponse

from catalog.models import Station
from places.models import Place, PlaceKind, PlaceSection


def _serialize_kind(kind: PlaceKind) -> dict:
    return {
        "slug": kind.slug,
        "label": kind.label,
        "icon": kind.icon or "",
        "description": kind.description,
    }


def place_kind_list(_request):
    kinds = PlaceKind.objects.all()
    return JsonResponse({"kinds": [_serialize_kind(k) for k in kinds]})


def _serialize_place(place: Place) -> dict:
    return {
        "slug": place.slug,
        "name": place.name,
        "note": place.note,
        "distanceKm": float(place.distance_km) if place.distance_km is not None else None,
        "externalUrl": place.external_url,
        "kind": place.kind.slug,
        "kindLabel": place.kind.label,
        "kindIcon": place.kind.icon or "",
        "sectionSlug": place.section.slug if place.section_id else None,
        "sectionLabel": place.section.label if place.section_id else None,
        "tags": place.tag_list,
        "stationSlug": place.station.slug,
    }


def _serialize_section(section: PlaceSection, places: list[Place]) -> dict:
    return {
        "slug": section.slug,
        "label": section.label,
        "icon": section.icon or "",
        "panelTitle": section.panel_title or "",
        "places": [_serialize_place(p) for p in places],
    }


def place_list(request):
    station_slug = request.GET.get("station", "").strip()
    kind_slug = request.GET.get("kind", "").strip()
    corridor_slug = request.GET.get("corridor", "").strip()

    qs = (
        Place.objects.filter(is_published=True)
        .select_related("station", "station__corridor", "kind", "section")
        .order_by("sort_order", "name")
    )

    if station_slug:
        qs = qs.filter(station__slug=station_slug)
    if kind_slug:
        qs = qs.filter(kind__slug=kind_slug)
    if corridor_slug:
        qs = qs.filter(station__corridor__slug=corridor_slug)

    return JsonResponse({"places": [_serialize_place(p) for p in qs]})


def station_places(request, station_slug: str):
    try:
        station = Station.objects.get(slug=station_slug)
    except Station.DoesNotExist as exc:
        raise Http404 from exc

    sections = list(
        PlaceSection.objects.filter(station=station)
        .prefetch_related("places__kind")
        .order_by("sort_order", "slug")
    )
    places = list(
        Place.objects.filter(station=station, is_published=True)
        .select_related("kind", "section")
        .order_by("sort_order", "name")
    )

    by_section: dict[int | None, list[Place]] = {}
    for place in places:
        key = place.section_id
        by_section.setdefault(key, []).append(place)

    panel_payload = []
    for section in sections:
        panel_places = by_section.pop(section.id, [])
        if panel_places:
            panel_payload.append(_serialize_section(section, panel_places))

    ungrouped = by_section.pop(None, [])
    for kind_slug, group in _group_by_kind(ungrouped).items():
        panel_payload.append(
            {
                "slug": kind_slug,
                "label": group[0].kind.label if group else kind_slug,
                "icon": group[0].kind.icon if group else "",
                "panelTitle": "",
                "places": [_serialize_place(p) for p in group],
            }
        )

    # Any places whose section id was deleted
    for orphan in by_section.values():
        for kind_slug, group in _group_by_kind(orphan).items():
            panel_payload.append(
                {
                    "slug": kind_slug,
                    "label": group[0].kind.label,
                    "icon": group[0].kind.icon or "",
                    "panelTitle": "",
                    "places": [_serialize_place(p) for p in group],
                }
            )

    return JsonResponse(
        {
            "stationSlug": station.slug,
            "stationName": station.name,
            "corridorSlug": station.corridor.slug,
            "lead": station.explore_lead or "",
            "panels": panel_payload,
        }
    )


def _group_by_kind(places: list[Place]) -> dict[str, list[Place]]:
    out: dict[str, list[Place]] = {}
    for place in places:
        out.setdefault(place.kind.slug, []).append(place)
    return out