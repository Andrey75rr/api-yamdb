from django.contrib import admin

from reviews.models import Category, Genre, Title


@admin.register(Title)
class TitleAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'year', 'category', 'rating')
    list_filter = ('category', 'genre', 'year')
    search_fields = ('name', 'description')
    filter_horizontal = ('genre',)


admin.site.register(Category)
admin.site.register(Genre)
