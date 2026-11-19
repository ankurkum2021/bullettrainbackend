from django.http import JsonResponse

from catalog.models import Corridor, Station


def corridor_list(request):
    rows = [
        {
            "slug": c.slug,
            "name": c.name,
            "shortName": c.short_name or c.name,
            "lengthKm": c.length_km,
            "phase": c.phase,
            "status": c.status,
        }
        for c in Corridor.objects.all()
    ]
    return JsonResponse({"corridors": rows})


def station_list(request):
    corridor_slug = request.GET.get("corridor")
    qs = Station.objects.select_related("corridor")
    if corridor_slug:
        qs = qs.filter(corridor__slug=corridor_slug)
    rows = [
        {
            "slug": s.slug,
            "name": s.name,
            "corridorSlug": s.corridor.slug,
            "stateCode": s.state_code,
            "order": s.sort_order,
            "live": s.is_live,
        }
        for s in qs
    ]
    return JsonResponse({"stations": rows})