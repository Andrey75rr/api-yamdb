import csv
import os

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import IntegrityError, DataError

from reviews.models import Category, Comment, Genre, Review, Title, User

MODELS_FILES = {
    Category: {
        'file': 'category.csv',
        'fields': ['id', 'name', 'slug']
    },
    Genre: {
        'file': 'genre.csv',
        'fields': ['id', 'name', 'slug']
    },
    User: {
        'file': 'users.csv',
        'fields': ['id', 'username', 'email', 'role']
    },
    Title: {
        'file': 'titles.csv',
        'fields': ['id', 'name', 'year', 'category'],
        'related': {'category': Category}
    },
    Review: {
        'file': 'review.csv',
        'fields': ['id', 'title', 'text', 'author', 'score', 'pub_date'],
        'related': {'title': Title, 'author': User}
    },
    Comment: {
        'file': 'comments.csv',
        'fields': ['id', 'review', 'text', 'author', 'pub_date'],
        'related': {'review': Review, 'author': User}
    },
}


class Command(BaseCommand):
    help = 'Импорт данных из CSV в БД'

    def _import_model(self, model, config, base_path):
        """Импорт одной модели из CSV."""
        file_path = os.path.join(base_path, config['file'])
        try:
            with open(file_path, encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row_num, row in enumerate(reader, start=2):
                    self._process_row(model, config, row, row_num)
            self.stdout.write(
                self.style.SUCCESS(f'{model.__name__} загружены.'))
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f'Файл {file_path} не найден'))
            raise

    def _process_row(self, model, config, row, row_num):
        """Обработка одной строки CSV."""
        try:
            data = {}
            for field in config['fields']:
                if field in config.get('related', {}):
                    rel_model = config['related'][field]
                    data[field] = rel_model.objects.get(id=row[field])
                else:
                    data[field] = row[field]
            model.objects.get_or_create(**data)
        except KeyError as e:
            self.stdout.write(
                self.style.ERROR(
                    f'{model.__name__}: нет поля {e} в строке {row_num}')
            )
        except IntegrityError as e:
            self.stdout.write(
                self.style.ERROR(
                    f'{model.__name__}: ошибка целостности '
                    f'в строке {row_num} - {e}')
            )
        except DataError as e:
            self.stdout.write(
                self.style.ERROR(
                    f'{model.__name__}: ошибка данных '
                    f'в строке {row_num} - {e}')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(
                    f'{model.__name__}: неизвестная ошибка '
                    f'в строке {row_num} - {e}')
            )

    def _import_m2m(self, base_path):
        """Импорт связей ManyToMany."""
        m2m_path = os.path.join(base_path, 'genre_title.csv')
        try:
            with open(m2m_path, encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    try:
                        title = Title.objects.get(id=row['title_id'])
                        genre = Genre.objects.get(id=row['genre_id'])
                        title.genre.add(genre)
                    except (Title.DoesNotExist, Genre.DoesNotExist) as e:
                        self.stdout.write(
                            self.style.ERROR(f'Ошибка связи: {e}'))
            self.stdout.write(
                self.style.SUCCESS('Связи жанров загружены.'))
        except FileNotFoundError:
            self.stdout.write(
                self.style.ERROR(f'Файл {m2m_path} не найден'))

    def handle(self, *args, **kwargs):
        base_path = os.path.join(settings.BASE_DIR, 'static/data')
        
        for model, config in MODELS_FILES.items():
            self._import_model(model, config, base_path)
        
        self._import_m2m(base_path)