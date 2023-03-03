from django.db import IntegrityError, transaction
from curation.parsers.generic import GenericData
from catalog.models import Demographic

class DemographicData(GenericData):

    def __init__(self,type,value,spreadsheet_name):
        GenericData.__init__(self,spreadsheet_name)
        self.type = type.strip()
        self.value = value


    @transaction.atomic
    def create_demographic_model(self):
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
