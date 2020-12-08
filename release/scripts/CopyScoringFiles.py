import sys, os, shutil, stat, glob, re
from os import path
import argparse
import hashlib

class CopyScoringFiles:

    ftp_scoring_files_dir = '/ebi/ftp/pub/databases/spot/pgs/scores/'
    ftp_std_scoringfile_suffix = '.txt.gz'
    scores_list_file = 'pgs_scores_list.txt'

    log_msg = {
        'copied': [],
        'updated': [],
        'skipped': []
    }

    def __init__(self, new_ftp_scores_dir, private_ftp_scoring_files_dir, scoring_files_dir, previous_release):
        self.new_ftp_scores_dir = new_ftp_scores_dir
        self.scoring_files_ftp_dir = private_ftp_scoring_files_dir
        self.scoring_files_dir = scoring_files_dir
        self.previous_release = previous_release

        if not os.path.exists(new_ftp_scores_dir):
            print(f'Error: The path to the data directory can\'t be found ({new_ftp_scores_dir}).')
            exit(1)
        if not os.path.exists(new_ftp_scores_dir+'/'+self.scores_list_file):
            print(f'Error: The file listing the score ID is missing ({new_ftp_scores_dir}/{self.scores_list_file}).')
            exit(1)
        if not os.path.exists(private_ftp_scoring_files_dir):
            print(f'Error: The path to the private FTP scoring files directory can\'t be found ({private_ftp_scoring_files_dir}).')
            exit(1)
        if not os.path.exists(scoring_files_dir):
            print(f'Error: The path to the scoring files directory can\'t be found ({scoring_files_dir}).')
            exit(1)
        if not previous_release:
            print("ERROR: the previous release date must be given as 3rd argument.")
            exit(1)


    def print_log_msg(self, key, label):
        if not key:
            print("Error: missing dictionnary key to print the report")
        elif key not in self.log_msg:
            print("Error: the key \""+key+"\" can't be found in the log")
        else:
            if not label:
                label = key

            log_data_list = self.log_msg[key]
            list_length = len(log_data_list)
            report_content = ''
            if list_length == 0:
                report_content = str(list_length)
            elif list_length > 20:
                report_content = '\n'+','.join(log_data_list)+'\n'
            else:
                report_content = '\n - '+'\n - '.join(log_data_list)+'\n'
            print("# "+label+" ("+str(list_length)+"): "+report_content)


    def get_list_of_scores(self):
        """ Extract the list of scores to be published, for the text file. """
        scores_file = open(self.new_ftp_scores_dir+'/'+self.scores_list_file, 'r')
        self.score_ids_list = [ line.strip(' \t\n') for line in scores_file.readlines() ]
        scores_file.close()


    def copy_scoring_files_to_production(self):
        """ Copy the new/updated scoring files from the private FTP to the production directory """
        print("\n***** Step 1 - Copy the new/updated scoring files from the private FTP to the production directory *****")
        count_new_pgs = 0
        count_updated_pgs = 0
        count_skipped_pgs = 0
        # Extract list of files on private FTP
        scoring_files = [f for f in os.listdir(self.scoring_files_ftp_dir) if os.path.isfile('/'.join([self.scoring_files_ftp_dir, f])) and re.match('^PGS\d+\.txt\.gz$',f)]
        # Check if corresponding ID in the list of scores to be published.
        # If so checks if it exists and if it needs to be copied (new/update)
        for scoring_file in scoring_files:
            scoring_file_id = scoring_file.split('.')[0]
            copy_msg = ''
            copy_type = ''
            # Score ID not in the list
            if not scoring_file_id in self.score_ids_list:
                print(f' ! File \'{scoring_file}\' has been skipped: not present in the list of released scores!')
                count_skipped_pgs += 1
                continue

            # Score ID in the list
            scoring_file_ftp_priv = f'{self.scoring_files_ftp_dir}/{scoring_file}'
            scoring_file_prod = f'{self.scoring_files_dir}/{scoring_file}'
            # Scoring file already in the Production directory - will check if it differs from the one on the private FTP
            if os.path.isfile(scoring_file_prod):
                md5_ftp_priv = self.get_md5_checksum(scoring_file_ftp_priv)
                md5_prod = self.get_md5_checksum(scoring_file_prod)
                if md5_ftp_priv != md5_prod:
                    copy_msg = f' > Updated file \'{scoring_file}\' has been copied to \'{self.scoring_files_dir}\''
                    copy_type = 'update'
            # Scoring file is new: it's not yet in the Production directory
            else:
                copy_msg = f' - New file \'{scoring_file}\' has been copied to \'{self.scoring_files_dir}\''
                copy_type = 'new'

            # Copy the file, if it was found new or modified
            if copy_msg != '':
                try:
                    shutil.copy2(scoring_file_ftp_priv, scoring_file_prod)
                    print(copy_msg)
                    if copy_type == 'update':
                        count_updated_pgs += 1
                    elif copy_type == 'new':
                        count_new_pgs += 1
                    else:
                        print(f'>>>>> ERROR! Can\'t determine whether the copy of \'{scoring_file}\' was due to the very first version of the scoring file or an updated version of the file')
                except IOError as e:
                    print(f'>>>>> ERROR! File \'{scoring_file}\' couldn\'t be copied to "{self.scoring_files_dir}"!')
                    print(e)
        total_count = count_new_pgs + count_updated_pgs
        print(f'Number of PGS files successfully copied: {total_count} (New: {count_new_pgs} | Updated: {count_updated_pgs} | Skipped: {count_skipped_pgs})')

        # Change chmod to allow group write access
        for fname in glob.glob(f'{self.scoring_files_dir}/*'):
            os.chmod(fname, stat.S_IRUSR|stat.S_IWUSR|stat.S_IRGRP|stat.S_IWGRP|stat.S_IROTH)


    def copy_scoring_files_to_metadata(self):
        """ Copy the new/updated scoring files to the metadata directory (temporary FTP) """
        print("\n***** Step 2 - Copy the new/updated scoring files to the metadata directory (temporary FTP) *****")
        for score_id in sorted(os.listdir(self.new_ftp_scores_dir+'/scores/')):
            score_release_dir = self.new_ftp_scores_dir+'/scores/'+score_id+'/ScoringFiles/'

            score_filename = score_id+self.ftp_std_scoringfile_suffix
            new_score_file = self.scoring_files_dir+'/'+score_filename

            ftp_score_dir = self.ftp_scoring_files_dir+score_id
            ftp_score_file = ftp_score_dir+"/ScoringFiles/"+score_filename

            # Check new PSG Scoring File
            if not os.path.exists(new_score_file):
                print("ERROR: new PGS Scoring file '"+new_score_file+"' can't be found.")
                continue
            elif os.path.getsize(new_score_file) == 0:
                print("ERROR: new PGS Scoring file '"+new_score_file+"' is empty.")
                continue

            to_copy = 1
            # Check if dir exist in FTP
            if os.path.exists(ftp_score_dir):
                # Check if score file exist in FTP
                if os.path.exists(ftp_score_file):
                    ftp_score_md5 = self.get_md5_checksum(ftp_score_file)
                    new_score_md5 = self.get_md5_checksum(new_score_file)
                    print(score_id+": "+ftp_score_md5+" | "+new_score_md5)
                    # Check if score file is different
                    if new_score_md5 == ftp_score_md5:
                        to_copy = 0
                        self.log_msg['skipped'].append(score_id)
                    else:
                        # Create archive and copy FTP file in it

                        scoring_archives = score_release_dir+'archived_versions/'
                        scoring_archives_file = score_id+'_'+self.previous_release+self.ftp_std_scoringfile_suffix
                        self.create_directory(score_release_dir)
                        self.create_directory(scoring_archives)
                        shutil.copy2(ftp_score_file, scoring_archives+scoring_archives_file)
                        self.log_msg['updated'].append(score_id)

            if (to_copy == 1):
                self.create_directory(score_release_dir)
                shutil.copy2(new_score_file, score_release_dir+score_filename)
                if not score_id in self.log_msg['updated']:
                    self.log_msg['copied'].append(score_id)


        # Copied PGS Scoring files
        self.print_log_msg('copied', 'Copied PGS Scoring files')

        # Updated PGS Scoring files (old files are archived)
        self.print_log_msg('updated', 'Updated PGS Scoring files')

        # Skipped PGS Scoring files (same files, no need to be copied)
        self.print_log_msg('skipped', 'Skipped PGS Scoring files')


    def get_md5_checksum(self,filename,blocksize=4096):
        """ Returns MD5 checksum for the given file. """

        md5 = hashlib.md5()
        try:
            file = open(filename, 'rb')
            with file:
                for block in iter(lambda: file.read(blocksize), b""):
                    md5.update(block)
        except IOError:
            print('File \'' + filename + '\' not found!')
            return None
        except:
            print("Error: the script couldn't generate a MD5 checksum for '" + self.filename + "'!")
            return None

        return md5.hexdigest()


    def create_directory(self,path):
        """ Create directory if it didn't exist """
        if not os.path.isdir(path):
            try:
                os.mkdir(path, 0o755)
            except OSError:
                print ("Creation of the directory %s failed" % path)
                exit()

