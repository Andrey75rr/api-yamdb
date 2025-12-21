from django.db import models
from django.utils.text import Truncator
from django.utils.translation import gettext_lazy as _

from core.constants import NAME_FIELD_LENGTH, STR_LENGTH


class SlugFieldListModel(models.Model):
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
