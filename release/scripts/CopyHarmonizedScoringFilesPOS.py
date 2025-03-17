import sys, os, shutil, stat, glob, re, pwd
from os import path
import requests
import argparse
import hashlib

class CopyHarmonizedScoringFilesPOS:

    ftp_std_scoringfile_suffix = '.txt.gz'
    scores_list_file = 'pgs_scores_list.txt'
    sql_table = 'catalog_scorefilemd5'
    genebuilds = ['37','38']
    harmonized_files_to_copy = {}
    mode = 0o775

    log_msg = { 'new': {}, 'updated': {} }
    for type in log_msg.keys():
        for gb in genebuilds:
            log_msg[type][gb] = []

    def __init__(self, new_ftp_scores_dir, staged_harmonized_files_dir, harmonized_files_dir, md5_sql_filepath, username, custom_list_scores=None):
        self.new_ftp_scores_dir = new_ftp_scores_dir
        self.harmonized_files_staged_dir = staged_harmonized_files_dir
        self.harmonized_files_prod_dir = harmonized_files_dir
        if custom_list_scores:
            self.scores_list_file_path = custom_list_scores
        else:
            self.scores_list_file_path = new_ftp_scores_dir+'/'+self.scores_list_file
        self.md5_sql_filepath = md5_sql_filepath
        self.username = username

        if not os.path.exists(new_ftp_scores_dir):
            print(f'Error: The path to the data directory can\'t be found ({new_ftp_scores_dir}).')
            exit(1)
        if not os.path.exists(self.scores_list_file_path):
            print(f'Error: The file listing the score ID is missing ({self.scores_list_file_path}).')
            exit(1)
        if not os.path.exists(staged_harmonized_files_dir):
            print(f'Error: The path to the staged FTP harmonized files directory can\'t be found ({staged_harmonized_files_dir}).')
            exit(1)
        if not os.path.exists(harmonized_files_dir):
            print(f'Error: The path to the harmonized files directory can\'t be found ({harmonized_files_dir}).')
            exit(1)


    def copy_harmonized_files_to_production(self):
        """ Copy the new/updated scoring files from the private FTP to the production directory """
        print("\n***** Step 1 - Copy the new/updated harmonized scoring files from the staged directory to the production directory *****")

        # Get the list of Scores in the new release and already released
        self.get_list_of_scores()

        # Extract list of files on staged directories
        for gb in self.genebuilds:
            print(f"#### GRCh{gb} files to be copied:")
            count_new_pgs = 0
            count_updated_pgs = 0
            count_skipped_pgs = 0

            staged_dir_gb = self.harmonized_files_staged_dir
            if not staged_dir_gb.endswith('/'):
                staged_dir_gb += '/'
            staged_dir_gb += gb

            harmonized_files = [f for f in os.listdir(staged_dir_gb) if os.path.isfile('/'.join([staged_dir_gb, f])) and re.match('^PGS\d+_hmPOS_.+\.txt\.gz$',f)]

            # Check if corresponding ID in the list of scores to be published.
            # If so checks if it exists and if it needs to be copied (new/update)
            for harmonized_file in harmonized_files:
                filename_parts = harmonized_file.split('_')
                pgs_id = filename_parts[0]
                print(f"> {pgs_id} - {gb}:")
                copy_msg = ''
                copy_type = ''
                # Score ID not in the list
                if not pgs_id in self.score_ids_list:
                    print(f" ! File '{harmonized_file}' has been skipped: not present in the list of released scores!")
                    count_skipped_pgs += 1
                    continue

                # Harmonized score files
                harmonized_file_staged = f'{staged_dir_gb}/{harmonized_file}'
                harmonized_file_prod_dir = f'{self.harmonized_files_prod_dir}/{pgs_id}/{gb}'
                harmonized_file_prod = f'{harmonized_file_prod_dir}/{harmonized_file}'

                # Harmonized Scoring file already in the Production directory - not expected (at least a different version)
                if os.path.isfile(harmonized_file_prod):
                    # Compare latest vs new file to be sure they are different
                    prod_harmonized_md5 = self.get_md5_checksum(harmonized_file_prod)
                    staged_harmonized_md5 = self.get_md5_checksum(harmonized_file_staged)
                    # Check if score file is different
                    if prod_harmonized_md5 == staged_harmonized_md5:
                        print(f"ERROR - {pgs_id}: the new and the current harmonized files are identical!")
                        count_skipped_pgs += 1
                    else:
                        copy_msg = f" > New version ('{harmonized_file}') has been copied to '{harmonized_file_prod_dir}'"
                        copy_type = 'updated'
                # Scoring file is new: it's not yet in the Production directory
                else:
                    copy_msg = f" - New file '{harmonized_file}' has been copied to '{harmonized_file_prod_dir}'"
                    copy_type = 'new'

                # Copy the file, if it was found new or modified
                if copy_msg != '':
                    print(f"Try copy file {harmonized_file_staged} to {harmonized_file_prod}")
                    try:
                        # Copy new harmonized file into production
                        self.create_directory(f'{self.harmonized_files_prod_dir}/{pgs_id}/')
                        self.create_directory(harmonized_file_prod_dir)
                        if os.path.isdir(harmonized_file_prod_dir):
                            try:
                                shutil.copyfile(harmonized_file_staged, harmonized_file_prod)
                                # If there is any permission issue
                            except PermissionError as e:
                                print(f'>>>>> ERROR! File \'{harmonized_file}\' (Permission issue) - {e}')
                            except IOError as e:
                                print(f'>>>>> ERROR! File \'{harmonized_file}\' couldn\'t be copied to production: "{self.harmonized_files_prod_dir}"!')
                                print(e)

                            # Change chmod to allow group write access
                            file_owner = pwd.getpwuid(os.stat(harmonized_file_prod).st_uid).pw_name
                            if self.username == file_owner:
                                try:
                                    os.chmod(harmonized_file_prod, stat.S_IRUSR|stat.S_IWUSR|stat.S_IRGRP|stat.S_IWGRP|stat.S_IROTH)
                                    print(copy_msg)
                                except:
                                    print(f">>>>> ERROR! Can't change the read/write access of the file '{harmonized_file}'!")

                            file_info = { 'genebuild': gb, 'name': harmonized_file, 'status': copy_type }
                            if not pgs_id in self.harmonized_files_to_copy:
                                self.harmonized_files_to_copy[pgs_id] = []
                            self.harmonized_files_to_copy[pgs_id].append(file_info)

                            if copy_type == 'updated':
                                count_updated_pgs += 1
                            elif copy_type == 'new':
                                count_new_pgs += 1
                            else:
                                print(f'>>>>> ERROR! Can\'t determine whether the copy of \'{harmonized_file}\' was due to the very first version of the scoring file or an updated version of the file')
                        else:
                            print(f'>>>>> ERROR! Directory \'{harmonized_prod_path}\' is missing')
                    except IOError as e:
                        print(f'>>>>> ERROR! File \'{harmonized_file}\' couldn\'t be copied to "{self.harmonized_files_prod_dir}"!')
                        print(e)
                else:
                    print(f"No try to copy {harmonized_file_staged}")

            # Counts
            total_count = count_new_pgs + count_updated_pgs
            print(f'\n===> Number of PGS harmonized files successfully copied on {gb}: {total_count} (New: {count_new_pgs} | Updated: {count_updated_pgs} | Skipped: {count_skipped_pgs})\n')


    def copy_harmonized_files_to_metadata(self):
        """ Copy the new/updated scoring files to the metadata directory (temporary FTP) """
        print("\n***** Step 2 - Copy the new/updated scoring files to the metadata directory (temporary FTP) *****")

        # md5_sql_file = open(self.md5_sql_filepath,'a')

        for score_id in sorted(self.harmonized_files_to_copy.keys()):

            score_release_dir = self.new_ftp_scores_dir+'/scores/'+score_id+'/ScoringFiles/'
            self.create_directory(score_release_dir)

            harmonized_release_dir = f'{score_release_dir}/Harmonized'
            self.create_directory(harmonized_release_dir)

            id = re.sub(r'PGS0+(.+)', r'\1', score_id)

            for entry in self.harmonized_files_to_copy[score_id]:
                harmonized_gb = entry['genebuild']
                harmonized_filename = entry['name']
                harmonized_status = entry['status']

                harmonized_file_prod = f'{self.harmonized_files_prod_dir}/{score_id}/{harmonized_gb}/{harmonized_filename}'
                harmonized_file_release = f'{harmonized_release_dir}/{harmonized_filename}'

                # Generate md5 checksum file
                harmonized_file_md5 = self.get_md5_checksum(harmonized_file_prod)
                md5_file = open(harmonized_file_release+'.md5','w')
                md5_file.write(f'{harmonized_file_md5}  {harmonized_filename}')
                md5_file.close()

                shutil.copy2(harmonized_file_prod, harmonized_file_release)
                self.log_msg[harmonized_status][harmonized_gb].append(score_id)

                # # md5 checksum SQL commands
                # sql_cmd = f"UPDATE {self.sql_table} SET hmpos_{harmonized_gb}_md5='{harmonized_file_md5}' WHERE score_id={id};\n"
                # md5_sql_file.write(sql_cmd)

        # md5_sql_file.close()

        # Copied PGS Scoring files
        self.print_log_msg('new', 'New PGS Scoring files')

        # Updated PGS Scoring files (old files are archived)
        self.print_log_msg('updated', 'Updated PGS Scoring files')


    def get_list_of_scores(self):
        """ Extract the list of scores to be published, for the text file. """
        scores_file = open(self.scores_list_file_path, 'r')
        self.score_ids_list = [ line.strip(' \t\n') for line in scores_file.readlines() ]
        scores_file.close()


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
                os.mkdir(path,self.mode)
                # Force mode
                os.chmod(path,self.mode)
            except OSError:
                print (f"Creation of the directory {path} failed!")
                exit()


    def print_log_msg(self, key, label):
        if not key:
            print("Error: missing dictionnary key to print the report")
        elif key not in self.log_msg:
            print(f"Error: the key '{key}' can't be found in the log")
        else:
            if not label:
                label = key
            print(f"#### {label} ####")
            for gb in self.genebuilds:
                log_data_list = self.log_msg[key][gb]
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
                print(f"# Genebuild {gb} ({list_length}): {report_content}")


################################################################################

def main():

    defaut_scores_dir = '/nfs/production/parkinso/spot/pgs/data-files/Harmonization/harmonized_files/'

    argparser = argparse.ArgumentParser(description='Script to copy the harmonized scoring files to the new FTP.')
    argparser.add_argument("--new_ftp_dir", type=str, help='The path to the data directory (only containing the metadata)', required=True)
    argparser.add_argument("--staged_scores_dir", type=str, help='The path to the harmonized Position staged files directory', required=True)
    argparser.add_argument("--scores_dir", type=str, help='The path to the scoring files directory', default=defaut_scores_dir, required=False)

    args = argparser.parse_args()

    print(f"> FTP data dir: {args.data_dir}")
    print(f"> Staged dir: {args.staged_scores_dir}")
    print(f"> Prod dir: {args.scores_dir}")
    pgs_harmonized_files = CopyHarmonizedScoringFilesPOS(args.data_dir,args.staged_scores_dir,args.scores_dir)
    pgs_harmonized_files.copy_harmonized_files_to_production()
    pgs_harmonized_files.copy_harmonized_files_to_metadata()

if __name__== "__main__":
    main()