def main():

    defaut_scores_dir = '/nfs/production3/spot/pgs/data-files/ScoringFiles/'

    argparser = argparse.ArgumentParser(description='Script to check that the expected FTP files and directories exist.')
    argparser.add_argument("--prev_release", type=str, help='Date of the previous release (format YYYY-MM-DD)', required=True)
    argparser.add_argument("--data_dir", type=str, help='The path to the data directory (only containing the metadata)', required=True)
    argparser.add_argument("--ftp_scores_dir", type=str, help='The path to the scoring files directory on the private FTP', required=True)
    argparser.add_argument("--scores_dir", type=str, help='The path to the scoring files directory', default=defaut_scores_dir, required=False)

    args = argparser.parse_args()

    if not re.match(r'^\d{4}\-\d{2}\-\d{2}', args.prev_release):
        print("Error: The previous release date '"+str(args.prev_release)+"' doesn't match the required format (YYYY-MM-DD).")
        exit(1)

    pgs_scoring_files = CopyScoringFiles(args.data_dir,args.ftp_scores_dir,args.scores_dir,args.prev_release)
    pgs_scoring_files.get_list_of_scores()
    pgs_scoring_files.copy_scoring_files_to_production()
    pgs_scoring_files.copy_scoring_files_to_metadata()

if __name__== "__main__":
   main()
