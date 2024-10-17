import requests
from catalog.models import Sample, Score, Cohort


class UpdateGwasStudies:
    """ Update the GWAS Catalog sample information where it is missing."""

    country_sep = ', '
    default_val = ''
    gwas_rest_url = 'https://www.ebi.ac.uk/gwas/rest/api/studies/'

    def __init__(self,verbose=None):
        self.samples = Sample.objects.filter(source_GWAS_catalog__isnull=False,sample_number__isnull=True,sample_cases__isnull=True,sample_controls__isnull=True)
        self.verbose = verbose


    def get_gwas_info(self,sample:Sample) -> dict:
        """
        Get the GWAS Study information related to the PGS sample.
        Check that all the required data is available
        > Parameter:
            - sample: instance of a Sample model
        > Return: dictionary (cohorts and ancestries)
        """
        study_data = { "ancestries": [] }
        gcst_id = sample.source_GWAS_catalog
        response = requests.get(f'{self.gwas_rest_url}{gcst_id}')

        print(f"\n# {gcst_id}:")

        if not response:
            print("\tNo response")
            return study_data
        response_data = response.json()
        if response_data:
            try:
                source_PMID = response_data['publicationInfo']['pubmedId']

                # Create list of cohorts if it exists in the GWAS study
                # This override the Cohorts found previously in the cohort column in the spreadsheet
                cohorts_list = []
                if 'cohort' in response_data.keys():
                    cohorts = response_data['cohort'].split('|')
                    for cohort in cohorts:
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
                for ancestry in response_data['ancestries']:

                    if ancestry['type'] != 'initial':
                        continue

                    ancestry_data = { 'source_PMID': source_PMID }
                    ancestry_data['sample_number'] = ancestry['numberOfIndividuals']

                    # ancestry_broad
                    for ancestralGroup in ancestry['ancestralGroups']:
                        if not 'ancestry_broad' in ancestry_data:
                            ancestry_data['ancestry_broad'] = self.default_val
                        else:
                            ancestry_data['ancestry_broad'] += self.country_sep
                        ancestry_data['ancestry_broad'] += ancestralGroup['ancestralGroup']

                    # ancestry_free
                    for countryOfOrigin in ancestry['countryOfOrigin']:
                        if countryOfOrigin['countryName'] != 'NR':
                            if not 'ancestry_free' in ancestry_data:
                                ancestry_data['ancestry_free'] = self.default_val
                            else:
                                ancestry_data['ancestry_free'] += self.country_sep
                            ancestry_data['ancestry_free'] += countryOfOrigin['countryName']

                    # ancestry_country
                    for countryOfRecruitment in ancestry['countryOfRecruitment']:
                        if countryOfRecruitment['countryName'] != 'NR':
                            if not 'ancestry_country' in ancestry_data:
                                ancestry_data['ancestry_country'] = self.default_val
                            else:
                                ancestry_data['ancestry_country'] += self.country_sep
                            ancestry_data['ancestry_country'] += countryOfRecruitment['countryName']
                    study_data["ancestries"].append(ancestry_data)

                if study_data["ancestries"]:
                    print(f'\t{len(study_data["ancestries"])} distinct ancestries')
                    if self.verbose:
                        for anc in study_data["ancestries"]:
                            print(f'\t{anc}')
                else:
                    print("\tNo ancestry")
            except:
                print(f'Error: can\'t fetch GWAS results for {gcst_id}')
        else:
            print("\tNo data")
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
                    # Override the list of cohorts found in the existing sample
                    if cohorts_list:
                        new_sample.cohorts.set(cohorts_list)
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
