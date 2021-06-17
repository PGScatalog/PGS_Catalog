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
    list_display = ["unit", "estimate", "estimate_type", 'range', 'range_type', 'variability', 'variability_type']
    list_filter = ('unit','estimate_type','range_type','variability_type')
    ordering = ('unit',)


@admin.register(EFOTrait)
class EFOTraitAdmin(admin.ModelAdmin):
    list_display = ["id", "label", "description", "url"]
    ordering = ('label',)


@admin.register(Metric)
class MetricAdmin(admin.ModelAdmin):
    list_display = ["name", "name_short", "estimate", "unit", "ci", "se"]
    list_filter = ('name_short',)
    ordering = ('name',)


@admin.register(Performance)
class PerformanceAdmin(admin.ModelAdmin):
    list_display = ["id", "score", "publication", "sampleset", "phenotyping_reported"]
    ordering = ('-num',)

    fieldsets = (
        (None, {
            'fields': ("id", "score", "publication", "sampleset", "phenotyping_reported", "phenotyping_efo", "covariates", "performance_comments")
        }),
        ('Curation', {
            'fields': ('date_released', 'curation_notes')
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ["num","id","date_released"]
        else:
            return []


@admin.register(Publication)
class PublicationAdmin(admin.ModelAdmin):
    list_display = ["id", "title", "authors", "PMID", "curation_status"]
    list_filter = ('curation_status',)
    ordering = ('-num',)

    fieldsets = (
        (None, {
            'fields': ("id", "title", "doi",  "PMID", "journal", "date_publication", "firstauthor", "authors")
        }),
        ('Curation', {
            'fields': ('date_released', 'curation_status', 'curation_notes')
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ["num","id","date_released"]
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
    list_display = ["ancestry_broad", "ancestry_country", "sample_number", "phenotyping_free", "source_GWAS_catalog", "source_PMID", "source_DOI", "display_sampleset"]
    ordering = ('ancestry_broad', "ancestry_country")


@admin.register(SampleSet)
class SampleSetAdmin(admin.ModelAdmin):
    list_display = ["id", "count_samples", "count_performances"]
    ordering = ('-num',)

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ["num","id"]
        else:
            return []

@admin.register(Score)
class ScoreAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "trait_reported", "method_name","variants_number", "publication"]
    ordering = ('-num',)

    fieldsets = (
        (None, {
            'fields': ("id", "name", "flag_asis", "publication",
                       "trait_reported", "trait_additional", "trait_efo",
                       #"samples_variants", "samples_training",
                       "method_name", "method_params",
                       "variants_number", "variants_interactions", "variants_genomebuild",
                       "ancestries")
        }),
        ('Curation', {
            'fields': ('date_released', 'curation_notes')
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ["num","id","date_released"]
        else:
            return []

@admin.register(TraitCategory)
class TraitCategoryAdmin(admin.ModelAdmin):
    list_display = ["label", "colour", "parent"]
    ordering = ('label',)

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ["id"]
        else:
            return []
