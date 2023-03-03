from django.db import IntegrityError, transaction
from curation.parsers.generic import GenericData
from catalog.models import EFOTrait


class TraitData(GenericData):

    def __init__(self,trait_id,spreadsheet_name):
        GenericData.__init__(self,spreadsheet_name)
        self.trait_id = trait_id


    def efotrait_model(self):
        '''
        Getter/setter for the EFOTrait model
        Return type: EFOTrait model
        '''
        try:
            self.model = EFOTrait.objects.get(id__iexact=self.trait_id)
        except EFOTrait.DoesNotExist:
            self.create_efotrait_model()
        return self.model


    @transaction.atomic
    def create_efotrait_model(self):
        '''
        Create an instance of the EFOTrait model.
        Return type: EFOTrait model
        '''
        try:
            with transaction.atomic():
                self.model = EFOTrait(id=self.trait_id)
                self.model.parse_api()
                self.model.save()
        except IntegrityError as e:
            self.model = None
            print('Error with the creation of the EFOTrait model')
        return self.model
