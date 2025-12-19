from rest_framework.filters import BaseFilterBackend


class TitleFilterBackend(BaseFilterBackend):
    """ Кастомный фильтр для Title."""

    def filter_queryset(self, request, queryset, view):
        category_slug = request.query_params.get('category')
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)
        genre_slug = request.query_params.get('genre')
        if genre_slug:
            queryset = queryset.filter(genre__slug=genre_slug)
        name = request.query_params.get('name')
        if name:
            queryset = queryset.filter(name__icontains=name)
        year = request.query_params.get('year')
        if year:
            queryset = queryset.filter(year=int(year))
        return queryset
    
