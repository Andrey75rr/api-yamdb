import re

from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from core.constants import NAME_FIELD_LENGTH, SLUG_FIELD_LENGTH


class SlugNameSerializer(serializers.ModelSerializer):
    """Базовый сериализатор для моделей с полями name и slug."""

    name = serializers.CharField(max_length=NAME_FIELD_LENGTH)
    slug = serializers.CharField(
        max_length=SLUG_FIELD_LENGTH,
        validators=[
            RegexValidator(
                regex=r'^[-a-zA-Z0-9_]+$',
                message=_('Slug содержит недопустимые символы')
            ),
        ]
    )

    class Meta:
        fields = ('name', 'slug')


class UsernameValidationMixin:
    """Миксин для валидации username."""

    def validate_username(self, value):
        if value.lower() == 'me':
            raise serializers.ValidationError(
                'Имя пользователя "me" не разрешено.'
            )
        pattern = r'^[\w.@+-]+\Z'
        if not re.match(pattern, value):
            raise serializers.ValidationError(
                'Имя пользователя содержит недопустимые символы. '
                'Разрешены только буквы, цифры и символы @/./+/-/_.'
            )
        return value
