import random
import string

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404
from rest_framework import serializers

from core.constants import (
    EMAIL_LENGTH,
    MAX_SCORE_RATING,
    MIN_SCORE_RATING,
    USER_NAME_FIELD_LENGTH,
)
from core.serializers import SlugNameSerializer, UsernameValidationMixin
from reviews.models import Category, Comment, Genre, Review, Title

User = get_user_model()


class SignUpSerializer(UsernameValidationMixin, serializers.Serializer):
    """Сериализатор для регистрации пользователя."""

    email = serializers.EmailField(
        required=True,
        max_length=EMAIL_LENGTH,
    )
    username = serializers.CharField(
        required=True,
        max_length=USER_NAME_FIELD_LENGTH,
    )

    def validate(self, data):
        email = data['email']
        username = data['username']

        if User.objects.filter(email=email, username=username).exists():
            return data
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError(
                'Пользователь с таким email уже существует.'
            )
        if User.objects.filter(username=username).exists():
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
        user = get_object_or_404(User, username=username)
        if user.confirmation_code != confirmation_code:
            raise serializers.ValidationError(
                {'confirmation_code': 'Неверный код подтверждения.'}
            )
        return data


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

    class Meta(SlugNameSerializer.Meta):
        model = Category


class GenreSerializer(SlugNameSerializer):
    """Сериализатор для жанров."""

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

    genre = serializers.SlugRelatedField(
        slug_field='slug',
        queryset=Genre.objects.all(),
        many=True,
        required=True,
        allow_empty=False
    )
    category = serializers.SlugRelatedField(
        slug_field='slug',
        queryset=Category.objects.all(),
        required=True
    )

    class Meta:
        model = Title
        fields = '__all__'

    def to_representation(self, instance):
        """Вернет данные, включая наименование и slug категории и жанра."""
        return TitleReadSerializer(instance, context=self.context).data


class TitleReadSerializer(serializers.ModelSerializer):
    """Сериализатор для чтения произведений.

    Вернет данные, включая наименование и slug категории и жанра.
    """

    rating = serializers.IntegerField(read_only=True, default=None)
    genre = GenreSerializer(many=True, read_only=True)
    category = CategorySerializer(read_only=True)

    class Meta:
        model = Title
        fields = (
            'id', 'name', 'year', 'rating', 'description', 'genre', 'category')
