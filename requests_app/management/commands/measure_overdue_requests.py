import time

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from requests_app.models import Employee, Request


class Command(BaseCommand):
    """Замеряет выборку просроченных заявок конкретного исполнителя."""

    help = (
        "Measure query time for overdue in-progress requests "
        "assigned to a specific employee."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--assignee-id",
            type=int,
            default=None,
            help="Employee id used as request assignee. If omitted, first employee is used.",
        )
        parser.add_argument(
            "--sample-size",
            type=int,
            default=10,
            help="How many found request numbers to print as a sample.",
        )
        parser.add_argument(
            "--explain",
            action="store_true",
            help="Print PostgreSQL EXPLAIN ANALYZE for the measured query.",
        )

    def handle(self, *args, **options):
        assignee = self._get_assignee(options["assignee_id"])
        sample_size = options["sample_size"]

        queryset = (
            Request.objects.filter(
                assignee=assignee,
                status=Request.Status.IN_PROGRESS,
                due_date__lt=timezone.localdate(),
            )
            .order_by("due_date")
            .values("id", "number", "due_date", "status", "assignee_id")
        )

        started_at = time.perf_counter()
        requests = list(queryset)
        elapsed = time.perf_counter() - started_at

        self.stdout.write(f"Assignee: {assignee.id} - {assignee.full_name}")
        self.stdout.write(f"Rows found: {len(requests)}")
        self.stdout.write(f"Elapsed: {elapsed:.6f}s")

        if requests and sample_size > 0:
            self.stdout.write("Sample:")
            for request in requests[:sample_size]:
                self.stdout.write(
                    f"  {request['number']} | due_date={request['due_date']} | "
                    f"status={request['status']}"
                )

        if options["explain"]:
            self.stdout.write("EXPLAIN ANALYZE:")
            self.stdout.write(queryset.explain(analyze=True, buffers=True))

    def _get_assignee(self, assignee_id):
        if assignee_id is not None:
            try:
                return Employee.objects.get(id=assignee_id)
            except Employee.DoesNotExist as exc:
                raise CommandError(
                    f"Employee with id={assignee_id} does not exist."
                ) from exc

        assignee = Employee.objects.order_by("id").first()
        if assignee is None:
            raise CommandError("No employees found. Run seed_test_data first.")
        return assignee
