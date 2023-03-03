from django.db import IntegrityError, transaction
from curation.parsers.generic import GenericData
from catalog.models import Cohort


class CohortData(GenericData):

    def __init__(self,name,name_long,name_others,spreadsheet_name):
        GenericData.__init__(self,spreadsheet_name)
        self.name = name.strip()
        self.name_long = name_long.strip()
        self.name_others = name_others
        if self.name_others:
            self.name_others = self.name_others.strip()
        self.cohort_tuple = (self.name,self.name_long,self.name_others)

    def check_cohort(self):
        '''
        Check if a Cohort model already exists.
        Return type: Cohort model
        '''
        try:
            cohort = Cohort.objects.get(name_short__iexact=self.name, name_full__iexact=self.name_long)
            self.model = cohort
            #print(f'Cohort {self.name} found in the DB')
        except Cohort.DoesNotExist:
            self.model = None
            try:
                cohort = Cohort.objects.get(name_short__iexact=self.name)
                # Short name = long name
                if self.name == self.name_long:
                    self.model = cohort
                else:
                    print(f'A existing cohort has been found in the DB with the ID "{self.name}" ({self.name_long}). However the long name differs.')
            except Cohort.DoesNotExist:
                print(f'New cohort "{self.name}".')
                self.model = None
            except:
                print(f'ERROR with cohort {self.name} duplicated!')
        except:
            print(f'ERROR with cohort {self.name} ({self.name_long}) duplicated!')


    @transaction.atomic
    def create_cohort_model(self):
        '''
        Retrieve/Create an instance of the Cohort model.
        Return type: Cohort model
        '''
        try:
            with transaction.atomic():
                self.check_cohort()
                if not self.model:
                    self.model = Cohort()
                    self.model.name_short=self.name
                    self.model.name_full=self.name_long
                    if self.name_others:
                        self.model.name_others=self.name_others
                    self.model.save()
        except IntegrityError as e:
            self.model = None
            print('Error with the creation of the Cohort')

        return self.model
