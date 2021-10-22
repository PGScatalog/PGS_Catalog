from rest_framework import serializers
from catalog.models import *


class CohortSerializer(serializers.ModelSerializer):

    class Meta:
        model = Cohort
        meta_fields = ('name_short', 'name_full')
        fields = meta_fields
        read_only_fields = meta_fields


class CohortExtendedSerializer(CohortSerializer):

    class Meta(CohortSerializer.Meta):
        meta_fields = ('associated_pgs_ids',)
        fields = CohortSerializer.Meta.fields + meta_fields
        read_only_fields = CohortSerializer.Meta.read_only_fields + meta_fields


class SampleSerializer(serializers.ModelSerializer):
    sample_age = serializers.SerializerMethodField()
    followup_time = serializers.SerializerMethodField()
    cohorts = CohortSerializer(many=True, read_only=True)

    class Meta:
        model = Sample
        meta_fields = ('sample_number', 'sample_cases', 'sample_controls', 'sample_percent_male',
                    'sample_age', 'phenotyping_free', 'followup_time',
                    'ancestry_broad', 'ancestry_free', 'ancestry_country', 'ancestry_additional',
                    'source_GWAS_catalog', 'source_PMID','source_DOI', 'cohorts', 'cohorts_additional')
        fields = meta_fields
        read_only_fields = meta_fields

    def get_sample_age(self, obj):
        if (obj.sample_age):
            return obj.sample_age.display_values_dict()
        return None

    def get_followup_time(self, obj):
        if (obj.followup_time):
            return obj.followup_time.display_values_dict()
        return None


class SampleSetSerializer(serializers.ModelSerializer):
    samples = SampleSerializer(many=True, read_only=True)

    class Meta:
        model = SampleSet
        meta_fields = ('id', 'samples')
        fields = meta_fields
        read_only_fields = meta_fields


class EFOTraitSerializer(serializers.ModelSerializer):

    class Meta:
        model = EFOTrait
        meta_fields = ('id', 'label', 'description', 'url')
        fields = meta_fields
        read_only_fields = meta_fields


class EFOTraitExtendedSerializer(EFOTraitSerializer):
    trait_synonyms = serializers.SerializerMethodField()
    trait_mapped_terms = serializers.SerializerMethodField()
    trait_categories = serializers.SerializerMethodField('get_category_labels_list')

    class Meta(EFOTraitSerializer.Meta):
        meta_fields = ('trait_categories', 'trait_synonyms', 'trait_mapped_terms', 'associated_pgs_ids')
        fields = EFOTraitSerializer.Meta.fields + meta_fields
        read_only_fields = EFOTraitSerializer.Meta.read_only_fields + meta_fields

    def get_trait_synonyms(self, obj):
        if (obj.synonyms):
            return obj.synonyms_list
        return []
    def get_trait_mapped_terms(self, obj):
        if (obj.mapped_terms):
            return obj.mapped_terms_list
        return []
    def get_category_labels_list(self, obj):
        return obj.category_labels_list


class EFOTraitOntologySerializer(serializers.ModelSerializer):

    trait_synonyms = serializers.SerializerMethodField()
    trait_mapped_terms = serializers.SerializerMethodField()
    trait_categories = serializers.SerializerMethodField('get_category_labels_list')

    class Meta:
        model = EFOTrait_Ontology
        meta_fields = ('trait_categories', 'trait_synonyms', 'trait_mapped_terms',
                    'associated_pgs_ids', 'child_associated_pgs_ids')
        fields = EFOTraitExtendedSerializer.Meta.fields + meta_fields
        read_only_fields = EFOTraitExtendedSerializer.Meta.read_only_fields + meta_fields

    def get_trait_synonyms(self, obj):
        if (obj.synonyms):
            return obj.synonyms_list
        return []
    def get_trait_mapped_terms(self, obj):
        if (obj.mapped_terms):
            return obj.mapped_terms_list
        return []
    def get_category_labels_list(self, obj):
        return obj.category_labels_list


class EFOTraitOntologyChildSerializer(EFOTraitOntologySerializer):

    child_traits = EFOTraitOntologySerializer(many=True, read_only=True)

    class Meta(EFOTraitOntologySerializer.Meta):
        meta_fields = ('child_traits',)
        fields = EFOTraitOntologySerializer.Meta.fields + meta_fields
        read_only_fields = EFOTraitOntologySerializer.Meta.read_only_fields + meta_fields


class MetricSerializer(serializers.ModelSerializer):

    class Meta:
        model = Metric
        meta_fields = ('name', 'name_short', 'type', 'estimate', 'unit', 'ci', 'se')
        fields = meta_fields
        read_only_fields = meta_fields


class PublicationSerializer(serializers.ModelSerializer):

    class Meta:
        model = Publication
        meta_fields = ('id', 'title', 'doi', 'PMID', 'journal', 'firstauthor', 'date_publication')
        fields = meta_fields
        read_only_fields = meta_fields


class PublicationExtendedSerializer(PublicationSerializer):

    class Meta(PublicationSerializer.Meta):
        model = Publication
        meta_fields = ('authors', 'associated_pgs_ids')
        fields = PublicationSerializer.Meta.fields + meta_fields
        read_only_fields = PublicationSerializer.Meta.read_only_fields + meta_fields


class ScoreSerializer(serializers.ModelSerializer):
    publication = PublicationSerializer(many=False, read_only=True)
    samples_variants = SampleSerializer(many=True, read_only=True)
    samples_training = SampleSerializer(many=True, read_only=True)
    trait_efo = EFOTraitSerializer(many=True, read_only=True)
    matches_publication = serializers.SerializerMethodField('get_flag_asis')
    ancestry_distribution = serializers.SerializerMethodField('get_ancestries')

    class Meta:
        model = Score
        meta_fields = ('id', 'name', 'ftp_scoring_file', 'publication', 'matches_publication',
                    'samples_variants', 'samples_training', 'trait_reported', 'trait_additional',
                    'trait_efo', 'method_name', 'method_params', 'variants_number',
                    'variants_interactions', 'variants_genomebuild', 'weight_type', 'ancestry_distribution', 'license')
        fields = meta_fields
        read_only_fields = meta_fields

    def get_flag_asis(self, obj):
        return obj.flag_asis

    def get_ancestries(self, obj):
        return obj.ancestries


class PerformanceSerializer(serializers.ModelSerializer):
    phenotype_efo = EFOTraitSerializer(many=True, read_only=True)
    publication = PublicationSerializer(many=False, read_only=True)
    sampleset = SampleSetSerializer(many=False, read_only=True)

    class Meta:
        model = Performance
        meta_fields = ('id', 'associated_pgs_id', 'phenotyping_reported', 'phenotype_efo', 'publication',
                    'sampleset', 'performance_metrics', 'covariates', 'performance_comments')
        fields = meta_fields
        read_only_fields = meta_fields


class ReleaseSerializer(serializers.ModelSerializer):

    class Meta:
        model = Release
        meta_fields = ('date', 'score_count', 'performance_count', 'publication_count', 'notes',
                    'released_score_ids', 'released_publication_ids', 'released_performance_ids')
        fields = meta_fields
        read_only_fields = meta_fields


class TraitCategorySerializer(serializers.ModelSerializer):
    efotraits = EFOTraitSerializer(many=True, read_only=True)

    class Meta:
        model = TraitCategory
        meta_fields = ('label', 'efotraits')
        fields = meta_fields
        read_only_fields = meta_fields
