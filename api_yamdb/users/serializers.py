from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
import random
import string

User = get_user_model()  # Получаем нашу модель пользователя


class SignUpSerializer(serializers.Serializer):
    """Сериализатор для регистрации пользователя."""

    email = serializers.EmailField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all())]
    )

    username = serializers.CharField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all())]
    )

    def validate(self, data):
        # Задание: добавь проверку, что username не равен 'me'
        # Подсказка: 'me' - зарезервированное имя
        if data['username'].lower() == 'me':
            raise serializers.ValidationError(
                'Имя пользователя "me" не разрешено.'
            )
        return data

    def create(self, validated_data):
        # Задание: сгенерировать случайный код из 6 символов
        confirmation_code = ''.join(
            random.choice(string.ascii_uppercase + string.digits)
            for _ in range(6)
        )

        # Создаём или получаем пользователя
        user, created = User.objects.get_or_create(
            username=validated_data['username'],
            email=validated_data['email'],
            defaults={'confirmation_code': confirmation_code}
        )

        # Если пользователь уже существует, обновляем код
        if not created:
            user.confirmation_code = confirmation_code
            user.save()

        # Отправляем email с кодом
        send_mail(
            subject='YaMDb: Код подтверждения',
            message=f'Ваш код подтверждения: {confirmation_code}',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[validated_data['email']],
        )

        return user
