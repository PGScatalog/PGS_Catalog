from django.db import IntegrityError, transaction
from curation.parsers.generic import GenericData
from catalog.models import EFOTrait


class TraitData(GenericData):

    def __init__(self,trait_id,trait_name,spreadsheet_name):
        GenericData.__init__(self,spreadsheet_name)
        self.trait_id = trait_id
        self.trait_name = trait_name


    def efotrait_model(self):
        '''
        Getter/setter for the EFOTrait model
        Return type: EFOTrait model
        '''
        try:
            self.model = EFOTrait.objects.get(id__iexact=self.trait_id)
            if self.model.label.lower() != self.trait_name.lower():
                self.import_report_error(f"The given trait name for '{self.trait_id}' ({self.trait_name}) is different from the one provided by EFO ({self.model.label})")
                self.model = None
        except EFOTrait.DoesNotExist:
            self.create_efotrait_model()
        return self.model


    @transaction.atomic
    def create_efotrait_model(self):
        '''
        Create an instance of the EFOTrait model.
        Return type: EFOTrait model
        '''
        self.import_report_error(f"Test for {self.trait_id}")
        try:
            with transaction.atomic():
                self.model = EFOTrait(id=self.trait_id)
                self.model.parse_api()
                if self.model.label.lower() == self.trait_name.lower():
                    self.model.save()
                else:
                    self.import_report_error(f"The given trait name for '{self.trait_id}' ({self.trait_name}) is different from the one provided by EFO ({self.model.label})")
                    self.model = None
        except IntegrityError as e:
            self.model = None
            self.import_report_error('Error with the creation of the EFOTrait model')
        return self.model
