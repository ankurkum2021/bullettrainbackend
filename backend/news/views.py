from django.http import Http404, JsonResponse

from news.models import NewsArticle
from news.pipeline.rewrite import source_site_label, write_feed_teaser


def _serialize(article: NewsArticle) -> dict:
    site = source_site_label(article.source_name)
    return {
        "id": article.slug,
        "title": article.title,
        "teaser": article.teaser or write_feed_teaser(article.title),
        "summary": article.summary,
        "body": article.body,
        "date": article.published_on.isoformat(),
        "sourceUrl": article.source_url,
        "sourceName": article.source_name,
        "sourceSite": site,
        "stationSlug": article.related_station.slug if article.related_station_id else None,
    }


def news_list(request):
    try:
        limit = min(int(request.GET.get("limit", 50)), 100)
    except (TypeError, ValueError):
        limit = 50
    qs = NewsArticle.objects.filter(is_published=True).order_by("-published_on")[:limit]
    return JsonResponse({"updates": [_serialize(a) for a in qs]})


def news_detail(request, slug: str):
    try:
        article = NewsArticle.objects.get(slug=slug, is_published=True)
    except NewsArticle.DoesNotExist as exc:
        raise Http404 from exc
    return JsonResponse(_serialize(article))