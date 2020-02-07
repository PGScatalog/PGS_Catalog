import requests
from catalog.models import EFOTrait, TraitCategory

def update_efo_info(trait):
    """ Fetch EFO information from an EFO ID, using the OLS REST API """
    trait_id = trait.id
    response = requests.get('https://www.ebi.ac.uk/ols/api/ontologies/efo/terms?obo_id=%s'%trait_id.replace('_', ':'))
    response = response.json()['_embedded']['terms']
    if len(response) == 1:
        response = response[0]
        new_label = response['label']

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

        trait_has_changed = 0
        if new_label != trait.label:
            #print("\tnew label '"+new_label+"'")
            trait_has_changed = 1
            trait.label = new_label
        if new_desc != trait.description:
            #print("\tnew desc '"+', '.join(new_desc)+"'")
            trait_has_changed = 1
            trait.description = new_desc
        if trait_has_changed == 1:
            trait.save()


def update_efo_category_info(trait):
    """ Fetch the trait category from an EFO ID, using the GWAS REST API """
    trait_id = trait.id
    response = requests.get('https://www.ebi.ac.uk/gwas/rest/api/parentMapping/%s'%trait_id)
    response_json = response.json()
    if response_json and response_json['trait'] != 'None':
        label  = response_json['colourLabel']
        colour = response_json['colour']
        parent = response_json['parent']
        #print("\tparent: "+response_json['parent'])
        #print("\tcolourLabel: "+response_json['colourLabel'])
        #print("\tcolour: "+response_json['colour'])

        categories = TraitCategory.objects.filter(label=label)
        # Update the trat category, if needed
        if len(categories) > 0:
            category = categories[0]
            cat_has_changed = 0
            if (colour != category.colour):
                category.colour = colour
                cat_has_changed = 1
            if (parent != category.parent):
                category.parent = parent
                cat_has_changed = 1
            if (trait not in category.efotraits.all()):
                category.efotraits.add(trait)
                cat_has_changed = 1

            if cat_has_changed == 1:
                category.save()
        # Create a new trait category and add the trait
        else:
            category = TraitCategory.objects.create(label=label,colour=colour,parent=parent)
            category.efotraits.add(trait)
            category.save()


def run():
    """ Update the EFO entries and add/update the Trait categories (from GWAS Catalog)."""
    for trait in EFOTrait.objects.all():
        #trait_id = trait.id
        #trait_label = trait.label
        #trait_desc = trait.description
        #print("# "+trait_id+" | "+trait_label)

        update_efo_info(trait)
        update_efo_category_info(trait)
