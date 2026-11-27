from django.core.management.base import BaseCommand

from jobs.geo import detect_country
from jobs.models import Job


class Command(BaseCommand):
    help = "Detect country for jobs that don't have one yet"

    def handle(self, *args, **options):
        updated = 0
        for job in Job.objects.filter(country="").only("pk", "location"):
            code = detect_country(job.location)
            if code:
                Job.objects.filter(pk=job.pk).update(country=code)
                updated += 1
        self.stdout.write(self.style.SUCCESS(f"Updated {updated} jobs"))