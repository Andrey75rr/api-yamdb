from django.contrib import admin

from reviews.models import Category, Genre, Title


@admin.register(Title)
class PostAdmin(admin.ModelAdmin):
    """list_display = ('pk', 'text', 'pub_date', 'author')
    search_fields = ('text',)
    list_filter = ('pub_date',)
    empty_value_display = '-пусто-'"""


admin.site.register(Category)
admin.site.register(Genre)
