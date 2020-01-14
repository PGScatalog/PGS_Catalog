from django.contrib import admin

# Register your models here.
from .models import *

admin.site.site_header = "PGS Catalog - Admin"
admin.site.site_title = "PGS Catalog - Admin Portal"
admin.site.index_title = "Welcome to PGS Catalog Portal"


@admin.register(Cohort)
class CohortAdmin(admin.ModelAdmin):
    list_display = ["name_short", "name_full"]
    ordering = ('name_short',)


@admin.register(Demographic)
class DemographicAdmin(admin.ModelAdmin):
    list_display = ["unit", "estimate", "estimate_type", "ci", "range", "se"]
    ordering = ('unit',)


@admin.register(EFOTrait)
class EFOTraitAdmin(admin.ModelAdmin):
    list_display = ["id", "label", "description", "url"]
    ordering = ('-id',)


@admin.register(Metric)
class MetricAdmin(admin.ModelAdmin):
    list_display = ["name", "name_short", "estimate", "unit", "ci", "se"]
    ordering = ('name',)


@admin.register(Performance)
class PerformanceAdmin(admin.ModelAdmin):
    list_display = ["id", "score", "publication", "sampleset", "phenotyping_reported"]
    ordering = ('-id',)

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ["num","id"]
        else:
            return []


@admin.register(Publication)
class PublicationAdmin(admin.ModelAdmin):
    list_display = ["id", "title", "authors", "PMID", "curation_status"]
    ordering = ('-id',)

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ["num","id"]
        else:
            return []


@admin.register(Release)
class ReleaseAdmin(admin.ModelAdmin):
    list_display = ["date", "score_count", "performance_count", "publication_count"]
    ordering = ("-date",)

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ["id"]
        else:
            return []


@admin.register(Sample)
class SampleAdmin(admin.ModelAdmin):
    list_display = ["ancestry_broad", "ancestry_country", "sample_number", "phenotyping_free", "source_GWAS_catalog", "source_PMID", "display_sampleset"]
    ordering = ('ancestry_broad', "ancestry_country")


@admin.register(SampleSet)
class SampleSetAdmin(admin.ModelAdmin):
    list_display = ["id", "count_samples", "count_performances"]
    ordering = ('-id',)

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ["num","id"]
        else:
            return []

@admin.register(Score)
class ScoreAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "trait_reported", "method_name","variants_number", "publication"]
    ordering = ('-id',)

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ["num","id"]
        else:
            return []
