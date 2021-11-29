from catalog.models import Score, Performance, Publication, EvaluatedScore
from pgs_web import constants


class UpdateScoreEvaluated:

    publications_eval = {}

    def __init__(self,verbose=None):
        self.publications = Publication.objects.all().order_by('num')
        self.verbose = verbose

    def update_score_evaluated(self):

        # Delete all EvaluatedScore entries
        EvaluatedScore.objects.all().delete()

        # Populate the EvaluatedScore table
        for publication in self.publications:
            evaluated_scores = set()
            score_ids = {}
            internal_scores = publication.publication_score.all()
            internal_score_ids = [x.id for x in internal_scores]
            external_score_ids = set()
            pquery = publication.publication_performance.select_related('score','publication').all()
            for perf in pquery:
                score = perf.score
                score_id = score.id
                if not score_id in score_ids.keys():
                    score_ids[score_id] = score
                if not score_id in internal_score_ids:
                    external_score_ids.add(score_id)

            scores = sorted(score_ids.values(), key=lambda s: s.id)
            score_evaluated = EvaluatedScore(publication=publication)
            score_evaluated.save()
            score_evaluated.scores_evaluated.set(scores)
            score_evaluated.save()

            if score_ids.keys():
                print(f'> {publication.id}: {len(score_ids.keys())} scores evaluated | {len(external_score_ids)} external scores evaluated')

################################################################################

def run():

    score_evaluated = UpdateScoreEvaluated(verbose=True)
    score_evaluated.update_score_evaluated()
