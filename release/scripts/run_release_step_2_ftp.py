import sys, os.path, shutil, glob
from datetime import datetime, date
import tarfile
from release.scripts.RemoveDataForRelease import *
from release.scripts.GenerateBulkExport import PGSExportAllMetadata
from release.scripts.PGSExport import PGSExport
from release.scripts.PGSBuildFtp import PGSBuildFtp
from release.scripts.UpdateEFO import *
from catalog.models import *

def run(*args):
    if (len(args) == 0):
        print("ERROR: missing argument providing the path to the export directory")
        print("Please use the command line with: --script-args <path_to_the_export_directory>")
        exit()

    previous_release_date = get_previous_release_date()

    # Remove non released data
    #call_remove_non_released_data(previous_release_date)

    # Remove non released data
    #call_remove_history_data()

    debug = 0
    scores_db = Score.objects.all().order_by('num')
    new_ftp_dir = '{}/../new_ftp_content/'.format(args[0])

    today = datetime.date.today()
    archive_file_name = '{}/../pgs_ftp_{}.tar.gz'.format(args[0],today)

    # Generate all PGS metadata files
    call_generate_all_metadata_exports(args[0])

    # Generate PGS studies metadata files
    call_generate_studies_metadata_exports(args[0],scores_db,debug)

    # Build FTP structure for scoring files
    #build_score_ftp(args[0],new_ftp_dir,scores_db,previous_release_date,debug)

    # Build FTP structure for metadata files
    build_metadata_ftp(args[0],new_ftp_dir,scores_db,previous_release_date,debug)

    # Build FTP structure for the bulk metadata files
    build_bulk_metadata_ftp(args[0],new_ftp_dir,previous_release_date,debug)


    # Generates the compressed archive to be copied to the EBI Private FTP
    tardir(new_ftp_dir, archive_file_name)

#-----------#
#  Methods  #
#-----------#

def call_remove_non_released_data(lastest_release):
    """ Remove non released data """

    # Release
    release_date = datetime.today().strftime('%Y-%m-%d')

    # Create object to remove the non released data
    data2remove = NonReleasedDataToRemove()

    # Entries to delete
    data2remove.list_entries_to_delete()

    # Delete selected entries
    #data2remove.delete_entries()

    print("Latest release: "+lastest_release)
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

    csv_prefix = datadir+'pgs_all'

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


def call_generate_studies_metadata_exports(dirpath,scores,debug):
    """ Generate metadata export files for each released studies """

    if debug:
        pgs_ids_list = []
        for i in range(1,debug+1):
            num = i < 10 and '0'+str(i) or str(i)
            pgs_ids_list.append('PGS0000'+num)
    else:
        pgs_ids_list = [  x.id for x in scores ]


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
        pgs_export.set_pgs_list([pgs_id])

        # Build the spreadsheets
        pgs_export.generate_sheets(csv_prefix)

        # Close the Pandas Excel writer and output the Excel file.
        pgs_export.save()

        # Generate a tar file of the study data
        pgs_export.generate_tarfile(dirpath+pgs_id+"_metadata.tar.gz",study_dir)



def build_score_ftp(dirpath,dirpath_new,scores,previous_release,debug):

    temp_data_dir = dirpath+'/scores/'
    temp_ftp_dir  = dirpath_new+'/scores/'

    # Prepare the temporary FTP directory to copy/download all the PGS Scores
    create_pgs_directory(dirpath_new)
    create_pgs_directory(temp_ftp_dir)

    # 1 - Add scoring data for each PGS Score
    for score in scores:
        pgs_id = score.id

        # For test only
        if debug and score.num == debug:
            break

        extension = str('.txt.gz')
        pgs_ftp = PGSBuildFtp(pgs_id, extension, 'score')

        score_file = pgs_id+pgs_ftp.file_extension

        if not os.path.exists(temp_data_dir+score_file):
            print("Data file '"+score_file+"' is missing in the directory '"+temp_data_dir+"'")
            exit()

        # Build temporary FTP structure for the PGS Score
        scoring_main_dir = temp_ftp_dir+pgs_id
        create_pgs_directory(scoring_main_dir)
        scoring_file_dir = scoring_main_dir+'/ScoringFiles/'
        create_pgs_directory(scoring_file_dir)

        # 2 - Compare scoring files
        new_file_md5_checksum = pgs_ftp.get_md5_checksum(temp_data_dir+score_file)
        ftp_file_md5_checksum = pgs_ftp.get_ftp_data_md5()

        # 2 a) - New published Score (PGS directory doesn't exist)
        if not ftp_file_md5_checksum:
            shutil.copy2(temp_data_dir+score_file, scoring_file_dir+score_file)
        # 2 b) - PGS directory exist (Updated Score)
        elif new_file_md5_checksum != ftp_file_md5_checksum:
            scoring_archives = scoring_file_dir+'archived_versions/'
            scoring_archives_file = scoring_archives+pgs_id+'_'+previous_release+'.txt.gz'
            create_pgs_directory(scoring_archives)

            pgs_ftp.get_ftp_file(scoring_archives_file)
            shutil.copy2(temp_data_dir+score_file, scoring_file_dir+score_file)
        ##### Extra for the first push #####
        else:
            shutil.copy2(temp_data_dir+score_file, scoring_file_dir+score_file)


