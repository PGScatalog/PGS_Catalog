from catalog.models import Sample, Score, Cohort
from services.gwas_rest_client import GwasRestClient, NotFoundError


class UpdateGwasStudies:
    """ Update the GWAS Catalog sample information where it is missing."""

    country_sep = ', '
    default_val = ''

    def __init__(self,verbose=None):
        self.samples = Sample.objects.filter(source_GWAS_catalog__isnull=False,sample_number__isnull=True,sample_cases__isnull=True,sample_controls__isnull=True)
        self.verbose = verbose


    def get_gwas_info(self, sample:Sample) -> dict:
        """
        Get the GWAS Study information related to the PGS sample.
        Check that all the required data is available
        > Parameter:
            - sample: instance of a Sample model
        > Return: dictionary (cohorts and ancestries)
        """
        study_data = {"ancestries": []}
        gcst_id = sample.source_GWAS_catalog
        print(f"\n# {gcst_id}:")

        try:
            gwas_study = GwasRestClient.fetch_study(gcst_id)
            source_PMID = gwas_study.get_pmid()

            # Create list of cohorts if it exists in the GWAS study
            # This override the Cohorts found previously in the cohort column in the spreadsheet
            cohorts_list = []
            for cohort in gwas_study.get_cohorts():
                cohort_id = cohort.upper()
                try:
                    cohort_model = Cohort.objects.get(name_short__iexact=cohort_id)
                    cohorts_list.append(cohort_model)
                except Cohort.DoesNotExist:
                    print(f"New cohort found: {cohort_id}")
                    cohort_model = Cohort(name_short=cohort_id,name_full=cohort_id)
                    cohort_model.save()
                    cohorts_list.append(cohort_model)
            if cohorts_list:
                study_data['cohorts'] = cohorts_list

            # Ancestries
            for gwas_ancestry in gwas_study.get_ancestries():

                if gwas_ancestry.get_type() != 'initial':
                    continue

                ancestry_data = {'source_PMID': source_PMID,
                                 'sample_number': gwas_ancestry.get_number_of_individuals()}

                # ancestry_broad
                ancestral_groups = gwas_ancestry.get_ancestral_groups()
                if ancestral_groups:
                    ancestry_data['ancestry_broad'] = self.country_sep.join(ancestral_groups)

                # ancestry_free
                countries_of_origin = [country.get_country_name() for country in gwas_ancestry.get_country_of_origin()
                                       if country.get_country_name() != 'NR']
                if countries_of_origin:
                    ancestry_data['ancestry_free'] = self.country_sep.join(countries_of_origin)

                # ancestry_country
                countries_of_recruitment = [country.get_country_name() for country in gwas_ancestry.get_country_of_recruitment()
                                            if country.get_country_name() != 'NR']
                if countries_of_recruitment:
                    ancestry_data['ancestry_country'] = self.country_sep.join(countries_of_recruitment)

                study_data["ancestries"].append(ancestry_data)

            if study_data["ancestries"]:
                print(f'\t{len(study_data["ancestries"])} distinct ancestries')
                if self.verbose:
                    for anc in study_data["ancestries"]:
                        print(f'\t{anc}')
            else:
                print("\tNo ancestry")

        except NotFoundError as e:
            print(str(e))
        except:
            print(f'Error: can\'t fetch GWAS results for {gcst_id}')

        return study_data


    def update_studies(self):
        for sample in self.samples:
            gwas_study = self.get_gwas_info(sample)
            new_samples = []
            cohorts_list = []
            # List of cohorts
            if 'cohorts' in gwas_study.keys():
                cohorts_list = gwas_study['cohorts']
            # List of ancestry data
            for gwas_ancestry in gwas_study['ancestries']:
                new_sample = Sample()
                new_sample.source_GWAS_catalog = sample.source_GWAS_catalog
                for field, val in gwas_ancestry.items():
                    if type(val) == str:
                        val = val.strip()
                    setattr(new_sample, field, val)
                new_sample.save()

                # Cohorts data
                if cohorts_list or sample.cohorts:
                    # Use the list of cohorts from the GWAS study (if available)
                    # Update the list of cohorts from the existing sample if new cohorts are found in the GWAS study
                    if cohorts_list:
                        new_sample.cohorts.set(cohorts_list)
                        # Print a message if the 2 list of cohorts (old & new) are different
                        if sample.cohorts:
                            new_set = sorted([x.name_short.upper() for x in cohorts_list])

                            old_set_string = ', '.join(sorted([x.name_short.upper() for x in sample.cohorts.all()]))
                            new_set_string = ', '.join(new_set)
                            if old_set_string != new_set_string:
                                # Add cohorts which are already associated to the sample in the database, but not in the GWAS study
                                for sample_cohort in sample.cohorts.all():
                                    if sample_cohort.name_short.upper() not in new_set:
                                        new_sample.cohorts.add(sample_cohort)
                                print(f"\t/!\ Replacing cohorts list:")
                                print(f"\t  - Old set: {old_set_string}")
                                print(f"\t  + New set: {', '.join(sorted([x.name_short.upper() for x in new_sample.cohorts.all()]))}")
                    # Copy the list of cohorts from the existing sample.
                    # Need to be added once the new Sample object as been saved,
                    # i.e. when the Sample `id` has been created
                    elif sample.cohorts:
                        for cohort in sample.cohorts.all():
                            new_sample.cohorts.add(cohort)
                    new_sample.save()

                new_samples.append(new_sample)

            if new_samples:
                # Update Score - sample_variants list
                scores = Score.objects.filter(samples_variants__in=[sample])
                for score in scores:
                    print(f"\t>> SCORE updated: {score.id}")
                    score.samples_variants.remove(sample)
                    score.samples_variants.add(*new_samples)

                # Delete "old" sample
                sample.delete()


################################################################################

def run():

    gwas_studies = UpdateGwasStudies(verbose=True)
    gwas_studies.update_studies()
