from __future__ import annotations

import inspect
from pathlib import Path
from typing import TYPE_CHECKING

from django.apps import apps
from django.core.management.base import BaseCommand
from server.configs.settings import PROJECT_APPS

from server.apps.core.checks import MODELS_WITHOUT_HISTORY

if TYPE_CHECKING:
    from django.db.models import Model

DECORATOR = "@track_history\n"
IMPORT_STATEMENT = "from server.apps.core.history import track_history\n"


class Command(BaseCommand):
    help = "Add decorators and import statements to models"

    def handle(self, *_args: tuple, **_options: dict) -> None:
        self.process_all_models()

    def add_decorator_and_import_to_model(self, model: type[Model]) -> None:
        model_file_path = Path(inspect.getfile(model))
        with model_file_path.open() as file:
            content = file.read()

        model_name = model.__name__
        class_declaration = f"class {model_name}("

        # Разделяем содержимое файла на строки
        lines = content.split("\n")

        # Найти место, где заканчиваются импорты
        import_index = next(
            i
            for i, line in enumerate(lines)
            if line.strip() and not line.startswith("import") and not line.startswith("from")
        )

        # Вставить импортное заявление, если его еще нет
        if IMPORT_STATEMENT.strip() not in content:
            lines.insert(import_index, IMPORT_STATEMENT)
            self.stdout.write(f"Added import statement to {model_name}.FP: {model_file_path}")

        # Добавление декоратора перед объявлением класса
        for i, line in enumerate(lines):
            if line.startswith(class_declaration):
                # Проверка, не был ли декоратор уже добавлен
                if i > 0 and lines[i - 1].strip() == DECORATOR.strip():
                    continue
                lines.insert(i, DECORATOR)
                self.stdout.write(f"Added decorator to {model_name}.FP: {model_file_path}")

        # Объединяем строки обратно в содержание файла
        updated_content = "\n".join(lines)

        # Запись обновленного содержания обратно в файл
        with model_file_path.open("w") as file:
            file.write(updated_content)

    def process_all_models(self) -> None:
        project_app_labels = tuple(project_path.rsplit(".", 1)[0].split(".")[-2] for project_path in PROJECT_APPS)
        for app_config in apps.get_app_configs():
            if app_config.label not in project_app_labels:
                continue
            self.stdout.write(f"Processing app: {app_config.label}")
            models = app_config.get_models()
            for model in models:
                self.stdout.write(f"Found model: {model.__name__}")
                if (
                    model.__name__.endswith("Event")
                    or "Historical" in model.__name__
                    or model in MODELS_WITHOUT_HISTORY
                ):
                    continue
                # Пропускаем прокси и абстрактные модели
                if model._meta.proxy or model._meta.abstract:
                    continue
                try:
                    apps.get_model(f"{model._meta.app_label}.{model._meta.model_name}Event")
                except LookupError:
                    self.add_decorator_and_import_to_model(model)
