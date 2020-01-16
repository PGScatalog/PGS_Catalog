import sys
import pandas as pd
from release.scripts.pgs_export import *
from catalog.models import *


#---------------------#
# Spreadsheet methods #
#---------------------#

def create_readme_spreadsheet(excel_writer):
    """ Info/readme spreadsheet """

    readme_data = {}

    version_date = '2019-11-04'
    readme_data['PGS Catalog version'] = [version_date]
    readme_data['Number of Polygenic Scores'] = [Score.objects.all().count()]
    readme_data['Number of Traits'] = [EFOTrait.objects.all().count()]
    readme_data['Number of Publications'] = [Publication.objects.all().count()]

    df = pd.DataFrame(readme_data)
    df = df.transpose()
    df.to_excel(excel_writer, sheet_name="Readme", header=False)


#---------------------#
# Main running method #
#---------------------#

def run():
    dirpath = '../../../datafiles/export/'
    datadir = dirpath+"all_metadata/"
    filename = datadir+'pgs_all_metadata.xlsx'


    if not os.path.isdir(datadir):
        try:
            os.mkdir(datadir)
        except OSError:
            print ("Creation of the directory %s failed" % datadir)

    if not os.path.isdir(datadir):
        print("Can't create a directory for the metadata ("+datadir+")")
        exit(1)

    pgs_export = PGSExport(filename)

    # Spreadsheets list and configuration
    spreadsheets = {
        'scores'     : ('Scores', pgs_export.create_scores_spreadsheet),
        'perf'       : ('Perfomance Metrics', pgs_export.create_performance_metrics_spreadsheet),
        'samplesets' : ('Sample Sets', pgs_export.create_samplesets_spreadsheet),
        'sample_training': ('Sample Training', pgs_export.create_sample_training_spreadsheet),
        'sample_variants': ('Source of Variant Associations', pgs_export.create_sample_variants_spreadsheet),
        'publications': ('Publications', pgs_export.create_publications_spreadsheet),
        'efo_traits': ('EFO Traits', pgs_export.create_efo_traits_spreadsheet)
    }
    spreadsheets_ordering = ['scores', 'perf', 'samplesets', 'sample_training', 'sample_variants', 'publications', 'efo_traits']


    # Create a Pandas Excel writer using XlsxWriter as the engine.
    #writer = pd.ExcelWriter(filename, engine='xlsxwriter')

    # Info/readme spreadsheet
    create_readme_spreadsheet(pgs_export.writer)

    if (len(spreadsheets.keys()) != len(spreadsheets_ordering)):
        print("Size discrepancies between the dictionary 'spreadsheets' and the list 'spreadsheets_ordering'.")
        exit()

    csv_prefix = datadir+'pgs'

    # Generate the spreadsheets
    for spreadsheet_name in spreadsheets_ordering:
        spreadsheet_label = spreadsheets[spreadsheet_name][0]
        try:
            data = spreadsheets[spreadsheet_name][1]()
            pgs_export.generate_sheet(data, spreadsheet_label)
            print("Spreadsheet '"+spreadsheet_label+"' done")
            pgs_export.generate_csv(data, csv_prefix,spreadsheet_label)
            print("CSV '"+spreadsheet_label+"' done")
        except:
            print("Issue to generate the spreadsheet '"+spreadsheet_label+"'")

    # Close the Pandas Excel writer and output the Excel file.
    pgs_export.save()

    # Create a md5 checksum for the spreadsheet
    pgs_export.create_md5_checksum()

    # Generate a tar file of the study data
    pgs_export.generate_tarfile(dirpath+"pgs_all_metadata.tar.gz",datadir)
