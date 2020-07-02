import requests
from catalog.models import EFOTrait, TraitCategory, EFOTrait_Ontology, Score

# Global variables
ontology_data = {}
parent_key = 'parent'
child_key = 'children'
direct_pgs_ids_key = 'direct_pgs_ids'
child_pgs_ids_key = 'child_pgs_ids'
items_separator = ' | '
exclude_terms = ['disposition', 'quality', 'experimental factor', 'material property', 'Thing']
trait_model_type = 'ontology'


def format_data(response):
    """ Format some parts of data to match the format in the database. """
    data = {}
    # Synonyms
    new_synonyms_string = ''
    new_synonyms = response['synonyms']
    if (new_synonyms):
        new_synonyms_string = items_separator.join(new_synonyms)
    data['synonyms'] = new_synonyms_string

    # Mapped terms
    new_mapped_terms_string = ''
    if 'database_cross_reference' in response['annotation']:
        new_mapped_terms = response['annotation']['database_cross_reference']
        if (new_mapped_terms):
            new_mapped_terms_string = items_separator.join(new_mapped_terms)
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

def update_efo_info(trait):
    """ Fetch EFO information from an EFO ID, using the OLS REST API """
    trait_id = trait.id
    response = requests.get('https://www.ebi.ac.uk/ols/api/ontologies/efo/terms?obo_id=%s'%trait_id.replace('_', ':'))
    response = response.json()['_embedded']['terms']
    if len(response) == 1:
        response = response[0]
        new_label = response['label']

        # Synonyms, Mapped terms and description
        efo_formatted_data = format_data(response)

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


def add_efo_trait_to_efotrait_ontology(trait):
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


def add_efo_parents_to_efotrait_ontology(trait):
    """ Fetch EFO information from an EFO ID, using the OLS REST API and
    import it into the EFOTrait_Ontology table. """
    trait_id = trait.id
    score_ids = trait.associated_pgs_ids
    ols_url = 'https://www.ebi.ac.uk/ols/api/ontologies/efo/ancestors?id={}'
    response = requests.get(ols_url.format(trait_id))
    response_json = response.json()

    try:
        ontology_trait = EFOTrait_Ontology.objects.get(id=trait.id)
    except EFOTrait_Ontology.DoesNotExist:
        print("No existing entries for the trait "+trait.id+"in the EFOTrait_Ontology model")
        exit(1)

    # Direct trait / PGS score associations
    if score_ids:
        if not trait_id in ontology_data:
            ontology_data[trait_id] = { direct_pgs_ids_key: set() }
        if not direct_pgs_ids_key in ontology_data[trait_id]:
            ontology_data[trait_id][direct_pgs_ids_key] = set()

        for score_id in score_ids:
            ontology_data[trait_id][direct_pgs_ids_key].add(score_id)

    if '_embedded' in response_json:
        response = response_json['_embedded']['terms']
        # Fetch parent data and store it
        if len(response) > 0:
            for parent in response:
                parent_id = parent['short_form']
                parent_label = parent['label']
                if not parent_label in exclude_terms:
                    # Child relations
                    if parent_id in ontology_data:
                        if child_key in ontology_data[parent_id]:
                            ontology_data[parent_id][child_key].append(ontology_trait)
                        else:
                            ontology_data[parent_id][child_key] = [ontology_trait]
                    else:
                        ontology_data[parent_id] = { child_key: [ontology_trait] }

                    # Children trait / PGS score associations
                    if score_ids:
                        if not parent_id in ontology_data:
                            ontology_data[parent_id] = { child_pgs_ids_key: set() }
                        if not child_pgs_ids_key in ontology_data[parent_id]:
                            ontology_data[parent_id][child_pgs_ids_key] = set()

                        for score_id in score_ids:
                            ontology_data[parent_id][child_pgs_ids_key].add(score_id)

                    try:
                        parent_trait = EFOTrait_Ontology.objects.get(id=parent_id)
                    except EFOTrait_Ontology.DoesNotExist:
                        # Synonyms, Mapped terms and description
                        parent_formatted_data = format_data(parent)

                        EFOTrait_Ontology.objects.create(
                            id=parent_id,
                            label=parent_label,
                            description=parent_formatted_data['description'],
                            url=parent['iri'],
                            synonyms=parent_formatted_data['synonyms'],
                            mapped_terms=parent_formatted_data['mapped_terms']
                        )
                        parent_trait = EFOTrait_Ontology.objects.get(id=parent_id)

                    # Parent relations
                    child_id = ontology_trait.id
                    if child_id in ontology_data:
                        if parent_key in ontology_data[child_id]:
                            ontology_data[child_id][parent_key].append(parent_trait)
                        else:
                            ontology_data[child_id][parent_key] = [parent_trait]
                    else:
                        ontology_data[child_id] = { parent_key: [parent_trait] }
        else:
            print("The script can't retrieve the parents of the trait '"+trait.label+"' ("+trait_id+"): the API returned "+str(len(response))+" results.")
    else:
        print("  >> WARNING: Can't find parents for the trait '"+trait_id+"'.")


