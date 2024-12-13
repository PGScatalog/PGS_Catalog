import datetime
import re
from catalog.models import *
from datetime import date, timedelta
from ftplib import FTP
from typing import Self


class CreateRelease:

    ftp_url  = 'ftp.ebi.ac.uk'
    ftp_path = 'pub/databases/spot/pgs/scores'

    new_scores = {}
    new_performances = {}
    new_traits = set()

    def __init__(self, release_date=date.today()):
        self.release_date = release_date
        self.new_publications = Publication.objects.filter(date_released__isnull=True, curation_status="C")

    @classmethod
    def tomorrow(cls) -> Self:
        return cls.on(date.today() + timedelta(days=1))

    @classmethod
    def on(cls, release_date: datetime.date) -> Self:
        return cls(release_date=release_date)

    def get_release_date(self):
        return self.release_date

    def update_data_to_release(self):
        """
        Update data ready for the release (scores, performances and publications)
        by adding a date in the 'date_released' columns
        """
        release_date = self.get_release_date()
        previous_traits = set(Score.objects.values_list('trait_efo__id', flat=True).exclude(date_released__isnull=True).distinct())
        #### Add release date for each publication and dependent models ####
        for publication in self.new_publications:
            publication.date_released = release_date
            publication.save()

            # Scores
            scores_list = Score.objects.filter(date_released__isnull=True, publication=publication)
            for score in scores_list:
                self.new_scores[score.id] = 1
                # Update date_release
                score.date_released = release_date
                score.save()
                # Get new traits
                score_traits = {efotrait.id for efotrait in score.trait_efo.all()}
                self.new_traits.update(score_traits.difference(previous_traits))

            # Performances
            performances_list = Performance.objects.filter(date_released__isnull=True, publication=publication)
            for performance in performances_list:
                self.new_performances[performance.id] = 1
                # Update date_release
                performance.date_released = release_date
                performance.save()

    def create_new_release(self):
        """ Create new release instance and save it in the database """
        #### Create new release instance ####
        release_notes = 'This release contains {} new Score(s), {} new Publication(s), {} new Performance metric(s) and {} new Trait(s)'.format(len(self.new_scores.keys()), len(self.new_publications), len(self.new_performances.keys()), len(self.new_traits))
        release = Release.objects.create(
                date=self.get_release_date(),
                performance_count=len(self.new_performances.keys()),
                publication_count=len(self.new_publications),
                score_count=len(self.new_scores.keys()),
                efotrait_count=len(self.new_traits),
                notes=release_notes
              )
        return release

    def check_ftp(self):
        """ Check that all the PGSs have a corresponding Scoring file in the PGS FTP. """
        files_list = []
        pgs_ftp_list_missing = []

        # Get the list of released PGS IDs
        for score in Score.objects.exclude(date_released__isnull=True):
            pgs_id = score.id

            path = self.ftp_path+'/'+pgs_id+'/ScoringFiles/'

            ftp = FTP(self.ftp_url)     # connect to host, default port
            ftp.login()                 # user anonymous, passwd anonymous@
            ftp.cwd(path)               # change into "debian" directory

            files_list = []
            file_found = 0

            # Get the list of PGS files on FTP and extract the PGS IDs
            ftp.retrlines('LIST', lambda x: files_list.append(x.split()))
            for file_info in files_list:
                file_name = file_info[-1]

                pgs_re = re.compile('(PGS0+\d+)\D+')
                file_match = pgs_re.match(file_name)
                if (file_match and file_match[1]):
                    file_found = 1
            if not file_found:
                pgs_ftp_list_missing.append(pgs_id)

        if len(pgs_ftp_list_missing) != 0:
            if (len(pgs_ftp_list_missing) == 1):
                print("Scoring file missing on the FTP for "+pgs_ftp_list_missing[0])
            else:
                print("There are "+str(len(pgs_ftp_list_missing))+" missing scoring files on the FTP")
                for id in pgs_ftp_list_missing:
                    print("- "+pgs_id)


################################################################################

def parse_arguments(args):
    """Parse runscript --script-args arguments and return them as a dictionary
    Must be a list of key=value pairs.
    eg: python manage.py runscript CreateRelease --script-args date=2024-12-25"""
    try:
        return dict(map(lambda s: s.split('='), args))
    except ValueError:
        raise Exception("Invalid arguments: must be key=value pairs")


def create_new_release_from_args(args) -> CreateRelease:
    """Parse the runscript arguments for the CreateRelease command.
    Expected argument: date=<iso-format-date YYYY-MM-DD>, to choose a particular date for the release.
    If no argument is given, the release will be planned for tomorrow."""
    parsed_args = parse_arguments(args)

    if 'date' in parsed_args:
        release = CreateRelease.on(date.fromisoformat(parsed_args['date']))
    else:
        release = CreateRelease.tomorrow()
    release.update_data_to_release()
    return release


def run(*args):

    latest_release = Release.objects.latest('date').date
    release = create_new_release_from_args(args)
    new_release = release.create_new_release()

    # Just a bunch of prints
    print("Latest release: "+str(latest_release))
    print("New release: "+str(new_release.date))
    print("Number of new Scores: "+str(new_release.score_count))
    print(', '.join(release.new_scores.keys()))
    print("Number of new Publications: "+str(new_release.publication_count))
    print("Number of new Performances: "+str(new_release.performance_count))
    print("Number of new Traits: " + str(new_release.efotrait_count))

    # Scores
    scores_direct = Score.objects.filter(date_released__isnull=True)

    # Performances
    perfs_direct = Performance.objects.filter(date_released__isnull=True)

    print("Number of new Scores (direct fetch): "+str(scores_direct.count()))
    print("Number of new Performances (direct fetch): "+str(perfs_direct.count()))
