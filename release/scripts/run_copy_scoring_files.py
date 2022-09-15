import argparse
from release.scripts.CopyScoringFiles import CopyScoringFiles
from release.scripts.CopyHarmonizedScoringFilesPOS import CopyHarmonizedScoringFilesPOS


def copy_scoring_files(new_ftp_dir,staged_scores_dir,scores_dir):
    print("\n#### Copy the new formatted scoring files ####")
    pgs_scoring_files = CopyScoringFiles(new_ftp_dir,staged_scores_dir,scores_dir)
    pgs_scoring_files.get_previous_release()
    pgs_scoring_files.get_list_of_scores()
    pgs_scoring_files.copy_scoring_files_to_production()
    pgs_scoring_files.copy_scoring_files_to_metadata()

def copy_hmpos_scoring_files(new_ftp_dir,staged_scores_dir,scores_dir):
    print("\n#### Copy the new harmonized position scoring files ####")
    pgs_harmonized_files = CopyHarmonizedScoringFilesPOS(new_ftp_dir,staged_scores_dir,scores_dir)
    pgs_harmonized_files.copy_harmonized_files_to_production()
    pgs_harmonized_files.copy_harmonized_files_to_metadata()


def main():

    argparser = argparse.ArgumentParser(description='Script to copy the scoring files and harmonized scoring files to the new FTP.')
    argparser.add_argument("--new_ftp_dir", type=str, help='The path to the data directory (only containing the metadata)', required=True)
    argparser.add_argument("--staged_scores_dir", type=str, help='The path to the staged scoring files directory', required=True)
    argparser.add_argument("--scores_dir", type=str, help='The path to the scoring files directory (Production)', required=False)
    argparser.add_argument("--hm_staged_scores_dir", type=str, help='The path to the harmonized Position staged files directory', required=True)
    argparser.add_argument("--hm_scores_dir", type=str, help='The path to the harmonized scoring files directory (Production)', required=False)


    args = argparser.parse_args()

    new_ftp_dir = args.new_ftp_dir
    staged_scores_dir = args.staged_scores_dir
    scores_dir = args.scores_dir
    hm_staged_scores_dir = args.hm_staged_scores_dir
    hm_scores_dir = args.hm_scores_dir

    copy_scoring_files(new_ftp_dir,staged_scores_dir,scores_dir)

    copy_hmpos_scoring_files(new_ftp_dir,hm_staged_scores_dir,hm_scores_dir)


if __name__== "__main__":
   main()
