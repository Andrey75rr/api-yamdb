from rest_framework import mixins, filters, status, viewsets
from rest_framework.response import Response

from api.permissions import IsAdminOrReadOnly


class SafeUpdateViewSet(viewsets.ModelViewSet):
    """Базовый класс для вьюсетов, в которых метод PUT запрещен."""

    def update(self, request, *args, **kwargs):
        """Запретит метод PUT (вернет ошибку 405)."""
        if request.method == 'PUT':
            return Response(
                {
                    "detail": (
                        "Полное обновление (PUT) запрещено. "
                        "Используйте PATCH для частичных изменений."
                    )
                },
                status=status.HTTP_405_METHOD_NOT_ALLOWED
            )
        return super().update(request, *args, **kwargs)
    

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
