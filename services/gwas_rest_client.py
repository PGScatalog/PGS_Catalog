import requests


gwas_rest_root_url = "https://www.ebi.ac.uk/gwas/rest/api/v2"
study_url = gwas_rest_root_url + '/studies'


class GwasCountry:

    def __init__(self, data):
        self.data = data

    def get_country_name(self) -> str:
        return self.data['country_name']


class GwasAncestry:

    def __init__(self, data):
        self.data = data

    def get_type(self) -> str:
        return self.data['type']

    def get_number_of_individuals(self) -> int:
        return self.data['number_of_individuals']

    def get_ancestral_groups(self) -> list[str]:
        return [ancestral_group['ancestral_group'] for ancestral_group in self.data['ancestral_groups']]

    def get_country_of_origin(self) -> list[GwasCountry]:
        return [GwasCountry(country) for country in self.data['country_of_origin']]

    def get_country_of_recruitment(self) -> list[GwasCountry]:
        return [GwasCountry(country) for country in self.data['country_of_recruitment']]


class GwasStudy:
    data = {}
    ancestries = None

    def __init__(self, gcst_id, data):
        self.gcst_id = gcst_id
        self.data = data

    def get_pmid(self) -> str:
        return self.data['pubmed_id']

    def get_cohorts(self) -> list[str]:
        if 'cohort' in self.data:
            return self.data['cohort']
        else:
            return []

    def get_ancestries(self) -> list[GwasAncestry]:
        """
        Gets the ancestries associated with this study. The ancestries are fetched from the GWAS Catalog the first time
        this method is executed and cached for subsequent calls.
        :return: list of GWAS Ancestry objects
        """
        if self.ancestries is None:
            self.ancestries = GwasRestClient.fetch_study_ancestries(self.gcst_id)
        return self.ancestries


class GwasRestClient:

    @staticmethod
    def _request(url: str):
        response = requests.get(url)
        if response.status_code != 200:
            response.raise_for_status()
        return response.json()

    @staticmethod
    def fetch_study(gcst_id: str) -> GwasStudy:
        response_data = GwasRestClient._request(f'{study_url}/{gcst_id}')
        if response_data:
            return GwasStudy(gcst_id, response_data)

    @staticmethod
    def fetch_study_ancestries(gcst_id: str) -> list[GwasAncestry]:
        ancestries = []
        response_data = GwasRestClient._request(f'{study_url}/{gcst_id}/ancestries')
        if response_data:
            if '_embedded' in response_data:
                response_data = response_data['_embedded']
            for ancestry_data in response_data['ancestries']:
                ancestries.append(GwasAncestry(ancestry_data))
        return ancestries
