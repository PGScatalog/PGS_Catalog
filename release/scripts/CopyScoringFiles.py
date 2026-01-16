import sys, os, shutil, stat, glob, re, pwd
from os import path
import requests
import argparse
import hashlib

class CopyScoringFiles:

    ftp_scoring_files_dir = '/nfs/ftp/public/databases/spot/pgs/scores/'
    ftp_std_scoringfile_suffix = '.txt.gz'
    scores_list_file = 'pgs_scores_list.txt'
    sql_table = 'catalog_scorefilemd5'
    log_msg = {
        'new': [],
        'updated': [],
        'skipped': []
    }

    def __init__(self, new_ftp_scores_dir, staged_scores_dir, scoring_files_dir, md5_sql_filepath, username):
        self.new_ftp_scores_dir = new_ftp_scores_dir
        self.new_scoringfiles_dir = staged_scores_dir
        self.scoring_files_dir = scoring_files_dir
        self.md5_sql_filepath = md5_sql_filepath
        self.username = username

        if not os.path.exists(new_ftp_scores_dir):
            print(f'Error: The path to the data directory can\'t be found ({new_ftp_scores_dir}).')
            exit(1)
        if not os.path.exists(new_ftp_scores_dir+'/'+self.scores_list_file):
            print(f'Error: The file listing the score ID is missing ({new_ftp_scores_dir}/{self.scores_list_file}).')
            exit(1)
        if not os.path.exists(staged_scores_dir):
            print(f'Error: The path to the private FTP scoring files directory can\'t be found ({staged_scores_dir}).')
            exit(1)
        if not os.path.exists(scoring_files_dir):
            print(f'Error: The path to the scoring files directory can\'t be found ({scoring_files_dir}).')
            exit(1)


    def get_previous_release(self):
        """"
        Generic method to perform REST API call to the live PGS Catalog
        The live release is used here as 'previous release'
        > Return type: current release version (date)
        """
        rest_full_url = 'https://www.pgscatalog.org/rest/release/current'
        try:
            response = requests.get(rest_full_url)
            response_json = response.json()
            if 'date' in response_json:
                self.previous_release = response_json['date']
                if not re.match(r'^\d{4}\-\d{2}\-\d{2}', self.previous_release):
                    print("Error: The previous release date '"+str(self.previous_release)+"' doesn't match the required format (YYYY-MM-DD).")
                    exit(1)
            else:
                print("Error: Can't retrieve the previous release date from the live website REST API.")
                exit(1)
        except requests.exceptions.RequestException as e:
            raise SystemExit(e)


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
            elif 20 < list_length < 100:
                report_content = '\n'+','.join(log_data_list)+'\n'
            elif list_length > 100 and key == 'skipped':
                report_content = '\nToo many PGS IDs to display\n'
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
        scoring_files = [f for f in os.listdir(self.new_scoringfiles_dir) if os.path.isfile('/'.join([self.new_scoringfiles_dir, f])) and re.match(r'^PGS\d+\.txt\.gz$', f)]
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
            scoring_file_ftp_priv = f'{self.new_scoringfiles_dir}/{scoring_file}'
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
                # Copy file
                try:
                    shutil.copyfile(scoring_file_ftp_priv, scoring_file_prod)
                    print(copy_msg)
                    if copy_type == 'update':
                        count_updated_pgs += 1
                    elif copy_type == 'new':
                        count_new_pgs += 1
                    else:
                        print(f'>>>>> ERROR! Can\'t determine whether the copy of \'{scoring_file}\' was due to the very first version of the scoring file or an updated version of the file')
                # If there is any permission issue
                except PermissionError as e:
                    print(f'>>>>> ERROR! File \'{scoring_file}\' (Permission issue) - {e}')
                except IOError as e:
                    print(f'>>>>> ERROR! File \'{scoring_file}\' couldn\'t be copied to production: "{self.scoring_files_dir}"!')
                    print(e)
                # Change chmod to allow group write access
                if os.path.isfile(scoring_file_prod):
                    file_owner = pwd.getpwuid(os.stat(scoring_file_prod).st_uid).pw_name
                    if self.username == file_owner:
                        try:
                            os.chmod(scoring_file_prod, stat.S_IRUSR|stat.S_IWUSR|stat.S_IRGRP|stat.S_IWGRP|stat.S_IROTH)
                        except:
                            print(f">>>>> ERROR! Can't change the read/write access of the file '{scoring_file}'!")
        total_count = count_new_pgs + count_updated_pgs
        print(f'Number of PGS files successfully copied: {total_count} (New: {count_new_pgs} | Updated: {count_updated_pgs} | Skipped: {count_skipped_pgs})')


    def copy_scoring_files_to_metadata(self):
        """ Copy the new/updated scoring files to the metadata directory (temporary FTP) """
        print("\n***** Step 2 - Copy the new/updated scoring files to the metadata directory (temporary FTP) *****")

        # md5_sql_file = open(self.md5_sql_filepath,'w')

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

            # Generate md5 checksum of the "new" scoring file
            new_score_md5 = self.get_md5_checksum(new_score_file)

            to_copy = True
            is_updated = False
            # Check if dir exist in FTP
            if os.path.exists(ftp_score_dir):
                # Check if score file exist in FTP
                if os.path.exists(ftp_score_file):
                    # Generate md5 checksum for the current file on FTP
                    ftp_score_md5 = self.get_md5_checksum(ftp_score_file)
                    # Check if score file is different
                    if new_score_md5 == ftp_score_md5:
                        to_copy = False
                        self.log_msg['skipped'].append(score_id)
                    else:
                        #print(score_id+": "+ftp_score_md5+" | "+new_score_md5)
                        # Create archive and copy FTP file in it
                        scoring_archives = score_release_dir+'archived_versions/'
                        scoring_archives_file = score_id+'_'+self.previous_release+self.ftp_std_scoringfile_suffix
                        self.create_directory(score_release_dir)
                        self.create_directory(scoring_archives)
                        shutil.copy2(ftp_score_file, scoring_archives+scoring_archives_file)
                        self.log_msg['updated'].append(score_id)
                        is_updated = True

            if to_copy == True:
                self.create_directory(score_release_dir)
                score_release_file = score_release_dir+score_filename

                # Generate md5 checksum file
                md5_file = open(score_release_file+'.md5','w')
                md5_file.write(f'{new_score_md5}  {score_filename}')
                md5_file.close()

                shutil.copy2(new_score_file, score_release_file)
                if not score_id in self.log_msg['updated']:
                    self.log_msg['new'].append(score_id)

                # # md5 checksum SQL commands
                # id = re.sub(r'PGS0+(.+)', r'\1', score_id)
                # if is_updated:
                #     sql_cmd = f"UPDATE {self.sql_table} SET score_md5='{new_score_md5}' WHERE score_id={id};\n"
                # else:
                #     sql_cmd = f"INSERT INTO {self.sql_table} (score_id,score_md5) VALUES ({id},'{new_score_md5}');\n"
                # md5_sql_file.write(sql_cmd)

        # md5_sql_file.close()


        # Copied PGS Scoring files
        self.print_log_msg('new', 'New PGS Scoring files')

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
            print("Error: the script couldn't generate a MD5 checksum for '" + filename + "'!")
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

    defaut_scores_dir = '/nfs/production/parkinso/spot/pgs/data-files/ScoringFiles/'

    argparser = argparse.ArgumentParser(description='Script to copy the scoring files.')
    argparser.add_argument("--new_ftp_dir", type=str, help='The path to the data directory (only containing the metadata)', required=True)
    argparser.add_argument("--staged_scores_dir", type=str, help='The path to the staged scoring files directory', required=True)
    argparser.add_argument("--scores_dir", type=str, help='The path to the scoring files directory', default=defaut_scores_dir, required=False)

    args = argparser.parse_args()

    pgs_scoring_files = CopyScoringFiles(args.new_ftp_dir,args.staged_scores_dir,args.scores_dir)
    pgs_scoring_files.get_previous_release()
    pgs_scoring_files.get_list_of_scores()
    pgs_scoring_files.copy_scoring_files_to_production()
    pgs_scoring_files.copy_scoring_files_to_metadata()

if __name__== "__main__":
   main()
