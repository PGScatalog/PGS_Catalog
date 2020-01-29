import sys, os, shutil
import pandas as pd
import hashlib
from release.scripts.pgs_export import *
from catalog.models import *

#---------------------#
# Main running method #
#---------------------#

def run():

    # Example
    dirpath = '../../../datafiles/export/'

    my_list = ['PGS000001','PGS000002','PGS000018']

    for pgs_id in my_list:

        print("\n# PGS "+pgs_id)

        study_dir = dirpath+pgs_id+"_metadata/"

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

        pgs_export = PGSExport(filename)

        # Spreadsheets list and configuration
        spreadsheets = {
            'scores'     : ('Scores', pgs_export.create_scores_spreadsheet),
            'perf'       : ('Perfomance Metrics', pgs_export.create_performance_metrics_spreadsheet),
            'samplesets' : ('Evaluation Sample Sets', pgs_export.create_samplesets_spreadsheet),
            'samples_development': ('Score Development Samples', pgs_export.create_samples_development_spreadsheet),
            'publications': ('Publications', pgs_export.create_publications_spreadsheet),
            'efo_traits': ('EFO Traits', pgs_export.create_efo_traits_spreadsheet)
        }
        spreadsheets_ordering = ['publications', 'scores', 'samples_development', 'perf', 'samplesets', 'efo_traits']


        # Create a Pandas Excel writer using XlsxWriter as the engine.
        #writer = pd.ExcelWriter(filename, engine='xlsxwriter')

        if (len(spreadsheets.keys()) != len(spreadsheets_ordering)):
            print("\tSize discrepancies between the dictionary 'spreadsheets' and the list 'spreadsheets_ordering'.")
            exit()

        csv_prefix = study_dir+pgs_id

        # Generate the spreadsheets
        for spreadsheet_name in spreadsheets_ordering:
            spreadsheet_label = spreadsheets[spreadsheet_name][0]
            try:
                data = spreadsheets[spreadsheet_name][1]([pgs_id])
                pgs_export.generate_sheet(data, spreadsheet_label)
                print("\tSpreadsheet '"+spreadsheet_label+"' done")
                pgs_export.generate_csv(data, csv_prefix, spreadsheet_label)
                print("\tCSV '"+spreadsheet_label+"' done")
            except:
                print("\t/!\ Issue to generate the spreadsheet '"+spreadsheet_label+"': ",sys.exc_info()[0]," /!\ \n")
                raise

        # Close the Pandas Excel writer and output the Excel file.
        pgs_export.save()

        # Generate a tar file of the study data
        pgs_export.generate_tarfile(dirpath+pgs_id+"_metadata.tar.gz",study_dir)
