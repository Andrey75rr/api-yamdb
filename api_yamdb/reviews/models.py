from django.db import models
from django.utils.text import Truncator

from reviews.constants import NAME_FIELD_LENGTH, SLUG_FIELD_LENGTH, STR_LENGTH


class Category(models.Model):
    name = models.CharField(
        max_length=NAME_FIELD_LENGTH,
        verbose_name='Наименование'
    )
    slug = models.SlugField(
        max_length=SLUG_FIELD_LENGTH,
        unique=True,
        verbose_name='Адрес категории'
    )

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'

    def __str__(self):
        return Truncator(self.name).chars(STR_LENGTH)


class Genre(models.Model):
    name = models.CharField(
        max_length=NAME_FIELD_LENGTH,
        verbose_name='Название жанра'
    )
    slug = models.SlugField(
        max_length=SLUG_FIELD_LENGTH,
        unique=True,
        verbose_name='Адрес жанра'
    )

    class Meta:
        verbose_name = 'Жанр'
        verbose_name_plural = 'Жанры'

    def __str__(self):
        return Truncator(self.name).chars(STR_LENGTH)


class Title(models.Model):
    name = models.CharField(
        max_length=NAME_FIELD_LENGTH,
        verbose_name='Название'
    )
    year = models.IntegerField(verbose_name='Год выпуска')
    rating = models.IntegerField(
        null=True,
        blank=True,
        default=None,
        verbose_name='Рейтинг на основе отзывов'
    )
    description = models.TextField(blank=True, verbose_name='Описание')
    genre = models.ManyToManyField('Genre', verbose_name='Жанр')
    category = models.ForeignKey(
        'Category',
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Категория'
    )

    class Meta:
        verbose_name = 'Произведение'
        verbose_name_plural = 'Произведения'
        default_related_name = 'titles'

    def __str__(self):
        return Truncator(self.name).chars(STR_LENGTH)
