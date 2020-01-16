import re
from catalog.models import *
from datetime import datetime
from ftplib import FTP


def check_ftp():
    """ Check that all the PGSs have a corresponding Scoring file in the PGS FTP. """
    files_list = []
    pgs_ftp_list = []

    ftp = FTP('ftp.ebi.ac.uk')     # connect to host, default port
    ftp.login()                     # user anonymous, passwd anonymous@
    ftp.cwd('pub/databases/spot/pgs/ScoringFiles_formatted')               # change into "debian" directory

    # Get the list of PGS files on FTP and extract the PGS IDs
    ftp.retrlines('LIST', lambda x: files_list.append(x.split()))
    for file_info in files_list:
        file_name = file_info[-1]

        pgs_re = re.compile('(PGS0+\d+)\D+')
        file_match = pgs_re.match(file_name)
        if (file_match and file_match[1]):
            pgs_ftp_list.append(file_match[1])
            print("FTP: "+file_match[1])

    # Get the list of released PGS IDs
    for score in Score.objects.exclude(date_released__isnull=True):
        pgs_id = score.id
        if (pgs_id not in pgs_ftp_list):
            print("Scoring file missing on the FTP for "+pgs_id)


def run():
    # Release
    lastest_release = Release.objects.latest('date')
    release_date = datetime.today().strftime('%Y-%m-%d')

    new_scores = {}
    new_perfs  = {}

    # Publications
    publications = Publication.objects.filter(date_released__isnull=True, curation_status="C")


    #### Add release date for each publications and dependent models ####
    for publication in publications:
        publication.date_released = release_date
        publication.save()

        # Scores
        scores_list = Score.objects.filter(date_released__isnull=True, publication=publication)
        for score in scores_list:
            new_scores[score.id] = 1
            # Update date_release
            score.date_released = release_date
            score.save()

        # Performances
        performances_list = Performance.objects.filter(date_released__isnull=True, publication=publication)
        for performance in performances_list:
            new_perfs[performance.id] = 1
            # Update date_release
            performance.date_released = release_date
            performance.save()


    print("Latest release: "+str(lastest_release.date))
    print("New release: "+str(release_date))
    print("Number of new Scores: "+str(len(new_scores.keys())))
    print(', '.join(new_scores.keys()))
    print("Number of new Publications: "+str(len(publications)))
    print("Number of new Performances: "+str(len(new_perfs.keys())))

    # Scores
    scores_direct = Score.objects.filter(date_released__isnull=True)

    # Performances
    perfs_direct = Performance.objects.filter(date_released__isnull=True)

    print("Number of new Scores (direct fetch): "+str(scores_direct.count()))
    print("Number of new Performances (direct fetch): "+str(perfs_direct.count()))

    check_ftp()
