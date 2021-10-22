import requests
from catalog.models import EFOTrait, TraitCategory, EFOTrait_Ontology, Score


class UpdateEFO:

    #---------------#
    # Configuration #
    #---------------#


    parent_key = 'parent'
    child_key  = 'children'
    colour_key = 'colour'
    efo_key = 'efo_ids'
    direct_pgs_ids_key = 'direct_pgs_ids'
    child_pgs_ids_key = 'child_pgs_ids'

    categories_info = {
        'Biological process': { colour_key: '#BEBADA', parent_key: 'biological process', efo_key: ['GO_0008150'] },
        'Body measurement': { colour_key: '#66CCFF', parent_key: 'body weights and measures', efo_key: ['EFO_0004324'] },
        'Cancer': { colour_key: '#BC80BD', parent_key: 'neoplasm', efo_key: ['EFO_0000616'] },
        'Cardiovascular disease': { colour_key: '#B33232', parent_key: 'cardiovascular disease', efo_key: ['EFO_0000319'] },
        'Cardiovascular measurement': { colour_key: '#80B1D3', parent_key: 'cardiovascular measurement', efo_key: ['EFO_0004298'] },
        'Digestive system disorder': { colour_key: '#B7704C', parent_key: 'digestive system disease', efo_key: ['EFO_0000405'] },
        'Hematological measurement': { colour_key: '#8DD3C7', parent_key: 'hematological measurement', efo_key: ['EFO_0004503'] },
        'Immune system disorder': { colour_key: '#FFED6F', parent_key: 'immune system disease', efo_key: ['EFO_0000540'] },
        'Inflammatory measurement': { colour_key: '#CCEBC5', parent_key: 'inflammatory biomarker measurement', efo_key: ['EFO_0004872'] },
        'Lipid or lipoprotein measurement': { colour_key: '#B3DE69', parent_key: 'lipid or lipoprotein measurement', efo_key: ['EFO_0004529','EFO_0004732','EFO_0005105'] },
        'Liver enzyme measurement': { colour_key: '#669900', parent_key: 'liver enzyme measurement', efo_key: ['EFO_0004582'] },
        'Metabolic disorder': { colour_key: '#FDB462', parent_key: 'metabolic disease', efo_key: ['EFO_0000589'] },
        'Neurological disorder': { colour_key: '#FFFFB3', parent_key: 'nervous system disease', efo_key: ['EFO_0000618'] },
        'Other disease': { colour_key: '#FF3399', parent_key: 'disease', efo_key: ['EFO_0000408'] },
        'Other measurement': { colour_key: '#006699', parent_key: 'measurement', efo_key: ['EFO_0001444'] },
        'Other trait': { colour_key: '#FB8072', parent_key: 'experimental factor', efo_key: ['EFO_0000001'] },
        'Response to drug': { colour_key: '#FCCDE5', parent_key: 'response to drug', efo_key: ['GO_0042493'] },
        'Sex-specific PGS': { colour_key: '#00adb5', parent_key: 'sex_specific_pgs', efo_key: ['PATO_0000383','PATO_0000384'] } #,'PATO_0001894','PATO_0000047'}
    }

    items_separator = ' | '

    exclude_terms = [
        'biological process',
        'biological sex',
        'disease',
        'disease by anatomical system',
        'disease by cellular process disrupted',
        'disease by subcellular system affected',
        'disease characteristic',
        'disorder by anatomical region',
        'disposition',
        'experimental factor',
        'information entity',
        'material property',
        'measurement',
        'phenotypic sex',
        'process',
        'quality',
        'Thing'
    ]

    pgs_specific_traits = {
        'sex'   : 'Sex-specific PGS',
        'male'  : 'Sex-specific PGS',
        'female': 'Sex-specific PGS'
    }


    def __init__(self):
        self.ontology_data = {}
        self.efo_traits_with_category = set()
        self.efo_categories_by_cat = {}
        self.entry_count = 0
        self.total_entries = 0
        # Category
        self.categories = {}
        self.efotrait_categories = []
        self.trait_categories = set()
        self.warnings = []
        self.build_efo_category_labels_dict()


    def build_efo_category_labels_dict(self):
        ''' Build a new dictionary from `categories_info` { EFO ID: Category label}. '''
        for cat_label in self.categories_info.keys():
            for efo_id in self.categories_info[cat_label][self.efo_key]:
                self.categories[efo_id] = cat_label
        self.efotrait_categories = self.categories.keys()


    def format_data(self, response):
        ''' Format some of the data to match the format in the database. '''
        data = {}
        # Synonyms
        new_synonyms_string = ''
        new_synonyms = response['synonyms']
        if (new_synonyms):
            new_synonyms_string = self.items_separator.join(sorted(new_synonyms))
        data['synonyms'] = new_synonyms_string

        # Mapped terms
        new_mapped_terms_string = ''
        if 'database_cross_reference' in response['annotation']:
            new_mapped_terms = response['annotation']['database_cross_reference']
            if (new_mapped_terms):
                new_mapped_terms_string = self.items_separator.join(sorted(new_mapped_terms))
        data['mapped_terms'] = new_mapped_terms_string

        # Make description
        try:
            desc = response['obo_definition_citation'][0]
            str_desc = desc['definition']
            for x in desc['oboXrefs']:
                if x['database'] != None:
                    if x['id'] != None:
                        str_desc += ' [{}: {}]'.format(x['database'], x['id'])
                    else:
                        str_desc += ' [{}]'.format(x['database'])
            new_desc = str_desc
        except:
            if type(response['description']) == list:
                new_desc = self.items_separator.join(response['description'])
            else:
                new_desc = response['description']
        data['description'] = new_desc

        return data


    def update_efo_info(self, trait):
        ''' Fetch EFO information from an EFO ID, using the OLS REST API '''
        trait_id = trait.id
        obo_id = trait_id.replace('_',':')
        ols_url = f'https://www.ebi.ac.uk/ols/api/ontologies/efo/terms?obo_id={obo_id}'
        response = requests.get(ols_url)
        response = response.json()['_embedded']['terms']
        if len(response) == 1:
            response = response[0]
            new_label = response['label']

            if response['is_obsolete']:
                obsolete_msg = f'The trait "{new_label}" ({trait_id}) is labelled as obsolete by EFO!'
                print(f'WARNING: {obsolete_msg}')
                self.warnings.append(obsolete_msg)

            # Synonyms, Mapped terms and description
            efo_formatted_data = self.format_data(response)

            trait_has_changed = 0
            if new_label != trait.label:
                #print("\tnew label '"+new_label+"'")
                trait_has_changed = 1
                trait.label = new_label
            if efo_formatted_data['description'] != trait.description:
                #print("\tnew desc '"+', '.join(new_desc)+"'")
                trait_has_changed = 1
                trait.description = efo_formatted_data['description']
            if efo_formatted_data['synonyms'] != trait.synonyms and efo_formatted_data['synonyms'] != '':
                #print("\tnew syn: "+str(len(new_synonyms_string)))
                trait_has_changed = 1
                trait.synonyms = efo_formatted_data['synonyms']
            if efo_formatted_data['mapped_terms'] != trait.mapped_terms and efo_formatted_data['mapped_terms'] != '':
                #print("\tnew map: "+str(len(new_mapped_terms)))
                trait_has_changed = 1
                trait.mapped_terms = efo_formatted_data['mapped_terms']
            if trait_has_changed == 1:
                trait.save()
        else:
            print("The script can't update the trait '"+trait.label+"' ("+trait_id+"): the API returned "+str(len(response))+" results.")


    def add_efo_trait_to_efotrait_ontology(self, trait):
        ''' Import the entries in the EFOTrait table into EFOTrait_Ontology. '''
        try:
            queryset = EFOTrait_Ontology.objects.get(id=trait.id)
        except EFOTrait_Ontology.DoesNotExist:
            EFOTrait_Ontology.objects.create(
                id=trait.id,
                label=trait.label,
                description=trait.description,
                url=trait.url,
                synonyms=trait.synonyms,
                mapped_terms=trait.mapped_terms
            )


    def add_efo_parents_to_efotrait_ontology(self, trait):
        ''' Fetch EFO information from an EFO ID, using the OLS REST API and
        import it into the EFOTrait_Ontology table. '''
        trait_id = trait.id
        try:
            ontology_trait = EFOTrait_Ontology.objects.get(id=trait_id)
        except EFOTrait_Ontology.DoesNotExist:
            print("No existing entries for the trait "+trait_id+"in the EFOTrait_Ontology model")
            exit(1)

        # Direct trait / PGS score associations
        score_ids = trait.associated_pgs_ids
        if score_ids:
            if not trait_id in self.ontology_data:
                self.ontology_data[trait_id] = { self.direct_pgs_ids_key: set() }
            if not self.direct_pgs_ids_key in self.ontology_data[trait_id]:
                self.ontology_data[trait_id][self.direct_pgs_ids_key] = set()

            for score_id in score_ids:
                self.ontology_data[trait_id][self.direct_pgs_ids_key].add(score_id)

        parents_list = self.get_parents(trait)
        if parents_list:
            self.add_parents(parents_list, ontology_trait, score_ids)
            self.collect_efo_category_info(ontology_trait,parents_list)


    def get_parents(self,trait):
        ols_url = 'https://www.ebi.ac.uk/ols/api/ontologies/efo/ancestors?id={}'
        response = requests.get(ols_url.format(trait.id))
        response_json = response.json()
        ols_embedded = '_embedded'
        ols_links = '_links'
        ols_next  = 'next'
        if ols_embedded in response_json:
            response = response_json[ols_embedded]['terms']
            # Fetch parent data and store it
            if len(response) > 0:
                if ols_links in response_json:
                    total_terms_count = response_json['page']['totalElements']

                    while ols_next in response_json[ols_links]:
                        next_url = response_json[ols_links][ols_next]['href']
                        response_next = requests.get(next_url)
                        response_json = response_next.json()
                        response_terms = response_json[ols_embedded]['terms']
                        response = response + response_terms

                    if total_terms_count != len(response):
                        print(f'The number of ancestors of "{trait.label}" retrieved doesn\'t match the number of ancestors declared by the REST API: {total_terms_count} vs {len(response)}')
                        response = None
                else:
                    print("The script can't retrieve the parents of the trait '"+trait.label+"' ("+trait.id+"): the API returned "+str(len(response))+" results.")
                    response = None
            else:
                print("  >> WARNING: Can't find parents for the trait '"+trait.id+"'.")
                response = None
        return response


    def add_parents(self,response,ontology_trait,score_ids):
        for parent in response:
            parent_id = parent['short_form']
            parent_label = parent['label']
            if not parent_label in self.exclude_terms:

                # Check obsolete terms
                if parent['is_obsolete']:
                    obsolete_msg = f'The parent trait "{parent_label}" ({parent_id}) is labelled as obsolete by EFO!'
                    print(f'WARNING: {obsolete_msg}')
                    self.warnings.append(obsolete_msg)

                # Child relations
                if parent_id in self.ontology_data:
                    if self.child_key in self.ontology_data[parent_id]:
                        self.ontology_data[parent_id][self.child_key].append(ontology_trait)
                    else:
                        self.ontology_data[parent_id][self.child_key] = [ontology_trait]
                else:
                    self.ontology_data[parent_id] = { self.child_key: [ontology_trait] }

                # Children trait / PGS score associations
                if score_ids:
                    if not parent_id in self.ontology_data:
                        self.ontology_data[parent_id] = { self.child_pgs_ids_key: set() }
                    if not self.child_pgs_ids_key in self.ontology_data[parent_id]:
                        self.ontology_data[parent_id][self.child_pgs_ids_key] = set()

                    for score_id in score_ids:
                        self.ontology_data[parent_id][self.child_pgs_ids_key].add(score_id)

                try:
                    parent_trait = EFOTrait_Ontology.objects.get(id=parent_id)
                except EFOTrait_Ontology.DoesNotExist:
                    # Synonyms, Mapped terms and description
                    parent_formatted_data = self.format_data(parent)

                    EFOTrait_Ontology.objects.create(
                        id=parent_id,
                        label=parent_label,
                        description=parent_formatted_data['description'],
                        url=parent['iri'],
                        synonyms=parent_formatted_data['synonyms'],
                        mapped_terms=parent_formatted_data['mapped_terms']
                    )


    def update_parent_child(self, ontology_trait):
        ''' Build the parent/child relations before updating the EFOTrait_Ontology model'''
        ontology_id = ontology_trait.id
        self.entry_count += 1
        # >>>>>>>>>>> PRINT <<<<<<<<<<<<<
        print(" - "+ontology_id+" ("+ontology_trait.label+")"+" | "+str(self.entry_count)+'/'+str(self.total_entries))

        if ontology_id in self.ontology_data.keys():
            # Update with child EFOTrait(s)
            if self.child_key in self.ontology_data[ontology_id]:
                for child_trait in self.ontology_data[ontology_id][self.child_key]:
                    ontology_trait.child_traits.add(child_trait)

            # Update with direct trait/PGS Score IDs associations
            if self.direct_pgs_ids_key in self.ontology_data[ontology_id]:
                pgs_ids = sorted(list(self.ontology_data[ontology_id][self.direct_pgs_ids_key]))
                pgs_scores = Score.objects.filter(id__in=pgs_ids).order_by('id')
                for pgs_score in pgs_scores:
                    ontology_trait.scores_direct_associations.add(pgs_score)

            # Update with child trait/PGS Score IDs associations
            if self.child_pgs_ids_key in self.ontology_data[ontology_id]:
                child_pgs_ids = sorted(list(self.ontology_data[ontology_id][self.child_pgs_ids_key]))
                child_pgs_scores = Score.objects.filter(id__in=child_pgs_ids).order_by('id')
                for child_pgs_score in child_pgs_scores:
                    ontology_trait.scores_child_associations.add(child_pgs_score)

        ontology_trait.save()


    def collect_efo_category_info(self, trait, response=None):
        '''
        Fetch the trait category from an EFO ID, using its parents
        > Parameters:
            - trait: EFOTrait_Ontology object
            - response: JSON results from the OLS REST API call (if provided)
        > Return: None
        '''
        trait_id = trait.id
        trait_label = trait.label

        if not trait_id in self.efo_traits_with_category:
            categories_list = set()
            # PGS-specific category
            if trait_label in self.pgs_specific_traits.keys():
                categories_list.add(self.pgs_specific_traits[trait_label])
            else:
                # Fetch the parent terms if none provided (response)
                if response == None:
                    response = self.get_parents(trait)
                # Get Category info
                categories_list = self.get_category_info(trait,response)
            self.store_category_info(trait_id,categories_list)


    def get_category_info(self, trait, response):
        '''
        Fetch the trait category from an EFO ID, using OLS REST API 'ancestors' results
        > Parameters:
            - trait: EFOTrait_Ontology object
            - response: JSON results from the OLS REST API call
        > Return: List of Trait categories
        '''
        trait_id = trait.id
        trait_label = trait.label
        ols_trait_list = set()
        ols_categories = set()
        for parent in response:
            parent_id = parent['short_form']
            if parent_id in self.efotrait_categories:
                ols_trait_list.add(parent_id)
        # Add trait if it part of the Categories list
        if trait_id in self.efotrait_categories:
            ols_trait_list.add(trait_id)

        # Exit if no category association found
        if len(ols_trait_list) == 0:
            print(f'No Trait category found for the trait "{trait_label}" ({trait_id}).')
            return

        # Other trait
        if len(ols_trait_list) > 1 and 'EFO_0000001' in ols_trait_list:
            ols_trait_list.remove('EFO_0000001')
        # Other disease
        if len(ols_trait_list) > 1 and 'EFO_0000408' in ols_trait_list:
            ols_trait_list.remove('EFO_0000408')
        # Other measurement
        if len(ols_trait_list) > 1 and 'EFO_0001444' in ols_trait_list:
            ols_trait_list.remove('EFO_0001444')

        for ols_trait_id in ols_trait_list:
            ols_categories.add(self.categories[ols_trait_id])

        return ols_categories


    def store_category_info(self,trait_id,categories_list):
        '''
        Create TraitCategory instance if it doesn't exist in the DB
        and add the trait to the list of traits associated with the trait category
        > Parameters:
            - trait_id: Ontology trait identifier (e.g. EFO_0001645)
            - categories_list: List of category labels associated with the trait
        > Return: None
        '''
        # Add/update category information
        for category_label in categories_list:
            if not category_label in self.trait_categories:
                category_colour = self.categories_info[category_label][self.colour_key]
                category_parent = self.categories_info[category_label][self.parent_key]
                # Update the trait category, if needed
                try:
                    category = TraitCategory.objects.get(label=category_label)
                    cat_has_changed = 0
                    if (category_colour != category.colour):
                        category.colour = category_colour
                        cat_has_changed = 1
                    if (category_parent != category.parent):
                        category.parent = category_parent
                        cat_has_changed = 1

                    if cat_has_changed == 1:
                        category.save()
                except:
                    category = TraitCategory.objects.create(label=category_label,colour=category_colour,parent=category_parent)
                    category.save()
                self.trait_categories.add(category_label)

            self.efo_traits_with_category.add(trait_id)
            if not category_label in self.efo_categories_by_cat.keys():
                self.efo_categories_by_cat[category_label] = set()
            self.efo_categories_by_cat[category_label].add(trait_id)


    def update_efo_category_info(self):
        ''' Update the EFO/TraitCategory relations, using the built up dictionary "efo_categories_by_cat" '''
        # Get all the EFOTrait IDs
        # efo_trait_ids = [ x.id for x in EFOTrait.objects.only('id').all() ]
        efo_trait_ids = EFOTrait.objects.values_list('id', flat=True)
        category_labels = self.efo_categories_by_cat.keys()
        total_cat = len(category_labels)
        count = 1
        for category_label in category_labels:
            print(f' -> Category {category_label} ({count}/{total_cat})')
            count += 1
            category_has_changed = 0
            trait_category = TraitCategory.objects.prefetch_related('efotraits','efotraits_ontology').get(label=category_label)
            if trait_category:
                # List of EFOtraits currently associated with the trait category in the database
                trait_category_efo_traits = trait_category.efotraits.all()

                # Loop over the EFO IDs associated with the current trait category
                for efo_trait_id in list(self.efo_categories_by_cat[category_label]):
                    # Creates TraitCategory association for each EFOTrait
                    if efo_trait_id not in trait_category_efo_traits and efo_trait_id in efo_trait_ids:
                        trait_category.efotraits.add(efo_trait_id)
                        category_has_changed = 1

                    # Creates TraitCategory association for EFOTrait_Ontology
                    if efo_trait_id not in trait_category.efotraits_ontology.all():
                        trait_category.efotraits_ontology.add(efo_trait_id)
                        category_has_changed = 1

                if category_has_changed == 1:
                    trait_category.save()
            else:
                print("ERROR: Can't retrieve the category '"+category_label+"'!")


    def launch_efo_updates(self):
        ''' Method to run the full EFOTrait/EFOTrait_Ontology/TraitCategory update'''

        print("> Truncate EFOTrait_Ontology table")
        EFOTrait_Ontology.objects.all().delete()

        print("> Truncate TraitCategory table")
        TraitCategory.objects.all().delete()

        print("> Update EFOTrait data and copy to EFOTrait_Ontology")
        efotraits = EFOTrait.objects.prefetch_related('associated_scores').all()
        for trait in efotraits:
            # Update EFOTrait
            self.update_efo_info(trait)
            # Copy to EFOTrait_Ontology
            self.add_efo_trait_to_efotrait_ontology(trait)

        print("> Add EFOTrait parent data to EFOTrait_Ontology + collect Trait Categories")
        for trait in efotraits:
            self.add_efo_parents_to_efotrait_ontology(trait)
        print(f'>>> Categories collected for {len(self.efo_traits_with_category)} traits')

        # Update parent entries
        efotrait_ontology_list = EFOTrait_Ontology.objects.prefetch_related('child_traits','scores_direct_associations','scores_child_associations').all()
        self.total_entries = str(len(efotrait_ontology_list))
        print("> Update EFOTrait_Ontology data ("+self.total_entries+" entries):")
        for ontology_trait in efotrait_ontology_list:
            # Update parent/child relation
            self.update_parent_child(ontology_trait)
            # Fetch trait category
            self.collect_efo_category_info(ontology_trait)

        # Update Trait category associations
        print('\n> Start updating Trait category associations in the database')
        self.update_efo_category_info()

        if self.warnings:
            print("##### Warnings #####")
            for warning in self.warnings:
                print(f'- {warning}')

        print('\n> End of script')


def run():
    ''' Update the EFO entries and add/update the Trait categories (from GWAS Catalog).'''

    efo_update = UpdateEFO()
    efo_update.launch_efo_updates()
