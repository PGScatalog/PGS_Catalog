import sys, os.path
from datetime import datetime
from release.scripts.RemoveDataForRelease import *
from release.scripts.GenerateBulkExport import PGSExportAllMetadata
from release.scripts.PGSExport import PGSExport
from release.scripts.UpdateEFO import *
from catalog.models import *

def run(*args):
    if (len(args) == 0):
        print("ERROR: missing argument providing the path to the export directory")
        print("Please use the command line with: --script-args <path_to_the_export_directory>")
        exit()

    # Remove non released data
    call_remove_non_released_data()

    # Remove non released data
    call_remove_history_data()

    # Generate all PGS metadata files
    call_generate_all_metadata_exports(args[0])

    # Generate PGS studies metadata files
    call_generate_studies_metadata_exports(args[0])




def call_remove_non_released_data():
    """ Remove non released data """

    # Release
    lastest_release = Release.objects.latest('date')
    release_date = datetime.today().strftime('%Y-%m-%d')

    # Create object to remove the non released data
    data2remove = NonReleasedDataToRemove()

    # Entries to delete
    data2remove.list_entries_to_delete()

    # Delete selected entries
    #data2remove.delete_entries()

    print("Latest release: "+str(lastest_release.date))
    print("New release: "+str(release_date))
    print("Number of non curated Publications: "+str(data2remove.publications.count()))
    print("Number of Scores to remove: "+str(len(data2remove.scores2del.keys())))
    print( ' - '+'\n - '.join(data2remove.scores2del.keys()))
    print("Number of Performances to remove : "+str(len(data2remove.perfs2del.keys())))
    print( ' - '+'\n - '.join(data2remove.perfs2del.keys()))
    print("Number of Sample Sets to remove: "+str(len(data2remove.pss2del.keys())))
    print( ' - '+'\n - '.join(data2remove.pss2del.keys()))


def call_remove_history_data():

    # Delete history records for the production database
    history2remove = RemoveHistory()
    history2remove.delete_history()
    

def call_generate_all_metadata_exports(dirpath):
    """ Generate all metadata export files """

    datadir = dirpath+"all_metadata/"
    filename = datadir+'pgs_all_metadata.xlsx'

    csv_prefix = datadir+'pgs'

    if not os.path.isdir(datadir):
        try:
            os.mkdir(datadir)
        except OSError:
            print ("Creation of the directory %s failed" % datadir)

    if not os.path.isdir(datadir):
        print("Can't create a directory for the metadata ("+datadir+")")
        exit(1)

    # Create export object
    pgs_export = PGSExportAllMetadata(filename)

    # Info/readme spreadsheet
    pgs_export.create_readme_spreadsheet()

    # Build the spreadsheets
    pgs_export.generate_sheets(csv_prefix)

    # Close the Pandas Excel writer and output the Excel file.
    pgs_export.save()

    # Create a md5 checksum for the spreadsheet
    pgs_export.create_md5_checksum()

    # Generate a tar file of the study data
    pgs_export.generate_tarfile(dirpath+"pgs_all_metadata.tar.gz",datadir)


def call_generate_studies_metadata_exports(dirpath):
    """ Generate metadata export files for each released studies """

    pgs_ids_list = ['PGS000001','PGS000002','PGS000018']
    #scores = scores_direct = Score.objects.filter(date_released__isnull=False)
    #pgs_ids_list = [  x.id for x in scores ]

    for pgs_id in pgs_ids_list:

        print("\n# PGS "+pgs_id)

        pgs_dir = dirpath+pgs_id
        study_dir = pgs_dir+"/Metadata/"
        csv_prefix = study_dir+pgs_id

        # Check / create PGS directory
        if not os.path.isdir(pgs_dir):
            try:
                os.mkdir(pgs_dir)
            except OSError:
                print ("Creation of the directory %s failed" % pgs_dir)

        # Check / create PGS metadata directory
        if os.path.isdir(pgs_dir) and not os.path.isdir(study_dir):
            try:
                os.mkdir(study_dir)
            except OSError:
                print ("Creation of the directory %s failed" % study_dir)

        if not os.path.isdir(study_dir):
            print("Can't create a directory for the study "+pgs_id)
            break

        #filename = 'study_download_example.xlsx'
        filename = study_dir+pgs_id+"_metadata.xlsx"

        # Create export object
        pgs_export = PGSExport(filename)

        # Build the spreadsheets
        pgs_export.generate_sheets(csv_prefix)

        # Close the Pandas Excel writer and output the Excel file.
        pgs_export.save()

        # Generate a tar file of the study data
        pgs_export.generate_tarfile(dirpath+pgs_id+"_metadata.tar.gz",study_dir)
