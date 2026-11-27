import requests
from defusedxml import ElementTree
from django.core.management.base import BaseCommand

from jobs.models import ExchangeRate, Job

ECB_URL = "https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml"


class Command(BaseCommand):
    help = "Update EUR exchange rates from the European Central Bank and recalculate salaries"

    def handle(self, *args, **options):
        try:
            response = requests.get(ECB_URL, timeout=15)
            response.raise_for_status()
            root = ElementTree.fromstring(response.content)
        except (requests.RequestException, ElementTree.ParseError) as error:
            self.stderr.write(self.style.ERROR(f"Request failed: {error}"))
            return

        rates = 0
        for element in root.iter():
            currency, rate = element.get("currency"), element.get("rate")
            if currency and rate:
                ExchangeRate.objects.update_or_create(currency=currency, defaults={"per_eur": rate})
                rates += 1

        recalculated = 0
        jobs = (
            Job.objects.exclude(salary_currency="EUR")
            .exclude(salary_min=None, salary_max=None)
            .only("pk", "salary_min", "salary_max", "salary_currency", "salary_period")
        )
        for job in jobs:
            Job.objects.filter(pk=job.pk).update(
                salary_eur_min=ExchangeRate.to_eur_monthly(job.salary_min, job.salary_currency, job.salary_period),
                salary_eur_max=ExchangeRate.to_eur_monthly(job.salary_max, job.salary_currency, job.salary_period),
            )
            recalculated += 1

        self.stdout.write(self.style.SUCCESS(f"{rates} rates updated, {recalculated} salaries recalculated"))