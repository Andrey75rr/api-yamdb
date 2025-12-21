from django.contrib.auth.models import AbstractUser
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone
from django.utils.text import Truncator
from django.utils.translation import gettext_lazy as _

from core.constants import (
    MAX_SCORE_RATING,
    MIN_SCORE_RATING,
    NAME_FIELD_LENGTH,
    STR_LENGTH,
)
from core.models import SlugFieldListModel


class Category(SlugFieldListModel):
    """Модель категории произведения."""

    class Meta(SlugFieldListModel.Meta):
        verbose_name = _('Категория')
        verbose_name_plural = _('Категории')


class Genre(SlugFieldListModel):
    """Модель категории произведения."""

    class Meta(SlugFieldListModel.Meta):
        verbose_name = _('Жанр')
        verbose_name_plural = _('Жанры')


class Title(models.Model):
    name = models.CharField(
        db_index=True,
        max_length=NAME_FIELD_LENGTH,
        verbose_name=_('Название')
    )
    year = models.SmallIntegerField(
        validators=[
            MaxValueValidator(timezone.now().year)
        ],
        verbose_name=_('Год выпуска')
    )
    description = models.TextField(blank=True, verbose_name=_('Описание'))
    genre = models.ManyToManyField('Genre', verbose_name=_('Жанр'))
    category = models.ForeignKey(
        'Category',
        on_delete=models.SET_NULL,
        null=True,
        verbose_name=_('Категория')
    )

    class Meta:
        ordering = ['name']
        verbose_name = _('Произведение')
        verbose_name_plural = _('Произведения')
        default_related_name = 'titles'

    def __str__(self):
        return Truncator(self.name).chars(STR_LENGTH)


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


class Review(models.Model):
    """Модель отзыва на произведение."""

    title = models.ForeignKey(
        Title,
        on_delete=models.CASCADE,
    )
    text = models.TextField()
    author = models.ForeignKey(
        'User',
        on_delete=models.CASCADE,
    )
    score = models.IntegerField(
        validators=[
            MinValueValidator(MIN_SCORE_RATING),
            MaxValueValidator(MAX_SCORE_RATING)
        ]
    )
    pub_date = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.update_title_rating()

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        self.update_title_rating()

    def update_title_rating(self):
        avg_rating = self.title.reviews.aggregate(
            models.Avg('score'))['score__avg']
        self.title.rating = round(avg_rating) if avg_rating else None
        self.title.save()

    class Meta:
        default_related_name = 'reviews'
        constraints = [
            models.UniqueConstraint(
                fields=['title', 'author'],
                name='unique_review'
            )
        ]
        ordering = ['-pub_date']
        verbose_name = _('Отзыв')
        verbose_name_plural = _('Отзывы')

    def __str__(self):
        return f'Отзыв от {self.author} на {self.title}'


class Comment(models.Model):
    """Модель комментария к отзыву."""

    review = models.ForeignKey(
        Review,
        on_delete=models.CASCADE,
    )
    text = models.TextField()
    author = models.ForeignKey(
        'User',
        on_delete=models.CASCADE,
    )
    pub_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        default_related_name = 'comments'
        ordering = ['-pub_date']
        verbose_name = _('Комментарий')
        verbose_name_plural = _('Комментарии')

    def __str__(self):
        return f'Комментарий от {self.author}'
