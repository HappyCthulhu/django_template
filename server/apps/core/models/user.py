from typing import ClassVar

from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone

from server.apps.core.models.base import BaseModel


from server.apps.core.history import track_history

class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email: str, password: str, **extra_fields) -> "User":
        if not email:
            raise ValueError("Email обязателен")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email: str, password: str | None = None, **extra_fields) -> "User":
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        extra_fields.setdefault("is_active", True)

        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email: str, password: str | None = None, **extra_fields) -> "User":
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if not extra_fields.get("is_staff"):
            raise ValueError("Superuser должен иметь is_staff=True.")
        if not extra_fields.get("is_superuser"):
            raise ValueError("Superuser должен иметь is_superuser=True.")

        return self._create_user(email, password, **extra_fields)


@track_history
class User(AbstractBaseUser, PermissionsMixin, BaseModel):
    email = models.EmailField(unique=True, verbose_name="Email")

    first_name = models.CharField(max_length=255, verbose_name="Имя")
    last_name = models.CharField(max_length=255, verbose_name="Фамилия")

    is_active = models.BooleanField(default=True, verbose_name="Активен")
    is_staff = models.BooleanField(default=False, verbose_name="Стафф")

    date_joined = models.DateTimeField(default=timezone.now, verbose_name="Дата регистрации")

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: ClassVar[list[str]] = []  # пустой список — username не требуется

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def __str__(self):
        return self.email
