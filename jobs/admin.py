from django.contrib import admin
from .models import Job, Skill
from .models import CompanyFeed

@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ("title", "company", "location", "created_at")
    exclude = ("embedding",)
    readonly_fields = ("skills",)

@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    search_fields = ("name",)

@admin.register(CompanyFeed)
class CompanyFeedAdmin(admin.ModelAdmin):
    list_display = ("name", "ats", "slug", "is_active")
    list_filter = ("ats", "is_active")
    list_editable = ("is_active",)