def build_metadata_ftp(dirpath,dirpath_new,scores,previous_release,debug):

    temp_data_dir = dirpath
    temp_ftp_dir  = dirpath_new+'/scores/'

    # Prepare the temporary FTP directory to copy/download all the PGS Scores
    create_pgs_directory(dirpath_new)
    create_pgs_directory(temp_ftp_dir)

    # 1 - Add metadata for each PGS Score
    for score in scores:
        pgs_id = score.id

        # For test only
        if debug and score.num == debug:
            break

        pgs_ftp = PGSBuildFtp(pgs_id, '_metadata.xlsx', 'metadata')

        meta_file_tar = pgs_id+'_metadata.tar.gz'
        meta_file_xls = pgs_id+pgs_ftp.file_extension

        # Build temporary FTP structure for the PGS Metadata
        pgs_main_dir = temp_ftp_dir+pgs_id
        create_pgs_directory(pgs_main_dir)
        meta_file_dir = pgs_main_dir+'/Metadata/'
        create_pgs_directory(meta_file_dir)

        temp_meta_dir = temp_data_dir+"/"+pgs_ftp.pgs_id+"/Metadata/"

        # 2 - Compare metadata files
        new_file_md5_checksum = pgs_ftp.get_md5_checksum(temp_meta_dir+meta_file_xls)
        ftp_file_md5_checksum = pgs_ftp.get_ftp_data_md5()

        # 2 a) - New published Score (PGS directory doesn't exist)
        if not ftp_file_md5_checksum:
            # Copy new files
            shutil.copy2(temp_meta_dir+meta_file_xls, meta_file_dir+meta_file_xls)
            shutil.copy2(temp_data_dir+meta_file_tar, meta_file_dir+meta_file_tar)
            for file in glob.glob(temp_meta_dir+'*.csv'):
                csv_filepath = file.split('/')
                filename = csv_filepath[-1]
                shutil.copy2(file, meta_file_dir+filename)

        # 2 b) - PGS directory exist (Updated Metadata)
        elif new_file_md5_checksum != ftp_file_md5_checksum:
            # Archiving metadata from previous release
            meta_archives = meta_file_dir+'archived_versions/'
            create_pgs_directory(meta_archives)
            meta_archives_file = meta_archives+pgs_id+'_metadata_'+previous_release+'.tar.gz'
            # Fetch and Copy tar file to the archive
            pgs_ftp.get_ftp_file(meta_archives_file)
            shutil.copy2(temp_data_dir+meta_file_tar, meta_file_dir+meta_file_tar)

            # Copy new files
            shutil.copy2(temp_meta_dir+meta_file_xls, meta_file_dir+meta_file_xls)
            shutil.copy2(temp_data_dir+meta_file_tar, meta_file_dir+meta_file_tar)
            for file in glob.glob(temp_meta_dir+'*.csv'):
                csv_filepath = file.split('/')
                filename = csv_filepath[-1]
                shutil.copy2(file, meta_file_dir+filename)


def build_bulk_metadata_ftp(dirpath,dirpath_new,previous_release,debug):

    temp_data_dir = dirpath
    temp_ftp_dir = dirpath_new+'/metadata/'

    # Prepare the temporary FTP directory to copy/download all the PGS Scores
    create_pgs_directory(dirpath_new)
    create_pgs_directory(temp_ftp_dir)

    pgs_ftp = PGSBuildFtp('all', '', 'metadata')

    meta_file = pgs_ftp.all_meta_file
    meta_file_xls = meta_file.replace('.tar.gz', '.xlsx')

    # Copy new metadata
    shutil.copy2(temp_data_dir+meta_file, temp_ftp_dir+meta_file)
    shutil.copy2(temp_data_dir+'all_metadata/'+meta_file_xls, temp_ftp_dir+meta_file_xls)

    for file in glob.glob(temp_data_dir+'all_metadata/*.csv'):
        csv_filepath = file.split('/')
        filename = csv_filepath[-1]
        shutil.copy2(file, temp_ftp_dir+filename)

    # Archiving metadata from previous release
    meta_archives_file = meta_file.replace('.tar.gz', '_'+previous_release+'.tar.gz')

    meta_archives_dir = temp_ftp_dir+'previous_releases/'
    create_pgs_directory(meta_archives_dir)

    previous_release_date = previous_release.split('-')
    meta_year_archives_dir = meta_archives_dir+previous_release_date[0]+'/'
    create_pgs_directory(meta_year_archives_dir)

    pgs_ftp.get_ftp_file(meta_year_archives_dir+meta_archives_file)


def get_previous_release_date():
    releases = Release.objects.all().order_by('-date')
    return str(releases[1].date)


def create_pgs_directory(path):
    if not os.path.isdir(path):
        try:
            os.mkdir(path, 0o755)
        except OSError:
            print ("Creation of the directory %s failed" % path)
            exit()


def tardir(path, tar_name):
    with tarfile.open(tar_name, "w:gz") as tar_handle:
        for root, dirs, files in os.walk(path):
            for file in files:
                tar_handle.add(os.path.join(root, file))
