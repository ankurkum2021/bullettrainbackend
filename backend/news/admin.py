from django.contrib import admin

from news.models import NewsArticle


@admin.register(NewsArticle)
class NewsArticleAdmin(admin.ModelAdmin):
    list_display = ("title", "published_on", "source_name", "is_published", "updated_at")
    list_filter = ("is_published", "source_name", "published_on")
    search_fields = ("title", "summary", "slug", "source_fingerprint")
    date_hierarchy = "published_on"
    ordering = ("-published_on",)