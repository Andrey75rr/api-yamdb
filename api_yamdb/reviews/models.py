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
