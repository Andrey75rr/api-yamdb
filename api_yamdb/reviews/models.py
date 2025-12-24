import re

from django.contrib import admin
from django.contrib.auth.models import AbstractUser
from django.core.validators import (
    MaxValueValidator,
    MinValueValidator,
    RegexValidator
)
from django.db import models
from django.utils import timezone
from django.utils.text import Truncator
from django.utils.translation import gettext_lazy as _

from core.constants import (
    MAX_SCORE_RATING,
    MIN_SCORE_RATING,
    NAME_FIELD_LENGTH,
    NAME_254_FIELD_LENGTH,
    STR_LENGTH,
    ROLE_FIELD_LIMIT,
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
    """Модель произведения."""

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
    genre = models.ManyToManyField(
        'Genre',
        verbose_name=_('Жанр'),
        through='TitleGenre'
    )
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

    @admin.display(description='Жанр')
    def get_title_genres(self):
        """Вернет строку с перечнем жанров произведения."""
        return ', '.join(self.genre.all().values_list('name', flat=True))


class TitleGenre(models.Model):
    """Модель от ноешния произведений к жанрам.

    Модель создана в явном виде и помогает адекватно отображать наименование
    объектов в админ-панели в карточке проивзедения
    """
    title = models.ForeignKey(
        Title,
        on_delete=models.CASCADE,
        verbose_name='Произведение'
    )
    genre = models.ForeignKey(
        Genre,
        on_delete=models.CASCADE,
        verbose_name='Жанр'
    )

    def __str__(self):
        return 'Жанр произведения'

    class Meta:
        db_table = 'reviews_title_genre'
        default_related_name = 'title_genres'
        verbose_name = 'Жанр произведения'
        verbose_name_plural = 'Жанры произведений'


class BaseFeedback(models.Model):
    """Абстрактная базовая модель для отзывов и комментариев."""

    text = models.TextField(_('Текст'))
    author = models.ForeignKey(
        'User',
        on_delete=models.CASCADE,
        verbose_name=_('Автор')
    )
    pub_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Дата публикации')
    )

    class Meta:
        abstract = True
        ordering = ['-pub_date']

    def __str__(self):
        return f'{self._meta.verbose_name} от {self.author}'


class User(AbstractUser):
    """Кастомная модель пользователя для YaMDb."""

    class Role(models.TextChoices):
        USER = 'user', _('Пользователь')
        MODERATOR = 'moderator', _('Модератор')
        ADMIN = 'admin', _('Администратор')

    email = models.EmailField(
        _('email address'),
        unique=True,
        null=False,
        max_length=NAME_254_FIELD_LENGTH
    )

    bio = models.TextField(
        _('биография'),
        blank=True,
    )

    role = models.CharField(
        _('роль'),
        max_length=ROLE_FIELD_LIMIT,
        choices=Role.choices,
        default=Role.USER
    )

    confirmation_code = models.CharField(
        _('код подтверждения'),
        max_length=6,
        blank=True,
        null=True
    )

    username = models.CharField(
        _('username'),
        max_length=150,
        unique=True,
        help_text=_('150 симв., буквы, цифры, @ . / + - _'),
        validators=[
            AbstractUser.username_validator,
            RegexValidator(
                regex=r'^(?!me$).*$',
                message='Использовать имя "me" в качестве username запрещено.',
                flags=re.IGNORECASE
            )
        ],
        error_messages={
            'unique': _("«Пользователь с таким именем уже существует."),
        },
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


class Review(BaseFeedback):
    """Модель отзыва на произведение."""

    title = models.ForeignKey(
        Title,
        on_delete=models.CASCADE,
        verbose_name=_('Произведение')
    )
    score = models.PositiveSmallIntegerField(
        _('Оценка'),
        validators=[
            MinValueValidator(MIN_SCORE_RATING),
            MaxValueValidator(MAX_SCORE_RATING)
        ]
    )

    class Meta:
        default_related_name = 'reviews'
        verbose_name = _('Отзыв')
        verbose_name_plural = _('Отзывы')
        constraints = [
            models.UniqueConstraint(
                fields=['title', 'author'],
                name='unique_review'
            )
        ]


class Comment(BaseFeedback):
    """Модель комментария к отзыву."""

    review = models.ForeignKey(
        Review,
        on_delete=models.CASCADE,
        verbose_name=_('Отзыв')
    )

    class Meta:
        default_related_name = 'comments'
        verbose_name = _('Комментарий')
        verbose_name_plural = _('Комментарии')
