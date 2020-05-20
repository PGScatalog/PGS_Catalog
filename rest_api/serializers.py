from rest_framework import serializers
from catalog.models import *


class CohortSerializer(serializers.ModelSerializer):

    class Meta:
        model = Cohort
        fields = ('name_short', 'name_full')
        read_only_fields = ('name_short', 'name_full')


class CohortExtendedSerializer(CohortSerializer):

    class Meta(CohortSerializer.Meta):
        fields = CohortSerializer.Meta.fields + ('associated_pgs_ids',)
        read_only_fields = CohortSerializer.Meta.read_only_fields + ('associated_pgs_ids',)


class SampleSerializer(serializers.ModelSerializer):
    sample_age = serializers.SerializerMethodField()
    followup_time = serializers.SerializerMethodField()
    cohorts = CohortSerializer(many=True, read_only=True)

    class Meta:
        model = Sample
        fields = ('sample_number', 'sample_cases', 'sample_controls', 'sample_percent_male',
                  'sample_age', 'phenotyping_free', 'followup_time',
                  'ancestry_broad', 'ancestry_free', 'ancestry_country', 'ancestry_additional',
                  'source_GWAS_catalog', 'source_PMID', 'cohorts', 'cohorts_additional')
        read_only_fields = ('sample_number', 'sample_cases', 'sample_controls', 'sample_percent_male',
                  'sample_age', 'phenotyping_free', 'followup_time',
                  'ancestry_broad', 'ancestry_free', 'ancestry_country', 'ancestry_additional',
                  'source_GWAS_catalog', 'source_PMID', 'cohorts', 'cohorts_additional')

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
        fields = ('id', 'samples')
        read_only_fields = ('id', 'samples')


class EFOTraitSerializer(serializers.ModelSerializer):

    class Meta:
        model = EFOTrait
        fields = ('id', 'label', 'description', 'url' )
        read_only_fields = ('id', 'label', 'description', 'url')


class EFOTraitExtendedSerializer(EFOTraitSerializer):
    trait_synonyms = serializers.SerializerMethodField()
    trait_mapped_terms = serializers.SerializerMethodField()

    class Meta(EFOTraitSerializer.Meta):
        fields = EFOTraitSerializer.Meta.fields + ('trait_synonyms', 'trait_mapped_terms', 'associated_pgs_ids')
        read_only_fields = EFOTraitSerializer.Meta.read_only_fields + ('trait_synonyms', 'trait_mapped_terms', 'associated_pgs_ids')

    def get_trait_synonyms(self, obj):
        if (obj.synonyms):
            return obj.synonyms_list
        return []
    def get_trait_mapped_terms(self, obj):
        if (obj.mapped_terms):
            return obj.mapped_terms_list
        return []


class MetricSerializer(serializers.ModelSerializer):

    class Meta:
        model = Metric
        fields = ('name', 'name_short', 'type', 'estimate', 'unit', 'ci', 'se')
        read_only_fields = ('name', 'name_short', 'type', 'estimate', 'unit', 'ci', 'se')


class PublicationSerializer(serializers.ModelSerializer):

    class Meta:
        model = Publication
        fields = ('id', 'title', 'doi', 'PMID', 'journal', 'firstauthor', 'date_publication')
        read_only_fields = ('id', 'title', 'doi', 'PMID', 'journal', 'firstauthor', 'date_publication')


class PublicationExtendedSerializer(PublicationSerializer):

    class Meta(PublicationSerializer.Meta):
        model = Publication
        fields = PublicationSerializer.Meta.fields + ('authors', 'associated_pgs_ids')
        read_only_fields = PublicationSerializer.Meta.read_only_fields + ('authors', 'associated_pgs_ids')


class ScoreSerializer(serializers.ModelSerializer):
    publication = PublicationSerializer(many=False, read_only=True)
    samples_variants = SampleSerializer(many=True, read_only=True)
    samples_training = SampleSerializer(many=True, read_only=True)
    trait_efo = EFOTraitSerializer(many=True, read_only=True)

    class Meta:
        model = Score
        fields = ('id', 'name', 'ftp_scoring_file', 'publication', 'samples_variants', 'samples_training',
                  'trait_reported', 'trait_additional', 'trait_efo', 'method_name', 'method_params',
                  'variants_number', 'variants_interactions', 'variants_genomebuild')
        read_only_fields = ('id', 'name', 'ftp_scoring_file', 'publication', 'samples_variants', 'samples_training',
                  'trait_reported', 'trait_additional', 'trait_efo', 'method_name', 'method_params',
                  'variants_number', 'variants_interactions', 'variants_genomebuild')


class PerformanceSerializer(serializers.ModelSerializer):
    phenotype_efo = EFOTraitSerializer(many=True, read_only=True)
    publication = PublicationSerializer(many=False, read_only=True)
    sampleset = SampleSetSerializer(many=False, read_only=True)

    class Meta:
        model = Performance
        fields = ('id', 'associated_pgs_id', 'phenotyping_reported', 'phenotype_efo', 'publication', 'sampleset', 'performance_metrics', 'covariates', 'performance_comments')
        read_only_fields = ('id', 'associated_pgs_id', 'phenotyping_reported', 'phenotype_efo', 'publication', 'sampleset', 'performance_metrics', 'covariates', 'performance_comments')


class ReleaseSerializer(serializers.ModelSerializer):

    class Meta:
        model = Release
        fields = ('date', 'score_count', 'performance_count', 'publication_count', 'notes', 'released_score_ids', 'released_publication_ids', 'released_performance_ids')
        read_only_fields = ('date', 'score_count', 'performance_count', 'publication_count', 'notes', 'released_score_ids', 'released_publication_ids', 'released_performance_ids')
