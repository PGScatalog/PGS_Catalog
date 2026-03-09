import requests


gwas_rest_root_url = "https://www.ebi.ac.uk/gwas/rest/api/v2"
study_url = gwas_rest_root_url + '/studies'


class NotFoundError(Exception):
    def __init__(self, message):
        super().__init__(message)


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

    def __init__(self, gcst_id, data, gwas_rest_client=None):
        """:param gcst_id: GCST id of the study
        :param data: data of the study as returned by the GWAS Catalog REST API
        :param gwas_rest_client: the client to use to fetch the ancestries of the study. If not provided, a new instance
        of GwasRestClient will be created and used."""
        self.gcst_id = gcst_id
        self.data = data
        self.ancestries = None
        self.gwas_rest_client = gwas_rest_client if gwas_rest_client else GwasRestClient()

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
            self.ancestries = self.gwas_rest_client.fetch_study_ancestries(self.gcst_id)
        return self.ancestries


class GwasRestClient:
    """This class provides methods to fetch GWAS studies and their associated ancestries from the GWAS Catalog REST API.
    The fetched data is cached in memory to avoid redundant API calls."""

    def __init__(self):
        self.cached_studies = {}
        self.cached_ancestries = {}

    @staticmethod
    def _request(url: str):
        """
        Sends a GET request to the given URL and returns the response data.
        :raise NotFoundError: if the URL returns 404.
        :raise HTTPError: if any HTTP status code other than 200 and 404.
        """
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            response_data = response.json()
            message = response_data["errorMessage"] if "errorMessage" in response_data else f'Resource {url} not found'
            raise NotFoundError(message)
        else:
            response.raise_for_status()

    def fetch_study(self, gcst_id: str) -> GwasStudy:
        """
        Attempts to fetch the GWAS study with the given GCST id.
        :return: A GwasStudy object
        :raise NotFoundError: if the study can't be found.
        """
        if gcst_id not in self.cached_studies:
            response_data = GwasRestClient._request(f'{study_url}/{gcst_id}')
            if response_data:
                self.cached_studies[gcst_id] = GwasStudy(gcst_id, response_data, self)
        return self.cached_studies[gcst_id]

    def fetch_study_ancestries(self, gcst_id: str) -> list[GwasAncestry]:
        """
        Attempts to fetch the ancestries associated with the study with the given GCST id.
        :return: A list of GWAS Ancestries
        :raise NotFoundError: if the study can't be found.
        """
        if gcst_id not in self.cached_ancestries:
            ancestries = []
            response_data = GwasRestClient._request(f'{study_url}/{gcst_id}/ancestries')
            if response_data:
                if '_embedded' in response_data:
                    response_data = response_data['_embedded']
                for ancestry_data in response_data['ancestries']:
                    ancestries.append(GwasAncestry(ancestry_data))
            self.cached_ancestries[gcst_id] = ancestries
        return self.cached_ancestries[gcst_id]
