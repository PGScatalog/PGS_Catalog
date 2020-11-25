import requests
from catalog.models import EFOTrait, TraitCategory, EFOTrait_Ontology, Score
from release.scripts.GWASMapping import GWASMapping

class UpdateEFO:

    #---------------#
    # Configuration #
    #---------------#

    parent_key = 'parent'
    child_key = 'children'
    direct_pgs_ids_key = 'direct_pgs_ids'
    child_pgs_ids_key = 'child_pgs_ids'
    items_separator = ' | '
    exclude_terms = [
        'biological process',
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
        'process',
        'quality',
        'Thing'
    ]
    exclude_categories = [
        'Other disease',
        'Other measurement',
        'Other trait'
    ]
    pgs_specific_categories = {
        'Sex-specific PGS': { 'colour':'#00adb5', 'parent':'sex_specific_pgs' }
    }
    pgs_specific_traits = {
        'sex'   : 'Sex-specific PGS',
        'male'  : 'Sex-specific PGS',
        'female': 'Sex-specific PGS'
    }
    force_gwas_rest_api = ['EFO_0000319','EFO_0000405','EFO_0000540','EFO_0004298','EFO_0004324','EFO_0004503','EFO_0004872','EFO_0005105']


    def __init__(self):
        self.ontology_data = {}
        self.efo_categories = {}
        self.entry_count = 0
        self.total_entries = 0
        self.gwas_mapping = GWASMapping()
        self.gwas_mapping.get_gwas_mapping()
        # For debugging
        self.gwas_rest_count = 0
        self.warnings = []


    def format_data(self, response):
        """ Format some of the data to match the format in the database. """
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
            new_desc = response['description']
        data['description'] = new_desc

        return data


    def update_efo_info(self, trait):
        """ Fetch EFO information from an EFO ID, using the OLS REST API """
        trait_id = trait.id
        response = requests.get('https://www.ebi.ac.uk/ols/api/ontologies/efo/terms?obo_id=%s'%trait_id.replace('_', ':'))
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
        """ Import the entries in the EFOTrait table into EFOTrait_Ontology. """
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
        """ Fetch EFO information from an EFO ID, using the OLS REST API and
        import it into the EFOTrait_Ontology table. """
        trait_id = trait.id
        score_ids = trait.associated_pgs_ids
        ols_url = 'https://www.ebi.ac.uk/ols/api/ontologies/efo/ancestors?id={}'
        response = requests.get(ols_url.format(trait_id))
        response_json = response.json()

        try:
            ontology_trait = EFOTrait_Ontology.objects.get(id=trait_id)
        except EFOTrait_Ontology.DoesNotExist:
            print("No existing entries for the trait "+trait_id+"in the EFOTrait_Ontology model")
            exit(1)

        # Direct trait / PGS score associations
        if score_ids:
            if not trait_id in self.ontology_data:
                self.ontology_data[trait_id] = { self.direct_pgs_ids_key: set() }
            if not self.direct_pgs_ids_key in self.ontology_data[trait_id]:
                self.ontology_data[trait_id][self.direct_pgs_ids_key] = set()

            for score_id in score_ids:
                self.ontology_data[trait_id][self.direct_pgs_ids_key].add(score_id)

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
                    else:
                        self.add_parents(response, ontology_trait, score_ids)
            else:
                print("The script can't retrieve the parents of the trait '"+trait.label+"' ("+trait_id+"): the API returned "+str(len(response))+" results.")
        else:
            print("  >> WARNING: Can't find parents for the trait '"+trait_id+"'.")


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
        """ Build the parent/child relations before updating the EFOTrait_Ontology model"""
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


    def collect_efo_category_info(self, trait):
        """ Fetch the trait category from an EFO ID, using the GWAS REST API """
        trait_id = trait.id
        trait_label = trait.label
        category = None
        category_label = None
        category_colour = None
        category_parent = None

        # Fetch category information
        # PGS-specific category
        if trait_label in self.pgs_specific_traits.keys():
            category_label = self.pgs_specific_traits[trait_label]
            category_colour = self.pgs_specific_categories[category_label]['colour']
            category_parent = self.pgs_specific_categories[category_label]['parent']
        # GWAS category from file
        elif trait_id in self.gwas_mapping.trait_mapping and not trait_id in self.force_gwas_rest_api:
            category_label = self.gwas_mapping.trait_mapping[trait_id]
            category_colour = self.gwas_mapping.categories[category_label]['colour']
            category_parent = self.gwas_mapping.categories[category_label]['parent']
        # GWAS category not in file
        else:
            # For debugging
            print(">>>> Category fetch from REST - "+trait_id)
            self.gwas_rest_count += 1

            rest_url = f'https://www.ebi.ac.uk/gwas/rest/api/parentMapping/{trait_id}'
            try:
                # First try
                response = requests.get(rest_url)
                response_json = response.json()
            except JSONDecodeError:
                # Second try
                response = requests.get(rest_url)
                response_json = response.json()

            if response_json and response_json['trait'] != 'None':
                category_label  = response_json['colourLabel']
                category_colour = response_json['colour']
                category_parent = response_json['parent']


        # Add/update category information
        if category_label:
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

            self.efo_categories[trait.id] = set()
            self.efo_categories[trait.id].add(category.label)


    def update_efo_category_info(self, trait):
        """ Update the EFO/TraitCategory relation, using the parents trait category """
        try:
            efo_trait = EFOTrait.objects.get(id=trait.id)
        except EFOTrait.DoesNotExist:
            efo_trait = None

        parent_traits = trait.parent_traits.all()
        if parent_traits:
            # Add categories from parents (to support multi parent terms for categories)
            for efo_parent in parent_traits:
                if efo_parent.id in self.efo_categories:
                    parent_categories = list(self.efo_categories[efo_parent.id])
                    if parent_categories:
                        for parent_category in parent_categories:
                            self.efo_categories[trait.id].add(parent_category)
                else:
                    print("MISSING CATEGORY FOR THE PARENT TRAIT '"+efo_parent.id+"' (of "+trait.id+")")

            # Cleanup the list of categories
            if len(list(self.efo_categories[trait.id])) > 1:
                categories = list(self.efo_categories[trait.id])
                for category in categories:
                    if category in self.exclude_categories:
                        self.efo_categories[trait.id].remove(category)
                # Case when all the categories are in the "self.exclude_categories" list
                if len(list(self.efo_categories[trait.id])) == 0:
                    self.efo_categories[trait.id] = categories

        # Update category associations
        category_labels = list(self.efo_categories[trait.id])

        for category_label in category_labels:
            category_has_changed = 0
            trait_category = TraitCategory.objects.prefetch_related('efotraits','efotraits_ontology').get(label=category_label)
            if trait_category:
                # Creates TraitCategory association for EFOTrait
                if efo_trait:
                    if (efo_trait not in trait_category.efotraits.all()):
                        trait_category.efotraits.add(efo_trait)
                        category_has_changed = 1

                # Creates TraitCategory association for EFOTrait_Ontology
                if (trait not in trait_category.efotraits_ontology.all()):
                    trait_category.efotraits_ontology.add(trait)
                    category_has_changed = 1

                if category_has_changed == 1:
                    trait_category.save()
            else:
                print("ERROR: Can't retrieve the category '"+category_label+"'!")


    def launch_efo_updates(self):
        """ Method to run the full EFOTrait/EFOTrait_Ontology/TraitCategory update"""

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

        print("> Add EFOTrait parent data to EFOTrait_Ontology")
        for trait in efotraits:
            self.add_efo_parents_to_efotrait_ontology(trait)

        # Update parent entries
        efotrait_ontology_list = EFOTrait_Ontology.objects.prefetch_related('child_traits','scores_direct_associations','scores_child_associations').all()
        self.total_entries = str(len(efotrait_ontology_list))
        print("> Update EFOTrait_Ontology data ("+self.total_entries+" entries):")
        for ontology_trait in efotrait_ontology_list:
            # Update parent/child relation
            self.update_parent_child(ontology_trait)
            # Fetch trait category
            self.collect_efo_category_info(ontology_trait)

        # For debugging
        print("COUNT GWAS REST CALLS: "+str(self.gwas_rest_count))

        # Update Trait categories
        print("> Update Trait category associations for EFOTrait and EFOTrait_Ontology:")
        for ontology_trait in EFOTrait_Ontology.objects.prefetch_related('parent_traits').all():
            self.update_efo_category_info(ontology_trait)

        if self.warnings:
            print("##### Warnings #####")
            for warning in self.warnings:
                print(f'- {warning}')

def run():
    """ Update the EFO entries and add/update the Trait categories (from GWAS Catalog)."""

    efo_update = UpdateEFO()
    efo_update.launch_efo_updates()
