from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils.text import Truncator
from django.utils.translation import gettext_lazy as _

from reviews.constants import NAME_FIELD_LENGTH, SLUG_FIELD_LENGTH, STR_LENGTH


class Category(models.Model):
    name = models.CharField(
        max_length=NAME_FIELD_LENGTH,
        verbose_name=_('Наименование')
    )
    slug = models.SlugField(
        max_length=SLUG_FIELD_LENGTH,
        unique=True,
        verbose_name=_('Адрес категории')
    )

    class Meta:
        ordering = ['name']
        verbose_name = _('Категория')
        verbose_name_plural = _('Категории')

    def __str__(self):
        return Truncator(self.name).chars(STR_LENGTH)


class Genre(models.Model):
    name = models.CharField(
        max_length=NAME_FIELD_LENGTH,
        verbose_name=_('Название жанра')
    )
    slug = models.SlugField(
        max_length=SLUG_FIELD_LENGTH,
        unique=True,
        verbose_name=_('Адрес жанра')
    )

    class Meta:
        ordering = ['name']
        verbose_name = _('Жанр')
        verbose_name_plural = _('Жанры')

    def __str__(self):
        return Truncator(self.name).chars(STR_LENGTH)


class Title(models.Model):
    name = models.CharField(
        max_length=NAME_FIELD_LENGTH,
        verbose_name=_('Название')
    )
    year = models.IntegerField(verbose_name=_('Год выпуска'))
    rating = models.IntegerField(
        null=True,
        blank=True,
        default=None,
        verbose_name=_('Рейтинг на основе отзывов')
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
       # related_name='reviews'
    )
    score = models.IntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(10)
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
