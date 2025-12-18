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
        verbose_name = _('Произведение')
        verbose_name_plural = _('Произведения')
        default_related_name = 'titles'

    def __str__(self):
        return Truncator(self.name).chars(STR_LENGTH)

