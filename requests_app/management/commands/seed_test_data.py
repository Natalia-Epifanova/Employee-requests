import random
import time
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from requests_app.models import Department, Employee, Position, Request

DEPARTMENT_NAMES = [
    "Бухгалтерия",
    "ИТ",
    "Кадры",
    "Продажи",
    "Маркетинг",
    "Юридический отдел",
    "Закупки",
    "Логистика",
    "Склад",
    "Поддержка клиентов",
    "Администрация",
    "Финансовый отдел",
    "Безопасность",
    "Производство",
    "Контроль качества",
    "Аналитика",
    "Разработка",
    "Эксплуатация",
    "Обучение",
    "Проектный офис",
]

POSITION_NAMES = [
    "Специалист",
    "Ведущий специалист",
    "Менеджер",
    "Старший менеджер",
    "Аналитик",
    "Инженер",
    "Системный администратор",
    "Разработчик",
    "Тестировщик",
    "Бухгалтер",
    "Юрист",
    "Координатор",
    "Руководитель группы",
    "Начальник отдела",
    "Директор направления",
]

LAST_NAMES = [
    "Иванов",
    "Петров",
    "Сидоров",
    "Смирнов",
    "Кузнецов",
    "Попов",
    "Васильев",
    "Соколов",
    "Михайлов",
    "Новиков",
]

FIRST_NAMES = [
    "Алексей",
    "Дмитрий",
    "Сергей",
    "Анна",
    "Мария",
    "Елена",
    "Ольга",
    "Ирина",
    "Павел",
    "Николай",
]

MIDDLE_NAMES = [
    "Иванович",
    "Петрович",
    "Сергеевич",
    "Алексеевич",
    "Дмитриевич",
    "Ивановна",
    "Петровна",
    "Сергеевна",
    "Алексеевна",
    "Дмитриевна",
]

DESCRIPTIONS = [
    "Настроить рабочее место сотрудника",
    "Выдать доступ к внутренней системе",
    "Проверить ошибку в корпоративном приложении",
    "Подготовить документы по заявке",
    "Обновить программное обеспечение",
    "Провести консультацию по сервису",
    "Заменить оборудование",
    "Обработать обращение пользователя",
]

STATUS_CHOICES = [
    Request.Status.NEW,
    Request.Status.IN_PROGRESS,
    Request.Status.DONE,
]


class Command(BaseCommand):
    """Заполняет базу тестовыми сотрудниками и заявками."""

    help = (
        "Create departments, positions, employees, and requests for performance tests."
    )

    def add_arguments(self, parser):
        parser.add_argument("--employees", type=int, default=1000)
        parser.add_argument("--requests", type=int, default=1_000_000)
        parser.add_argument("--batch-size", type=int, default=10_000)
        parser.add_argument("--seed", type=int, default=42)
        parser.add_argument("--number-prefix", default=None)

    def handle(self, *args, **options):
        employees_target = options["employees"]
        requests_target = options["requests"]
        batch_size = options["batch_size"]
        random_generator = random.Random(options["seed"])
        number_prefix = options["number_prefix"] or timezone.now().strftime(
            "REQ%Y%m%d%H%M%S"
        )

        started_at = time.perf_counter()
        self._create_reference_data()
        self._create_employees(employees_target, batch_size, random_generator)
        self._create_requests(
            requests_target, batch_size, random_generator, number_prefix
        )
        elapsed = time.perf_counter() - started_at

        self.stdout.write(
            self.style.SUCCESS(
                f"Test data is ready: employees={Employee.objects.count()}, "
                f"requests={Request.objects.count()}, elapsed={elapsed:.2f}s"
            )
        )

    def _create_reference_data(self):
        with transaction.atomic():
            Department.objects.bulk_create(
                [Department(name=name) for name in DEPARTMENT_NAMES],
                ignore_conflicts=True,
            )
            Position.objects.bulk_create(
                [Position(name=name) for name in POSITION_NAMES],
                ignore_conflicts=True,
            )

        self.stdout.write("Departments and positions are ready.")

    def _create_employees(self, target_count, batch_size, random_generator):
        existing_count = Employee.objects.count()
        missing_count = max(target_count - existing_count, 0)
        if missing_count == 0:
            self.stdout.write(f"Employees already exist: {existing_count}.")
            return

        department_ids = list(Department.objects.values_list("id", flat=True))
        position_ids = list(Position.objects.values_list("id", flat=True))
        employees = []

        for index in range(existing_count + 1, target_count + 1):
            full_name = self._build_full_name(index, random_generator)
            employees.append(
                Employee(
                    full_name=full_name,
                    department_id=random_generator.choice(department_ids),
                    position_id=random_generator.choice(position_ids),
                    is_active=True,
                )
            )

            if len(employees) >= batch_size:
                Employee.objects.bulk_create(employees, batch_size=batch_size)
                employees.clear()
                self.stdout.write(f"Employees created: {Employee.objects.count()}.")

        if employees:
            Employee.objects.bulk_create(employees, batch_size=batch_size)

        self.stdout.write(
            self.style.SUCCESS(
                f"Employees created up to {Employee.objects.count()} records."
            )
        )

    def _create_requests(
        self, target_count, batch_size, random_generator, number_prefix
    ):
        existing_count = Request.objects.count()
        missing_count = max(target_count - existing_count, 0)
        if missing_count == 0:
            self.stdout.write(f"Requests already exist: {existing_count}.")
            return

        employee_ids = list(Employee.objects.values_list("id", flat=True))
        today = timezone.localdate()
        now = timezone.now()
        requests = []

        for index in range(existing_count + 1, target_count + 1):
            requests.append(
                Request(
                    number=f"{number_prefix}-{index:07d}",
                    created_at=now - timedelta(days=random_generator.randint(0, 60)),
                    author_id=random_generator.choice(employee_ids),
                    assignee_id=random_generator.choice(employee_ids),
                    description=random_generator.choice(DESCRIPTIONS),
                    due_date=today + timedelta(days=random_generator.randint(-30, 30)),
                    status=random_generator.choice(STATUS_CHOICES),
                )
            )

            if len(requests) >= batch_size:
                Request.objects.bulk_create(requests, batch_size=batch_size)
                requests.clear()
                self.stdout.write(f"Requests created: {Request.objects.count()}.")

        if requests:
            Request.objects.bulk_create(requests, batch_size=batch_size)

        self.stdout.write(
            self.style.SUCCESS(
                f"Requests created up to {Request.objects.count()} records."
            )
        )

    def _build_full_name(self, index, random_generator):
        return " ".join(
            [
                random_generator.choice(LAST_NAMES),
                random_generator.choice(FIRST_NAMES),
                f"{random_generator.choice(MIDDLE_NAMES)}-{index}",
            ]
        )
