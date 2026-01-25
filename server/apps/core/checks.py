from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, Generator

from django.apps import apps
from django.conf import settings
from django.core.checks import Error, Tags, register
from django.urls import URLPattern, URLResolver, get_resolver
from server.configs.settings import PROJECT_APPS


if TYPE_CHECKING:
    from rest_framework.viewsets import ViewSet

# Добавлять модели, которые не должны иметь историю изменений
MODELS_WITHOUT_HISTORY = ()


@register(Tags.models)
def check_history_models(**_kwargs) -> list[Error]:
    errors: list[Error] = []

    for app_config in apps.get_app_configs():
        # Берем только наши модели, djangoвские модели не трогаем
        if app_config.label not in tuple(project_path.split(".")[0] for project_path in PROJECT_APPS):
            continue
        # Пропускаем Event и Historical модели
        for model in app_config.get_models():
            if model.__name__.endswith("Event") or "Historical" in model.__name__ or model in MODELS_WITHOUT_HISTORY:
                continue

            # Пропускаем прокси модели
            if model._meta.proxy:
                continue

            try:
                apps.get_model(f"{model._meta.app_label}.{model._meta.model_name}Event")
            except LookupError:
                errors.append(
                    Error(
                        "Историческая модель не найдена",
                        hint="Необходимо создать pg_history модель для данной модели.",
                        obj=model,
                        id="core.E001",
                    ),
                )

    return errors


@register(Tags.urls)
def check_access_policy(app_configs, **_kwargs) -> list[Error]:  # noqa: ANN001
    del app_configs  # For ruff warnings.
    errors: list[Error] = []

    if not getattr(settings, "CHECK_ACCESS_POLICY", False):
        return []

    resolver = get_resolver()
    checked_views: set[Callable] = set()
    for url_pattern in _get_patterns_from_resolver(resolver):
        callback = getattr(url_pattern, "callback", None)
        if callback and hasattr(callback, "cls") and callback not in checked_views:
            checked_views.add(callback)
            errors.extend(_validate_viewset_policy(callback.cls))
    return errors


def _get_patterns_from_resolver(resolver: URLResolver) -> Generator[URLPattern, Any, None]:
    for pattern in resolver.url_patterns:
        if isinstance(pattern, URLPattern):
            yield pattern
        elif isinstance(pattern, URLResolver):
            yield from _get_patterns_from_resolver(pattern)


def _validate_viewset_policy(viewset_class: type[ViewSet]) -> list[Error]:
    error: list[Error] = []
    access_policy = getattr(viewset_class, "access_policy", None)

    if access_policy is None:
        return error

    viewset_methods = {
        method
        for method in (
            *(method.__name__ for method in getattr(viewset_class, "get_extra_actions", list)()),
        )
        if hasattr(viewset_class, method)
    }

    policy_methods = set()
    for statement in getattr(access_policy, "statements", []):
        policy_methods.update(statement.get("action", []))

    missing_methods = viewset_methods - policy_methods
    if missing_methods:
        error.append(
            Error(
                f"AccessPolicy для {viewset_class.__name__} не покрывает все методы ViewSet: {missing_methods}",
                obj=viewset_class,
                id="access_policy.E001",
            ),
        )

    extra_policy_methods = policy_methods - viewset_methods
    if extra_policy_methods:
        error.append(
            Error(
                (
                    f"AccessPolicy для {viewset_class.__name__} содержит методы не предоставленные"
                    f"в ViewSet: {extra_policy_methods}"
                ),
                obj=viewset_class,
                id="access_policy.E002",
            ),
        )

    return error