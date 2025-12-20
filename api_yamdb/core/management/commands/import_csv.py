import csv
import os

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.utils import IntegrityError

from reviews.models import Category, Genre, Title, Review, Comment, User


class Command(BaseCommand):
    help = 'Импорт данных из CSV файлов'
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
        self.stdout.write("Проверка базы данных...")
        data_dir = os.path.join(settings.BASE_DIR, 'static/data')
        for csv_file, model in self.MODELS_ORDER:
            file_path = os.path.join(data_dir, csv_file)
            if not os.path.exists(file_path):
                self.stdout.write(
                    self.style.WARNING(f'Файл {csv_file} не найден'))
                continue

            self.import_csv(file_path, model)
        self.import_genre_title_relations(data_dir)

    def import_csv(self, file_path, model):
        """Обработает построчно данные из csv файла."""
        model_name = model.__name__
        self.stdout.write(
            f"Импорт {model_name} из {os.path.basename(file_path)}...")

        try:
            with open(file_path, mode='r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                row_count = 0

                for row in reader:
                    try:
                        self.create_or_update_object(model, row)
                        row_count += 1
                    except (IntegrityError, ObjectDoesNotExist) as e:
                        self.stdout.write(
                            self.style.ERROR(
                                f'Ошибка при обработке строки: {e}'
                            )
                        )
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(
                            f'Неожиданная ошибка: {e}'))

                if row_count > 0:
                    self.stdout.write(self.style.SUCCESS(
                        f'Успешно импортировано {row_count} записей: '
                        f'{model_name}'))
                else:
                    self.stdout.write(self.style.WARNING(
                        f'Нет данных для импорта: {model_name}'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(
                f'Ошибка чтения файла {file_path}: {e}'))

    def create_or_update_object(self, model, data):
        """Создаст или обновит объекты в БД."""
        processed_data = {}

        for key, value in data.items():
            if value == '' or value is None:
                continue
            if key in ['category', 'title', 'author', 'review']:
                try:
                    if key in ['author'] and model in [Review, Comment, User]:
                        processed_data[key + '_id'] = int(value)
                    elif key == 'category' and model == Title:
                        processed_data[key + '_id'] = int(value)
                    elif key == 'title' and model == Review:
                        processed_data[key + '_id'] = int(value)
                    elif key == 'review' and model == Comment:
                        processed_data[key + '_id'] = int(value)
                    else:
                        processed_data[key] = value
                except (ValueError, TypeError):
                    processed_data[key] = value
            elif key.endswith('_id'):
                processed_data[key] = int(value)
            elif key in ['id', 'year', 'score']:
                processed_data[key] = int(value) if value else None
            else:
                processed_data[key] = value
        obj_id = processed_data.pop('id', None)

        try:
            if obj_id is not None:
                obj, created = model.objects.update_or_create(
                    id=obj_id,
                    defaults=processed_data
                )
            else:
                obj = model.objects.create(**processed_data)

            return obj
        except Exception as e:
            raise Exception(f'Ошибка создания объекта: {e}')

    def import_genre_title_relations(self, data_dir):
        """Загрузит связи ManyToMany между произведениями и жанрами."""
        file_path = os.path.join(data_dir, 'genre_title.csv')

        if not os.path.exists(file_path):
            self.stdout.write(self.style.WARNING(
                'Файл genre_title.csv не найден'))
            return

        self.stdout.write("Импорт связей жанров с произведениями...")

        try:
            with open(file_path, mode='r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                relation_count = 0

                for row in reader:
                    try:
                        title_id = int(row['title_id'])
                        genre_id = int(row['genre_id'])

                        title = Title.objects.get(id=title_id)
                        genre = Genre.objects.get(id=genre_id)
                        title.genre.add(genre)
                        relation_count += 1

                    except (Title.DoesNotExist, Genre.DoesNotExist) as e:
                        self.stdout.write(self.style.ERROR(
                            f'Объект не найден: {e}'))
                    except (ValueError, KeyError) as e:
                        self.stdout.write(
                            self.style.ERROR(f'Ошибка данных: {e}'))
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(
                            f'Неожиданная ошибка: {e}'))

                if relation_count > 0:
                    self.stdout.write(self.style.SUCCESS(
                        f'Установлено {relation_count} связей жанров'))
                else:
                    self.stdout.write(self.style.WARNING(
                        'Нет связей для импорта'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(
                f'Ошибка чтения genre_title.csv: {e}'))
