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


class IsAuthorModeratorAdminOrReadOnly(permissions.BasePermission):
    """
    Разрешение: чтение для всех,
    изменение только для автора, модератора или администратора.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        is_author = obj.author == request.user
        is_moderator = (
            request.user.is_moderator
            if request.user.is_authenticated
            else False
        )
        is_admin = (
            request.user.is_admin
            if request.user.is_authenticated
            else False
        )
        return is_author or is_moderator or is_admin
