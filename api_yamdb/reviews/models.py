from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """Кастомная модель пользователя для YaMDb."""

    class Role(models.TextChoices):
        USER = 'user', _('Пользователь')
        MODERATOR = 'moderator', _('Модератор')
        ADMIN = 'admin', _('Администратор')

    email = models.EmailField(
        _('email address'),
        unique=True,
        blank=False,
        null=False
    )

    bio = models.TextField(
        _('биография'),
        blank=True,
    )

    role = models.CharField(
        _('роль'),
        max_length=20,
        choices=Role.choices,
        default=Role.USER
    )

    confirmation_code = models.CharField(
        _('код подтверждения'),
        max_length=6,
        blank=True,
        null=True
    )

    class Meta:
        ordering = ['username']
        verbose_name = _('Пользователь')
        verbose_name_plural = _('Пользователи')

    def __str__(self):
        return self.username

    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN or self.is_superuser

    @property
    def is_moderator(self):
        return self.role == self.Role.MODERATOR
