from django.db import models
from django.utils.text import Truncator
from django.utils.translation import gettext_lazy as _

from core.constants import NAME_FIELD_LENGTH, STR_LENGTH


class BaseFeedback(models.Model):
    """Абстрактная базовая модель для отзывов и комментариев."""

    text = models.TextField(verbose_name=_('Текст'))
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


class SlugFieldListModel(models.Model):
    """Абстрактная базовая модель для списков с полем slug."""

    name = models.CharField(
        max_length=NAME_FIELD_LENGTH,
        verbose_name=_('Наименование')
    )
    slug = models.SlugField(
        unique=True,
        verbose_name=_('Адрес')
    )

    class Meta:
        abstract = True
        ordering = ['name']

    def __str__(self):
        return Truncator(self.name).chars(STR_LENGTH)
