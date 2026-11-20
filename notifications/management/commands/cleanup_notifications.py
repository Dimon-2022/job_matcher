from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from notifications.models import Notification


class Command(BaseCommand):
    help = "Delete read notifications older than N days"

    def add_arguments(self, parser):
        parser.add_argument("--days", type=int, default=30)

    def handle(self, *args, **options):
        cutoff = timezone.now() - timedelta(days=options["days"])
        deleted, _ = Notification.objects.filter(is_read=True, created_at__lt=cutoff).delete()
        self.stdout.write(self.style.SUCCESS(f"Deleted {deleted} old notifications."))