def update_efo_category_info(trait,type):
    """ Fetch the trait category from an EFO ID, using the GWAS REST API """
    trait_id = trait.id
    response = requests.get('https://www.ebi.ac.uk/gwas/rest/api/parentMapping/%s'%trait_id)
    response_json = response.json()
    if response_json and response_json['trait'] != 'None':
        label  = response_json['colourLabel']
        colour = response_json['colour']
        parent = response_json['parent']

        categories = TraitCategory.objects.filter(label=label)
        # Update the trait category, if needed
        if len(categories) > 0:
            category = categories[0]
            cat_has_changed = 0
            if (colour != category.colour):
                category.colour = colour
                cat_has_changed = 1
            if (parent != category.parent):
                category.parent = parent
                cat_has_changed = 1
            if type == trait_model_type:
                if (trait not in category.efotraits_ontology.all()):
                    category.efotraits_ontology.add(trait)
                    cat_has_changed = 1
            else:
                if (trait not in category.efotraits.all()):
                    category.efotraits.add(trait)
                    cat_has_changed = 1

            if cat_has_changed == 1:
                category.save()
        # Create a new trait category and add the trait
        else:
            category = TraitCategory.objects.create(label=label,colour=colour,parent=parent)
            if type == trait_model_type:
                category.efotraits_ontology.add(trait)
            else:
                category.efotraits.add(trait)
            category.save()


def run():
    """ Update the EFO entries and add/update the Trait categories (from GWAS Catalog)."""

    print("Truncate EFOTrait_Ontology table")
    EFOTrait_Ontology.objects.all().delete()

    print("Process EFOTrait data")
    for trait in EFOTrait.objects.all():

        # Update EFOTrait and update/import TraitCategory
        update_efo_info(trait)
        update_efo_category_info(trait,'')

        # Import EFOTrait_Ontology and update/import TraitCategory
        add_efo_trait_to_efotrait_ontology(trait)
        add_efo_parents_to_efotrait_ontology(trait)


    # Update parent entries
    total_entries = str(len(ontology_data.keys()))
    entry_count = 0
    print("# Update EFOTrait ontology data ("+total_entries+" entries):")
    for ontology_id in ontology_data:

        ontology_trait = EFOTrait_Ontology.objects.get(id=ontology_id)
        entry_count += 1
        # >>>>>>>>>>> PRINT <<<<<<<<<<<<<
        print("- "+ontology_id+" ("+ontology_trait.label+")"+" | "+str(entry_count)+'/'+total_entries)

        # Update with child EFOTrait(s)
        if child_key in ontology_data[ontology_id]:
            for efo_trait in ontology_data[ontology_id][child_key]:
                ontology_trait.child_traits.add(efo_trait)

        # Update with parent EFOTrait(s)
        if parent_key in ontology_data[ontology_id]:
            for efo_trait in ontology_data[ontology_id][parent_key]:
                ontology_trait.parent_traits.add(efo_trait)

        # Update with direct trait/PGS Score IDs associations
        if direct_pgs_ids_key in ontology_data[ontology_id]:
            pgs_ids = sorted(list(ontology_data[ontology_id][direct_pgs_ids_key]))
            pgs_scores = Score.objects.filter(id__in=pgs_ids).order_by('id')
            for pgs_score in pgs_scores:
                ontology_trait.scores_direct_associations.add(pgs_score)

        # Update with child trait/PGS Score IDs associations
        if child_pgs_ids_key in ontology_data[ontology_id]:
            child_pgs_ids = sorted(list(ontology_data[ontology_id][child_pgs_ids_key]))
            child_pgs_scores = Score.objects.filter(id__in=child_pgs_ids).order_by('id')
            for child_pgs_score in child_pgs_scores:
                ontology_trait.scores_child_associations.add(child_pgs_score)

        update_efo_category_info(ontology_trait,trait_model_type)

        ontology_trait.save()
