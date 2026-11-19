from django.contrib import admin

from catalog.models import Corridor, Station


class StationInline(admin.TabularInline):
    model = Station
    extra = 0
    fields = ("slug", "name", "state_code", "sort_order", "is_live")
    ordering = ("sort_order",)


@admin.register(Corridor)
class CorridorAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "phase", "length_km", "short_name")
    list_filter = ("phase",)
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    inlines = [StationInline]


@admin.register(Station)
class StationAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "corridor", "state_code", "sort_order", "is_live")
    list_filter = ("corridor", "state_code", "is_live")
    search_fields = ("name", "slug")
    ordering = ("corridor", "sort_order")