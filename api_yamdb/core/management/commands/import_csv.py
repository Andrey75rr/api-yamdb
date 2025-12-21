import csv
import os
from typing import Any, Dict

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist

from core.constants import CSV_PATH
from reviews.models import Category, Genre, Title, Review, Comment, User


class Command(BaseCommand):
    """Управляющая команда для загрузки данных в БД из csv."""

    help = 'Импорт данных из CSV файлов'
    MODEL_CONFIGS = {
        Category: {
            'fields': ['id', 'name', 'slug'],
            'foreign_keys': {}
        },
        Genre: {
            'fields': ['id', 'name', 'slug'],
            'foreign_keys': {}
        },
        User: {
            'fields': ['id', 'username', 'email', 'role'],
            'foreign_keys': {}
        },
        Title: {
            'fields': ['id', 'name', 'year', 'category'],
            'foreign_keys': {'category': Category}
        },
        Review: {
            'fields': ['id', 'title', 'text', 'author', 'score', 'pub_date'],
            'foreign_keys': {'title': Title, 'author': User}
        },
        Comment: {
            'fields': ['id', 'review', 'text', 'author', 'pub_date'],
            'foreign_keys': {'review': Review, 'author': User}
        },
    }

    MODELS_ORDER = [
        ('category.csv', Category),
        ('genre.csv', Genre),
        ('users.csv', User),
        ('titles.csv', Title),
        ('review.csv', Review),
        ('comments.csv', Comment),
    ]

    @transaction.atomic
    def handle(self, *args, **options):
        """Загрузит данные из csv файла."""
        data_dir = os.path.join(settings.BASE_DIR, CSV_PATH)

        for csv_file, model in self.MODELS_ORDER:
            file_path = os.path.join(data_dir, csv_file)
            if not os.path.exists(file_path):
                self.stdout.write(
                    self.style.WARNING(f'Файл {csv_file} не найден')
                )
                continue

            self.import_csv(file_path, model)

        self.import_genre_title_relations(data_dir)
        self.stdout.write(self.style.SUCCESS("Импорт завершен!"))

    def import_csv(self, file_path, model):
        """Обработает построчно данные из csv файла."""
        model_name = model.__name__
        self.stdout.write(f"Импорт {model_name}...")

        success = 0
        errors = 0

        try:
            with open(file_path, mode='r', encoding='utf-8') as f:
                reader = csv.DictReader(f)

                for row_num, row in enumerate(reader, start=2):
                    try:
                        self.process_row(model, row, row_num)
                        success += 1
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(f'Строка {row_num}: {e}')
                        )
                        errors += 1

                self.report_result(model_name, success, errors)

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Ошибка файла {file_path}: {e}')
            )

    def process_row(self, model, row: Dict[str, str], row_num: int) -> None:
        """Обрабатывает одну строку CSV."""
        data = self.prepare_data(model, row)
        obj_id = data.pop('id', None)

        if obj_id is not None:
            model.objects.update_or_create(id=obj_id, defaults=data)
        else:
            model.objects.create(**data)

    def prepare_data(self, model, row: Dict[str, str]) -> Dict[str, Any]:
        """Подготавливает данные для сохранения."""
        config = self.MODEL_CONFIGS[model]
        result = {}

        for field in config['fields']:
            value = row.get(field)
            if value is None or value == '':
                continue
            if field in config['foreign_keys']:
                related_model = config['foreign_keys'][field]
                try:
                    result[field] = related_model.objects.get(id=int(value))
                except ObjectDoesNotExist:
                    raise Exception(
                        f'{related_model.__name__} с id={value} не найден')
                except ValueError:
                    raise Exception(f'Некорректный ID для {field}: {value}')
            elif field in ['id', 'year', 'score']:
                try:
                    result[field] = int(value)
                except ValueError:
                    raise Exception(f'Некорректное число для {field}: {value}')
            else:
                result[field] = value

        return result

    def report_result(
            self, model_name: str,
            success: int,
            errors: int) -> None:
        """Выводит результат импорта."""
        if success:
            self.stdout.write(
                self.style.SUCCESS(f'  {model_name}: {success} записей')
            )
        if errors:
            self.stdout.write(
                self.style.ERROR(f'  Ошибок: {errors}')
            )

    def import_genre_title_relations(self, data_dir):
        """Загрузит связи ManyToMany между произведениями и жанрами."""
        file_path = os.path.join(data_dir, 'genre_title.csv')

        if not os.path.exists(file_path):
            self.stdout.write(
                self.style.WARNING('Файл genre_title.csv не найден')
            )
            return

        self.stdout.write("Импорт связей жанров...")

        success = 0
        errors = 0

        try:
            with open(file_path, mode='r', encoding='utf-8') as f:
                reader = csv.DictReader(f)

                for row_num, row in enumerate(reader, start=2):
                    try:
                        title_id = int(row['title_id'])
                        genre_id = int(row['genre_id'])

                        title = Title.objects.get(id=title_id)
                        genre = Genre.objects.get(id=genre_id)
                        title.genre.add(genre)
                        success += 1

                    except (Title.DoesNotExist, Genre.DoesNotExist) as e:
                        self.stdout.write(
                            self.style.ERROR(
                                f'Строка {row_num}: объект не найден: {e}')
                        )
                        errors += 1
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(f'Строка {row_num}: {e}')
                        )
                        errors += 1

                self.report_result("Связи жанров", success, errors)

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Ошибка чтения связей: {e}')
            )
