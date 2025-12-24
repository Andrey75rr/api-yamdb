from rest_framework import filters, mixins, viewsets

from api.permissions import IsAdminOrReadOnly


class SafeUpdateViewSet(viewsets.ModelViewSet):
    """Базовый класс для вьюсетов, в которых метод PUT запрещен."""

    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']


class SlugModelViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet
):
    """Базовый вью для моделей-справочников с полем `slug`."""

    lookup_field = 'slug'
    filter_backends = (filters.SearchFilter,)
    search_fields = ['name']
    permission_classes = (IsAdminOrReadOnly,)
