import string

import random
from datetime import datetime

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.utils.translation import gettext_lazy as _

from rest_framework import serializers
from rest_framework.exceptions import NotFound
from rest_framework.validators import UniqueValidator

from core.constants import (
    MIN_SCORE_RATING,
    MAX_SCORE_RATING,
    NAME_FIELD_LENGTH
)
from core.serializers import SlugNameSerializer, UsernameValidationMixin
from reviews.models import Category, Comment, Genre, Title, Review, Title


User = get_user_model()


class SignUpSerializer(UsernameValidationMixin, serializers.Serializer):
    """Сериализатор для регистрации пользователя."""

    email = serializers.EmailField(
        required=True,
        max_length=254,
    )
    username = serializers.CharField(
        required=True,
        max_length=150,
    )

    def validate(self, data):
        email = data.get('email')
        username = data.get('username')

        if not email or not username:
            return data

        email_exists = User.objects.filter(email=email).exists()
        username_exists = User.objects.filter(username=username).exists()

        if email_exists and username_exists:
            user = User.objects.filter(
                email=email,
                username=username
            ).first()
            if not user:
                raise serializers.ValidationError(
                    'Email и username принадлежат разным пользователям.'
                )
        elif email_exists:
            user_with_email = User.objects.filter(email=email).first()
            if user_with_email.username != username:
                raise serializers.ValidationError(
                    'Пользователь с таким email уже существует.'
                )
        elif username_exists:
            user_with_username = User.objects.filter(username=username).first()
            if user_with_username.email != email:
                raise serializers.ValidationError(
                    'Пользователь с таким username уже существует.'
                )
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
        username = data['username']
        confirmation_code = data['confirmation_code']
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise NotFound('Пользователь не найден.')
        if user.confirmation_code != confirmation_code:
            raise serializers.ValidationError(
                {'confirmation_code': 'Неверный код подтверждения.'}
            )
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['slug'].validators.append(
            UniqueValidator(
                queryset=Category.objects.all(),
                message=_('Категория с таким slug уже существует.')
            )
        )

    class Meta(SlugNameSerializer.Meta):
        model = Category


class GenreSerializer(SlugNameSerializer):
    """Сериализатор для жанров."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['slug'].validators.append(
            UniqueValidator(
                queryset=Genre.objects.all(),
                message=_('Жанр с таким slug уже существует.')
            )
        )

    class Meta(SlugNameSerializer.Meta):
        model = Genre


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
        min_value=MIN_SCORE_RATING,
        max_value=MAX_SCORE_RATING,
        required=True,
        error_messages={
            'min_value': f'Оценка не может быть меньше {MIN_SCORE_RATING}',
            'max_value': f'Оценка не может быть больше {MAX_SCORE_RATING}'
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
    """Сериализатор для записи произведений."""

    name = serializers.CharField(max_length=NAME_FIELD_LENGTH)
    rating = serializers.IntegerField(read_only=True)
    year = serializers.IntegerField(max_value=datetime.now().year)
    genre = serializers.SlugRelatedField(
        slug_field='slug',
        queryset=Genre.objects.all(),
        many=True,
        required=True
    )
    category = serializers.SlugRelatedField(
        slug_field='slug',
        queryset=Category.objects.all(),
        required=True
    )

    class Meta:
        model = Title
        fields = '__all__'


class TitleReadSerializer(serializers.ModelSerializer):
    """Сериализатор для чтения произведений."""

    rating = serializers.IntegerField(read_only=True, allow_null=True)
    genre = GenreSerializer(many=True, read_only=True)
    category = CategorySerializer(read_only=True)

    class Meta:
        model = Title
        fields = (
            'id', 'name', 'year', 'rating', 'description', 'genre', 'category')
