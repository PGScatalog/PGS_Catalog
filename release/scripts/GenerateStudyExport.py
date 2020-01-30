import sys, os, shutil
import pandas as pd
import hashlib
from release.scripts.pgs_export import PGSExport
from catalog.models import *

#---------------------#
# Main running method #
#---------------------#

def run(*args):
    if (len(args) == 0):
        print("ERROR: missing argument providing the path to the export directory")
        print("Please use the command line with: --script-args <path_to_the_export_directory>")
        exit()

    dirpath = args[0] # e.g. '../../../datafiles/export/'

    my_list = ['PGS000001','PGS000002','PGS000018']

    for pgs_id in my_list:

        print("\n# PGS "+pgs_id)

        study_dir = dirpath+pgs_id+"_metadata/"

        csv_prefix = study_dir+pgs_id

        if not os.path.isdir(study_dir):
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
