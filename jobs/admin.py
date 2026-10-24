from django.contrib import admin
from .models import Job, Skill

@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ("title", "company", "location", "created_at")
    exclude = ("embedding",)
    readonly_fields = ("skills",)

@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    search_fields = ("name",)