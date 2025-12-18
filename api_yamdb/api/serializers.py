import string
import re
import random
from datetime import datetime

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _

from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from reviews.constants import NAME_FIELD_LENGTH, SLUG_FIELD_LENGTH
from reviews.models import Category, Genre, Title, Review, Title


User = get_user_model()


class SlugNameSerializer(serializers.ModelSerializer):
    """Базовый сериализатор для моделей с полем slug."""

    name = serializers.CharField(max_length=NAME_FIELD_LENGTH)
    slug = serializers.CharField(
        max_length=SLUG_FIELD_LENGTH,
        validators=[
            RegexValidator(
                regex=r'^[-a-zA-Z0-9_]+$',
                message=_('Slug содержит недопустимые символы')
            )
        ]
    )


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


class SignUpSerializer(UsernameValidationMixin, serializers.Serializer):
    """Сериализатор для регистрации пользователя."""

    email = serializers.EmailField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all())]
    )
    username = serializers.CharField(
        required=True,
        max_length=150,
        validators=[
            UniqueValidator(queryset=User.objects.all()),
        ]
    )

    def validate(self, data):
        return data

    def create(self, validated_data):

        confirmation_code = ''.join(
            random.choice(string.ascii_uppercase + string.digits)
            for _ in range(6)
        )
        user, created = User.objects.get_or_create(
            username=validated_data['username'],
            email=validated_data['email'],
            defaults={'confirmation_code': confirmation_code}
        )
        if not created:
            user.confirmation_code = confirmation_code
            user.save()
        send_mail(
            subject='YaMDb: Код подтверждения',
            message=f'Ваш код подтверждения: {confirmation_code}',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[validated_data['email']],
        )
        return user


class TokenSerializer(UsernameValidationMixin, serializers.Serializer):
    """Сериализатор для получения JWT-токена."""

    username = serializers.CharField(required=True)
    confirmation_code = serializers.CharField(required=True, write_only=True)

    def validate(self, data):
        try:
            user = User.objects.get(username=data['username'])
        except User.DoesNotExist:
            raise serializers.ValidationError('Пользователь не найден.')
        if user.confirmation_code != data['confirmation_code']:
            raise serializers.ValidationError('Неверный код подтверждения.')
        return data


class UserSerializer(UsernameValidationMixin, serializers.ModelSerializer):
    """Сериализатор для работы с пользователями."""

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name',
                  'last_name', 'bio', 'role')
        read_only_fields = ('role',)


class AdminUserSerializer(
    UsernameValidationMixin,
    serializers.ModelSerializer
):
    """Сериализатор для администраторов (полные права)."""

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name',
                  'last_name', 'bio', 'role')


class CategorySerializer(SlugNameSerializer):
    """Сериализатор для категорий."""

    class Meta:
        model = Category
        fields = '__all__'


class GenreSerializer(SlugNameSerializer):
    """Сериализатор для жанров."""

    class Meta:
        model = Genre
        fields = '__all__'


class CommentSerializer(serializers.ModelSerializer):
    """Сериализатор для комментариев."""

    author = serializers.SlugRelatedField(
        slug_field='username',
        read_only=True
    )

    class Meta:
        model = Comment
        fields = ('id', 'text', 'author', 'pub_date')


class ReviewSerializer(serializers.ModelSerializer):
    """Сериализатор для отзывов."""

    author = serializers.SlugRelatedField(
        slug_field='username',
        read_only=True
    )

    score = serializers.IntegerField(
        min_value=1,
        max_value=10,
        required=True,
        error_messages={
            'min_value': 'Оценка не может быть меньше 1',
            'max_value': 'Оценка не может быть больше 10'
        }
    )

    class Meta:
        model = Review
        fields = ('id', 'text', 'author', 'score', 'pub_date')
        read_only_fields = ('author',)

    def validate(self, data):
        request = self.context.get('request')
        if request and request.method == 'POST':
            title_id = self.context['view'].kwargs.get('title_id')
            if Review.objects.filter(
                title_id=title_id,
                author=request.user
            ).exists():
                raise serializers.ValidationError(
                    'Вы уже оставляли отзыв на это произведение.'
                )
        return data


class TitleSerializer(serializers.ModelSerializer):
    """Сериализатор для произведений."""
    name = serializers.CharField(max_length=NAME_FIELD_LENGTH)
    rating = serializers.IntegerField(read_only=True)
    year = serializers.IntegerField(max_value=datetime.now().year)

    class Meta:
        model = Title
        fields = '__all__'
