from django.db import IntegrityError, transaction
from curation.parsers.generic import GenericData
from catalog.models import Demographic

class DemographicData(GenericData):

    def __init__(self,type:str,value:str|int|float,spreadsheet_name:str) -> None:
        GenericData.__init__(self,spreadsheet_name)
        self.type = type.strip()
        self.value = value


    def update_demographic_data(self) -> None:
        """ Change the default estimate_type value if no estimate is provided """
        demographic_keys = self.data.keys()
        if not 'estimate' in demographic_keys and 'range' in demographic_keys:
            self.data['estimate_type'] = 'range'


    @transaction.atomic
    def create_demographic_model(self) -> Demographic:
        '''
        Create an instance of the Demographic model.
        Return type: Demographic model
        '''
        try:
            with transaction.atomic():
                self.model = Demographic(**self.data)
                self.model.save()
        except IntegrityError as e:
            print('Error with the creation of the Demographic')

        return self.model
