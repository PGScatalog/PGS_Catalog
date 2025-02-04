from django.db import transaction
from catalog.models import EFOTrait_Ontology, Score, Release


class OnlyUpdateEFOAssociations:
    """This class updates the EFO trait associations of the given scores without rebuilding
    the whole EFO ontology as UpdateEFO does. This might be useful when one or several
    EFO traits went obsolete, although we don't want to reflect this change yet in the PGS Catalog."""

    def get_current_release_scores(self):
        """Retrieve the scores of the ongoing release, assuming this process is executed
        as part of the release post-processing."""
        latest_release = Release.objects.latest('date')
        return Score.objects.filter(date_released=latest_release.date)

    def add_score_efo_trait_associations(self, score):
        """Add EFO trait associations to the given score."""
        efo_traits = score.trait_efo.all()
        for efo_trait in efo_traits:
            try:
                efo_trait_ontology = EFOTrait_Ontology.objects.get(id=efo_trait.id)
                efo_trait_ontology.scores_direct_associations.add(score)
                efo_trait_ontology.save()
                for efo_trait_parent in efo_trait_ontology.parent_traits.all():
                    efo_trait_parent.scores_child_associations.add(score)
                    efo_trait_parent.save()
            except EFOTrait_Ontology.DoesNotExist as e:
                print(f'ERROR: {efo_trait.id} is a new trait, UpdateEFO cannot be bypassed.')
                raise e

    def add_efo_trait_associations(self):
        """Main function."""
        latest_scores = self.get_current_release_scores()
        with transaction.atomic():
            try:
                for score in latest_scores:
                    self.add_score_efo_trait_associations(score)
            except Exception as e:
                transaction.rollback()
                raise e


def run():
    only_update_efo_associations = OnlyUpdateEFOAssociations()
    only_update_efo_associations.add_efo_trait_associations()