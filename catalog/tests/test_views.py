from django.test import TestCase
from catalog.views import *
from catalog.models import *
from datetime import datetime

class SimpleContentTest(TestCase):
    """ Test the simple content """

    def test_content(self):
        self.assertIsNotNone(performance_disclaimer())
        self.assertIsNotNone(score_disclaimer('test'))


class EFOTraitDataTest(TestCase):
    """ Test the fetch of the EFO traits data """
    def test_efo_traits_data(self):
        d_pub = datetime(2020,3,10)
        pub = Publication.objects.create(num=350,date_publication=d_pub,PMID=12340,journal='Nature')

        trait_1 = EFOTrait.objects.create(id='EFO_0000292',label='bladder carcinoma')
        trait_2 = EFOTrait.objects.create(id='EFO_0000305',label='breast carcinoma')
        trait_3 = EFOTrait.objects.create(id='EFO_0000378',label='coronary artery disease')
        trait_4 = EFOTrait.objects.create(id='EFO_0000000',label='Not defined')

        score_1 = Score.objects.create(num=950,publication=pub,variants_number=10,name='Score1')
        score_1.trait_efo.add(trait_1)
        score_2 = Score.objects.create(num=951,publication=pub,variants_number=10,name='Score2')
        score_2.trait_efo.add(trait_2)
        score_3 = Score.objects.create(num=952,publication=pub,variants_number=10,name='Score3')
        score_3.trait_efo.add(trait_3)

        cat_label_1 = 'Cancer'
        cat_colour_1 = '#BC80BD'
        cat_parent_1 = 'neoplasm'
        trait_cat_1 = TraitCategory.objects.create(label=cat_label_1,colour=cat_colour_1,parent=cat_parent_1)
        trait_cat_1.efotraits.add(trait_1)
        trait_cat_1.efotraits.add(trait_2)

        cat_label_2 = 'Cardiovascular disease'
        cat_colour_2 = '#B33232'
        cat_parent_2 = 'cardiovascular disease'
        trait_cat_2 = TraitCategory.objects.create(label=cat_label_2,colour=cat_colour_2,parent=cat_parent_2)
        trait_cat_2.efotraits.add(trait_3)

        # Trait and category not linked to a score
        cat_label_3 = 'Unknown'
        cat_colour_3 = '#000000'
        cat_parent_3 = 'unknown'
        trait_cat_3 = TraitCategory.objects.create(label=cat_label_3,colour=cat_colour_3,parent=cat_parent_3)
        trait_cat_3.efotraits.add(trait_4)

        data = get_efo_traits_data()
        self.assertEqual(len(data),2)
        self.assertTrue(len(data[0]) > 0)
        self.assertTrue(len(data[1]) > 0)
