from django.core.exceptions import ValidationError
from django.utils import timezone


def validate_year(value: int) -> None:
    if value > timezone.now().year:
        raise ValidationError('Год не может превышать текущий год.')
