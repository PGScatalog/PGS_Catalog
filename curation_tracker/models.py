from django.db import models
from pgs_web import constants
from catalog import common
# Create your models here.


curation_admin_path = '/curation_admin/curation_tracker'
curation_annotation_path = curation_admin_path+'/curationpublicationannotation'
curation_publication_path = curation_admin_path+'/curationpublication'

class CurationCurator(models.Model):
    name = models.CharField('Curator Name', max_length=100, db_index=True)

    def __str__(self):
        return self.name


class CurationPublicationAnnotation(models.Model):
    """Class for publications with PGS"""

    ## Identifiers ##
    num = models.IntegerField('PGS Literature Triage (PGL)', primary_key=True)
    id = models.CharField('PGS Literature Triage ID (PGL)', max_length=30, db_index=True)

    # Publications
    study_name = models.CharField('Study Name', max_length=50, db_index=True)

    pgp_id = models.CharField('PGS Publication/Study ID (PGP)', max_length=30, null=True, blank=True, db_index=True)

    doi = models.CharField('digital object identifier (doi)', max_length=100, null=True, blank=True)
    PMID = models.IntegerField('PubMed ID (PMID)', null=True, blank=True)
    journal = models.CharField('Journal Name', max_length=100, null=True, blank=True)
    title = models.TextField('Title', null=True, blank=True)
    year = models.IntegerField('Year of Submission', null=True, blank=True)

    ## Curation info ##
    # First level
    CURATION_STATUS_LEVEL_1_CHOICES = [
        ('Author submission','Author submission'),
        ('Awaiting access','Awaiting access'),
        ('Awaiting curation (AS)','Awaiting curation (AS)'),
        ('Awaiting curation','Awaiting curation'),
        ('Contact author','Contact author'),
        ('Curation done','Curation done'),
        ('Curation done (AS)','Curation done (AS)'),
        ('Determined ineligible','Determined ineligible'),
        ('Outstanding curation query','Outstanding curation query'),
        ('Pending author response - follow up required', 'Pending author response - follow up required'),
        ('Pending author response', 'Pending author response'),
        ('Undergoing curation','Undergoing curation')
    ]
    first_level_curator = models.ForeignKey(CurationCurator, on_delete=models.PROTECT, related_name='curator_level1_name', verbose_name='First Level Curator Name', null=True, blank=True)
    first_level_curation_status = models.CharField(choices=CURATION_STATUS_LEVEL_1_CHOICES, default='Awaiting curation', max_length=50, verbose_name='First Level Curation Status', null=True, blank=True)
    first_level_date = models.DateField('First Level Curation Date', null=True, blank=True)
    first_level_comment = models.TextField('First Level Curation Comment', default='', null=True, blank=True)
    # Second level
    CURATION_STATUS_LEVEL_2_CHOICES = [
        ('-','-'),
        ('Awaiting curation','Awaiting curation'),
        ('Curation done','Curation done'),
        ('Determined ineligible','Determined ineligible'),
        ('Outstanding curation query','Outstanding curation query'),
        ('Pending author response', 'Pending author response'),
        ('Undergoing curation','Undergoing curation')
    ]
    second_level_curator = models.ForeignKey(CurationCurator, on_delete=models.PROTECT, related_name='curator_level2_name', verbose_name='Second Level Curator Name', null=True, blank=True)
    second_level_curation_status = models.CharField(choices=CURATION_STATUS_LEVEL_2_CHOICES, default='-', max_length=50, verbose_name='Second Level Curation Status', null=True, blank=True)
    second_level_date = models.DateField('Second Level Curation Date', null=True, blank=True)
    second_level_comment = models.TextField('Second Level Curation Comment', default='', null=True, blank=True)
    # Third level
    third_level_curator = models.ForeignKey(CurationCurator, on_delete=models.PROTECT, related_name='third_level_curator_name', verbose_name='Third Level Curator', null=True, blank=True)
    CURATION_STATUS_CHOICES = [
        ('Abandoned/Ineligble','Abandoned/Ineligble'),
        ('Pending Author Response','Pending Author Response'),
        ('Awaiting L1','Awaiting L1'),
        ('Awaiting L2','Awaiting L2'),
        ('Curated - Awaiting Import','Curated - Awaiting Import'),
        ('Imported - Awaiting Release','Imported - Awaiting Release'),
        ('Released','Released'),
        ('Embargoed','Embargoed'),
        ('Retired','Retired')
    ]
    curation_status = models.CharField(choices=CURATION_STATUS_CHOICES, default='Awaiting L1', max_length=50, verbose_name='Curation Status', null=True, blank=True)


    ## Eligibility ##
    DEV_NEW_SCORE_VAL = [
        ('y','Yes'),
        ('n','No'),
        ('MR','MR')
    ]
    EVAL_SCORE_VAL = [
        ('y','Yes'),
        ('n','No')
    ]
    EXTERNAL_VALIDATION = [
        ('y','Yes'),
        ('y (no dev)','Yes (no dev)'),
        ('y (eval only)','Yes (eval only)'),
        ('n','No'),
        ('NA','NA'),
        ('unsure', 'Unsure')
    ]
    TRAIT_MATCHING = [
        ('perfect match','perfect match'),
        ('related','related'),
        ('loosely related','loosely related'),
        ('unmatched','unmatched')
    ]
    SCORE_PROVIDED_VAL = [
        ('y','Yes'),
        ('n','No'),
        ('partial','Partial'),
        ('possibly','Possibly'),
        ('NA','NA'),
        ('unsure', 'Unsure')
    ]
    eligibility = models.BooleanField('Paper eligibility', default=False)
    eligibility_dev_score = models.CharField(choices=DEV_NEW_SCORE_VAL, max_length=50, verbose_name='Develop a new score', null=True, blank=True)
    eligibility_eval_score = models.CharField(choices=EVAL_SCORE_VAL, max_length=50, verbose_name='Evaluate existing score', null=True, blank=True)
    eligibility_external_valid = models.CharField(choices=EXTERNAL_VALIDATION, default='NA', max_length=50, verbose_name='External validation (dev and eval in different sample?)', null=True, blank=True)
    eligibility_trait_matching = models.CharField(choices=TRAIT_MATCHING, max_length=50, verbose_name='Trait matching', null=True, blank=True)
    eligibility_score_provided = models.CharField(choices=SCORE_PROVIDED_VAL, max_length=50, verbose_name='Score provided', null=True, blank=True)
    eligibility_description = models.TextField('Eligibility Comment', default='', null=True, blank=True)

    ## Release ##
    author_submission = models.BooleanField('Author Submission', default=False)
    embargoed = models.BooleanField('Embargoed Study', default=False)
    release_date = models.DateField('Release Date', null=True, blank=True)

    # Notes
    reported_trait = models.TextField('Reported Trait(s)',null=True, blank=True)
    gwas_and_pgs = models.CharField('GWAS + PGS', max_length=100, null=True, blank=True)
    comment = models.TextField('Curation Comments', default='', null=True, blank=True)

    class Meta:
        get_latest_by = 'num'

    def __str__(self):
        label = self.id
        if self.study_name:
            label = label+' ('+self.study_name+')'
        return label

    def set_annotation_ids(self, n):
        self.num = n
        self.id = 'PGL' + str(n).zfill(6)
