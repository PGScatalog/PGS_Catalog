import requests
from curation.parsers.generic import GenericData
from catalog.models import Publication


class PublicationData(GenericData):

    def __init__(self,table_publication,doi=None,PMID=None,publication=None):
        GenericData.__init__(self)
        self.table_publication = table_publication
        self.doi = doi
        self.PMID = PMID
        self.model = publication


    def get_publication_information(self):
        '''
        Retrieve the main publication information from EuropePMC (via their REST API),
        using the DOI or the PubMed ID.
        '''
        try:
            result = self.rest_api_call_to_epmc(f'doi:{self.doi}')
        except:
            if self.PMID:
                result = self.rest_api_call_to_epmc(f'ext_id:{self.PMID}')
            else:
                print(f'Can\'t find a match on EuropePMC for the publication: {self.doi}')

        if result:
            data_result = {
                'doi': result['doi'],
                'firstauthor': result['authorString'].split(',')[0],
                'authors': result['authorString'],
                'title': result['title'],
                'date_publication': result['firstPublicationDate']
            }
            if result['pubType'] == 'preprint':
                data_result['journal'] = result['bookOrReportDetails']['publisher']
            else:
                data_result['journal'] = result['journalTitle']
                if 'pmid' in result:
                    data_result['PMID'] = result['pmid']

            self.add_curation_notes()

            for field, value in data_result.items():
                self.add_data(field,value)
        else:
            print(f'Can\'t find a result on EuropePMC for the publication: {self.doi}')


    def add_curation_notes(self):
        '''
        Add the curation notes to the "data" dictionary if there is one in the Publication spreadsheet.
        '''
        if self.table_publication.shape[0] > 1:
            self.add_data('curation_notes',self.table_publication.iloc[1,0])


    def add_curation_status(self,curation_status):
        '''
        Add the curation status to the "data" dictionary if there is one.
        - curation_status: curation status from the configuration file
        '''
        if curation_status:
            self.add_data('curation_status',curation_status)


    def rest_api_call_to_epmc(self,query):
        '''
        REST API call to EuropePMC
        - query: the search query
        Return type: JSON
        '''
        payload = {'format': 'json'}
        payload['query'] = query
        result = requests.get('https://www.ebi.ac.uk/europepmc/webservices/rest/search', params=payload)
        result = result.json()
        result = result['resultList']['result'][0]
        return result


    def create_publication_model(self):
        '''
        Create an instance of the Publication model.
        Return type: Publication model
        '''
        if not self.model:
            self.model = Publication(**self.data)
            self.model.set_publication_ids(self.next_id_number(Publication))
            self.model.save()
        return self.model
