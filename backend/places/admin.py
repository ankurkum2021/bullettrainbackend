from django.contrib import admin

from places.models import Place, PlaceKind, PlaceSection


@admin.register(PlaceKind)
class PlaceKindAdmin(admin.ModelAdmin):
    list_display = ("label", "slug", "icon", "sort_order")
    search_fields = ("label", "slug")
    prepopulated_fields = {"slug": ("label",)}
    ordering = ("sort_order", "slug")


class PlaceInline(admin.TabularInline):
    model = Place
    extra = 0
    fields = ("slug", "name", "kind", "distance_km", "sort_order", "is_published")
    ordering = ("sort_order",)


@admin.register(PlaceSection)
class PlaceSectionAdmin(admin.ModelAdmin):
    list_display = ("label", "station", "slug", "sort_order")
    list_filter = ("station__corridor",)
    search_fields = ("label", "slug", "station__name", "station__slug")
    inlines = [PlaceInline]


@admin.register(Place)
class PlaceAdmin(admin.ModelAdmin):
    list_display = ("name", "station", "kind", "section", "distance_km", "is_published")
    list_filter = ("kind", "is_published", "station__corridor")
    search_fields = ("name", "slug", "note", "tags")
    autocomplete_fields = ("station", "kind", "section")
    ordering = ("station", "sort_order")