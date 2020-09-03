import sys, os
import argparse
from os import path

class PGSFTPChecks:

    ftp_std_scoringfile_suffix = '.txt.gz'
    ftp_metadata_file_prefix = '_metadata'
    ftp_metadata_file_suffixes = {
        'tar': '.tar.gz',
        'excel': '.xlsx',
        'csv': [
            '_efo_traits.csv',
            '_evaluation_sample_sets.csv',
            '_performance_metrics.csv',
            '_publications.csv',
            '_score_development_samples.csv',
            '_scores.csv'
        ]
    }

    log_msg = {
        'missing_pgs_dir': [],
        'missing_score_dir': [],
        'missing_metadata_dir': [],
        'missing_std_scoring_file': [],
        'missing_harm_scoring_file': [],
        'missing_metadata_tar_file': [],
        'missing_metadata_excel_file': [],
        'missing_metadata_csv_file': [],
        'missing_global_metadata_file': []
    }
    directories_checked = False

    def __init__(self, pgs_ids_count, ftp_root_path):
        self.pgs_ids = []
        self.pgs_ids_count = pgs_ids_count
        self.ftp_pgs_ids_count = 0
        # FTP root path, e.g. /ebi/ftp/pub/databases/spot/pgs/
        self.ftp_root_path = ftp_root_path
        self.ftp_scores_path = ftp_root_path+'scores/'
        self.ftp_metadata_path = ftp_root_path+'metadata/'

    def print_log_msg(self, key, label):
        if not key:
            print("Error: missing dictionnary key to print the report")
        elif key not in self.log_msg:
            print("Error: the key \""+key+"\" can't be found in the log")
        else:
            if not label:
                label = key
            log_data_list = self.log_msg[key]
            report_content = ''
            data_count = str(len(log_data_list))
            if len(log_data_list) == 0:
                report_content = 'no data'
            elif len(log_data_list) > 20:
                report_content = '\n'+','.join(log_data_list)+'\n'
            else:
                report_content = '\n - '+'\n - '.join(log_data_list)+'\n'
            print("# "+label+" ("+data_count+" entries): "+report_content)


    def check_directories(self):

        for pgs_id in os.listdir(self.ftp_scores_path):
            ftp_pgs_dir = self.ftp_scores_path+pgs_id
            if not os.path.isdir(self.ftp_scores_path+pgs_id):
                continue
            self.pgs_ids.append(pgs_id)
            ftp_score_dir = ftp_pgs_dir+"/ScoringFiles/"
            ftp_metadata_dir = ftp_pgs_dir+"/Metadata/"

            # 1 - Test PGS ScoringFile directory exists
            if not os.path.exists(ftp_score_dir):
                self.log_msg['missing_score_dir'].append(pgs_id)
                continue

            # 2 - Test PGS Metadata directory exists
            if not os.path.exists(ftp_metadata_dir):
                self.log_msg['missing_metadata_dir'].append(pgs_id)
                continue

        if len(self.pgs_ids) != self.pgs_ids_count:
            self.log_msg['missing_pgs_dir'].append('The number of Score directories are different ('+str(len(self.pgs_ids))+' found vs '+str(self.pgs_ids_count)+' expected)!')

        # Missing PGS directories
        self.print_log_msg('missing_pgs_dir', 'Missing PGS directories')

        # Missing PGS Score directories
        self.print_log_msg('missing_score_dir', 'Missing PGS Scoring File directories')

        # Missing PGS Metadata directories
        self.print_log_msg('missing_metadata_dir', 'Missing PGS Metadata directories')

        self.directories_checked = True


    def check_score_files(self):

        if not self.directories_checked:
            self.check_directories()

        for pgs_id in self.pgs_ids:

            if pgs_id in self.log_msg['missing_pgs_dir'] or pgs_id in self.log_msg['missing_score_dir']:
                continue

            ftp_pgs_dir = self.ftp_scores_path+pgs_id
            ftp_score_dir = ftp_pgs_dir+"/ScoringFiles/"
            ftp_std_scoring_file = ftp_score_dir+pgs_id+self.ftp_std_scoringfile_suffix

            # 1 - Test PGS "Standard" ScoringFile file exists and is not empty
            if not os.path.exists(ftp_std_scoring_file):
                self.log_msg['missing_std_scoring_file'].append(pgs_id)
                continue
            elif os.path.getsize(ftp_std_scoring_file) == 0:
                self.log_msg['missing_std_scoring_file'].append(pgs_id)
                continue

            # 2 - Test PGS "Harmonised" ScoringFile file exists and is not empty
            # TODO

        # Missing PGS Scoring Files
        self.print_log_msg('missing_std_scoring_file', 'Missing PGS Standard Scoring Files')


    def check_metadata_files(self):

        if not self.directories_checked:
            self.check_directories()

        for pgs_id in self.pgs_ids:

            if pgs_id in self.log_msg['missing_pgs_dir'] or pgs_id in self.log_msg['missing_metadata_dir']:
                continue

            ftp_pgs_dir = self.ftp_scores_path+pgs_id
            ftp_metadata_dir = ftp_pgs_dir+"/Metadata/"

            # 1 - Test PGS Metadata tar file exists and is not empty
            ftp_metadata_tar_file = ftp_metadata_dir+pgs_id+self.ftp_metadata_file_prefix+self.ftp_metadata_file_suffixes['tar']
            if not os.path.exists(ftp_metadata_tar_file):
                self.log_msg['missing_metadata_tar_file'].append(pgs_id)
            elif os.path.getsize(ftp_metadata_tar_file) == 0:
                self.log_msg['missing_metadata_tar_file'].append(pgs_id)

            # 2 - Test PGS Metadata excel file exists and is not empty
            ftp_metadata_excel_file = ftp_metadata_dir+pgs_id+self.ftp_metadata_file_prefix+self.ftp_metadata_file_suffixes['excel']
            if not os.path.exists(ftp_metadata_excel_file):
                self.log_msg['missing_metadata_excel_file'].append(pgs_id)
            elif os.path.getsize(ftp_metadata_excel_file) == 0:
                self.log_msg['missing_metadata_excel_file'].append(pgs_id)

            # 3 - Test PGS Metadata csv files exist and are not empty
            for suffix in self.ftp_metadata_file_suffixes['csv']:
                ftp_metadata_file = ftp_metadata_dir+pgs_id+self.ftp_metadata_file_prefix+suffix

                if not os.path.exists(ftp_metadata_file):
                    self.log_msg['missing_metadata_csv_file'].append(pgs_id)
                    break
                elif os.path.getsize(ftp_metadata_file) == 0:
                    self.log_msg['missing_metadata_csv_file'].append(pgs_id)
                    break

        # Missing PGS Metadata Files
        self.print_log_msg('missing_metadata_tar_file', 'Missing PGS Metadata tar files')
        self.print_log_msg('missing_metadata_excel_file', 'Missing PGS Metadata Excel files')
        self.print_log_msg('missing_metadata_csv_file', 'Missing PGS Metadata csv files')


    def check_global_metadata_files(self):

        metadata_file_prefix = self.ftp_metadata_path+'pgs_all'+self.ftp_metadata_file_prefix

        # 1 - Test PGS Metadata tar file exists and is not empty
        ftp_metadata_tar_file = metadata_file_prefix+self.ftp_metadata_file_suffixes['tar']
        if not os.path.exists(ftp_metadata_tar_file):
            self.log_msg['missing_global_metadata_file'].append(ftp_metadata_tar_file)
        elif os.path.getsize(ftp_metadata_tar_file) == 0:
            self.log_msg['missing_global_metadata_file'].append(ftp_metadata_tar_file)

        # 2 - Test PGS Metadata excel file exists and is not empty
        ftp_metadata_excel_file = metadata_file_prefix+self.ftp_metadata_file_suffixes['excel']
        if not os.path.exists(ftp_metadata_excel_file):
            self.log_msg['missing_global_metadata_file'].append(ftp_metadata_excel_file)
        elif os.path.getsize(ftp_metadata_excel_file) == 0:
            self.log_msg['missing_global_metadata_file'].append(ftp_metadata_excel_file)

        # 3 - Test PGS Metadata csv files exist and are not empty
        for suffix in self.ftp_metadata_file_suffixes['csv']:
            ftp_metadata_file = metadata_file_prefix+suffix

            if not os.path.exists(ftp_metadata_file):
                self.log_msg['missing_global_metadata_file'].append(ftp_metadata_file)
            elif os.path.getsize(ftp_metadata_file) == 0:
                self.log_msg['missing_global_metadata_file'].append(ftp_metadata_file)

        # Missing PGS Metadata Files
        self.print_log_msg('missing_global_metadata_file', 'Missing PGS Global Metadata files')


def main():

    argparser = argparse.ArgumentParser(description='Script to check that the expected FTP files and directories exist.')
    argparser.add_argument("-n", type=int, help='Number of entries to be checked (will iterate over the number to get the PGS IDs)', required=True)
    argparser.add_argument("--dir", type=str, help='The path to root directory to be checked (e.g. PGS FTP root directory)', required=True)

    args = argparser.parse_args()

    if not(isinstance(args.n, int)):
            print("Error: The first parameter 'Number of entries' must be an integer")
            exit(1)
    if not os.path.exists(args.dir):
            print("Error: The path to ftp root directory can't be found ("+args.dir+").")
            exit(1)

    pgs_ftp_checks = PGSFTPChecks(args.n,args.dir)
    pgs_ftp_checks.check_directories()
    pgs_ftp_checks.check_score_files()
    pgs_ftp_checks.check_metadata_files()
    pgs_ftp_checks.check_global_metadata_files()


if __name__== "__main__":
   main()
