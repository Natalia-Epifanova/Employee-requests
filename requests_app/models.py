from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class Department(models.Model):
    name = models.CharField("Название", max_length=255, unique=True)

    class Meta:
        verbose_name = "Подразделение"
        verbose_name_plural = "Подразделения"
        ordering = ("name",)

    def __str__(self):
        return self.name


class Position(models.Model):
    name = models.CharField("Название", max_length=255, unique=True)

    class Meta:
        verbose_name = "Должность"
        verbose_name_plural = "Должности"
        ordering = ("name",)

    def __str__(self):
        return self.name


class Employee(models.Model):
    full_name = models.CharField("ФИО", max_length=255)
    department = models.ForeignKey(
        Department,
        verbose_name="Подразделение",
        on_delete=models.PROTECT,
        related_name="employees",
    )
    position = models.ForeignKey(
        Position,
        verbose_name="Должность",
        on_delete=models.PROTECT,
        related_name="employees",
    )
    is_active = models.BooleanField("Активен", default=True)

    class Meta:
        verbose_name = "Сотрудник"
        verbose_name_plural = "Сотрудники"
        ordering = ("full_name",)

    def __str__(self):
        return self.full_name


class Request(models.Model):
    class Status(models.TextChoices):
        NEW = "new", "Новая"
        IN_PROGRESS = "in_progress", "В работе"
        DONE = "done", "Выполнена"

    STATUS_TRANSITIONS = {
        Status.NEW: {Status.IN_PROGRESS},
        Status.IN_PROGRESS: {Status.DONE},
        Status.DONE: set(),
    }

    number = models.CharField("Номер", max_length=32, unique=True)
    created_at = models.DateTimeField("Дата создания", auto_now_add=True)
    author = models.ForeignKey(
        Employee,
        verbose_name="Автор",
        on_delete=models.PROTECT,
        related_name="authored_requests",
    )
    assignee = models.ForeignKey(
        Employee,
        verbose_name="Исполнитель",
        on_delete=models.PROTECT,
        related_name="assigned_requests",
    )
    description = models.TextField("Описание")
    due_date = models.DateField("Срок выполнения")
    status = models.CharField(
        "Статус",
        max_length=20,
        choices=Status.choices,
        default=Status.NEW,
    )

    class Meta:
        verbose_name = "Заявка"
        verbose_name_plural = "Заявки"
        ordering = ("due_date", "number")
        indexes = [
            models.Index(fields=("status",), name="request_status_idx"),
            models.Index(fields=("due_date",), name="request_due_date_idx"),
            models.Index(
                fields=("assignee", "status", "due_date"),
                name="req_asg_status_due_idx",
            ),
        ]

    def __str__(self):
        return f"{self.number} ({self.get_status_display()})"

    @property
    def is_overdue(self):
        return self.status != self.Status.DONE and self.due_date < timezone.localdate()

    def can_transition_to(self, new_status):
        return new_status in self.STATUS_TRANSITIONS[self.status]

    def transition_to(self, new_status):
        if new_status == self.status:
            return

        if not self.can_transition_to(new_status):
            raise ValidationError(
                {"status": f"Переход из статуса '{self.get_status_display()}' невозможен."}
            )

        self.status = new_status

    def clean(self):
        super().clean()

        if self.due_date:
            start_date = self.created_at.date() if self.created_at else timezone.localdate()
            if self.due_date < start_date:
                raise ValidationError(
                    {"due_date": "Срок выполнения не может быть раньше даты создания заявки."}
                )
