from django.db import IntegrityError, transaction
from curation.parsers.generic import GenericData
from curation.parsers.trait import TraitData
from catalog.models import Score


class ScoreData(GenericData):

    method_name_replacement = {
        'C+T': 'Clumping and Thresholding (C+T)',
        'Ldpred': 'LDpred',
        'P+T': 'Pruning and Thresholding (P+T)',
        'PRScs': 'PRS-CS'
    }

    def __init__(self,score_name,spreadsheet_name):
        GenericData.__init__(self,spreadsheet_name)
        self.name = score_name
        self.data = {'name': score_name}


    @transaction.atomic
    def create_score_model(self,publication):
        '''
        Create an instance of the Score model.
        It also create instance(s) of the EFOTrait model if needed.
        - publication: instance of the Publication model
        Return type: Score model
        '''
        try:
            with transaction.atomic():
                self.model = Score()
                self.model.set_score_ids(self.next_id_number(Score))
                trait_ids = []
                trait_names = []
                for field, val in self.data.items():
                    if field == 'trait_efo':
                        trait_ids = [x.replace(':','_').strip() for x in val]
                    elif field == 'trait_efo_name':
                        trait_names = [x.replace(':','_').strip() for x in val]
                    else:
                        if field == 'method_name':
                            if val in self.method_name_replacement.keys():
                                val = self.method_name_replacement[val]
                        setattr(self.model, field, val)
                # Traits
                trait_ids_names = zip(trait_ids, trait_names)
                efo_traits = []
                for trait_id, trait_name in trait_ids_names:
                        trait = TraitData(trait_id, trait_name, self.spreadsheet_name)
                        efo = trait.efotrait_model()
                        if efo:
                            efo_traits.append(efo)
                        else:
                            self.import_report_error(f"Can't create the EFO model {trait_id} ({trait_name}): {trait.display_import_report_errors(False)}")
                            return None
                # Associate a Publication
                self.model.publication = publication
                self.model.save()

                for efo in efo_traits:
                    self.model.trait_efo.add(efo)
                self.model.save()
        except IntegrityError as e:
            self.model = None
            self.import_report_error('Error with the creation of the Score(s) and/or the Trait(s)')
        return self.model
