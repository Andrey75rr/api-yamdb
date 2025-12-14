from rest_framework import permissions


class IsAdmin(permissions.BasePermission):
    """Разрешение только для администраторов."""

    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.user.is_admin or request.user.is_staff
        )


class IsAdminOrReadOnly(permissions.BasePermission):
    """Разрешение: чтение для всех, изменение только для админов."""

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True

        return request.user.is_authenticated and (
            request.user.is_admin or request.user.is_staff
        )


class IsAuthorOrReadOnly(permissions.BasePermission):
    """Разрешение: чтение для всех, изменение только для автора."""

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.author == request.user
