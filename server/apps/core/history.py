from typing import Any, Callable

import pghistory
from django.db.models import Model


def track_history(cls: type[Model]) -> Callable[..., Any]:
    """Декоратор для классов, который добавляет трекинг истории изменений через pghistory."""
    tracked_events = [pghistory.InsertEvent(), pghistory.UpdateEvent(), pghistory.DeleteEvent()]
    return pghistory.track(*tracked_events)(cls)
