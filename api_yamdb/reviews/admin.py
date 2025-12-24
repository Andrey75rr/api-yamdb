from django.contrib import admin
from django.contrib.auth.models import Group

from reviews.models import (
    Category,
    Comment,
    Genre,
    Review,
    Title,
    TitleGenre,
)

admin.site.unregister(Group)


@admin.register(Category, Genre)
class SlugFieldModelAdmin(admin.ModelAdmin):
    """Класс для настройки отображения списковых моделей с полем slug."""

    list_display = ('id', 'name', 'slug')
    list_display_links = ['name']
    list_filter = ('name', 'slug')
    search_fields = ('name', 'slug')


class GenreTitleTabular(admin.TabularInline):
    """Класс для отображения и изменения жанров в карточке произведения."""

    model = TitleGenre
    extra = 1


@admin.register(Title)
class TitleAdmin(admin.ModelAdmin):
    """Класс с настройками управления произведениями в админ-панели."""

    list_display = ('id', 'name', 'year', 'category', 'get_title_genres')
    list_display_links = ['name']
    list_editable = ('category',)
    list_filter = ('category', 'genre', 'year')
    search_fields = ('name', 'description')
    inlines = [
        GenreTitleTabular
    ]
    exclude = ('genre',)


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    """Класс для настройки отображения комментариев."""

    list_display = ('id', 'text', 'review', 'author', 'pub_date')
    list_display_links = ['id']
    list_filter = ('review', 'author', 'pub_date')
    search_fields = ('text', 'review__text', 'author__username')


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    """Класс для настройки отображения отзывов."""

    list_display = ('id', 'title', 'text', 'author', 'score', 'pub_date')
    list_display_links = ['id']
    list_filter = ('title', 'score', 'author', 'pub_date')
    search_fields = ('text', 'title__name', 'author__username')
