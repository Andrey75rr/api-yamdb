import re

from rest_framework import serializers

from core.constants import NAME_FIELD_LENGTH, USERNAME_VALIDATION_PATTERN


class SlugNameSerializer(serializers.ModelSerializer):
    """Базовый сериализатор для моделей с полями name и slug."""

    name = serializers.CharField(max_length=NAME_FIELD_LENGTH)

    class Meta:
        fields = ('name', 'slug')


class UsernameValidationMixin:
    """Миксин для валидации username."""

    FORBIDDEN_USERNAME = 'me'

    def validate_username(self, value):
        if value == self.FORBIDDEN_USERNAME:
            raise serializers.ValidationError(
                f"Имя пользователя '{self.FORBIDDEN_USERNAME}' не разрешено."
            )
        pattern = USERNAME_VALIDATION_PATTERN
        if not re.match(pattern, value):
            raise serializers.ValidationError(
                'Имя пользователя содержит недопустимые символы. '
                'Разрешены только буквы, цифры и символы @/./+/-/_.'
            )
        return value
