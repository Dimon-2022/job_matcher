from django import forms

from .models import Job

MAX_SALARY = 50000
SALARY_STEP = 100


class JobForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = [
            "title", "company", "location", "work_mode",
            "category", "level", "job_type",
            "salary_min", "salary_max",
            "url", "description",
        ]
        widgets = {
            "salary_min": forms.NumberInput(attrs={"step": SALARY_STEP, "min": 0, "max": MAX_SALARY}),
            "salary_max": forms.NumberInput(attrs={"step": SALARY_STEP, "min": 0, "max": MAX_SALARY}),
            "url": forms.URLInput(attrs={"placeholder": "https://company.com/careers/job"}),
            "description": forms.Textarea(attrs={"rows": 6}),
        }
        labels = {
            "salary_min": "Salary from (€ / month)",
            "salary_max": "Salary to (€ / month)",
            "url": "Link to the original job posting",
        }

    def clean_salary_min(self):
        return self._check_salary(self.cleaned_data.get("salary_min"))

    def clean_salary_max(self):
        return self._check_salary(self.cleaned_data.get("salary_max"))

    def _check_salary(self, value):
        if value is None:
            return value
        if value > MAX_SALARY:
            raise forms.ValidationError(f"Salary cannot be higher than {MAX_SALARY} €.")
        if value % SALARY_STEP != 0:
            raise forms.ValidationError(f"Salary must be a multiple of {SALARY_STEP} €.")
        return value

    def clean(self):
        cleaned_data = super().clean()
        salary_min = cleaned_data.get("salary_min")
        salary_max = cleaned_data.get("salary_max")

        if salary_min is not None and salary_max is not None and salary_min > salary_max:
            self.add_error("salary_max", "Maximum salary must be greater than or equal to minimum.")

        if cleaned_data.get("work_mode") != "remote" and not cleaned_data.get("location"):
            self.add_error("location", "Location is required for on-site and hybrid jobs.")

        return cleaned_data