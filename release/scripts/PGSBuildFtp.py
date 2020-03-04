import sys, os
import hashlib
import requests
import urllib
from ftplib import FTP


class PGSBuildFtp:

    ftp_root = 'ftp.ebi.ac.uk'
    ftp_path = 'pub/databases/spot/pgs/'
    allowed_types = ['score','metadata']
    all_meta_file = 'pgs_all_metadata.tar.gz'
    data_dir = '/ScoringFiles_formatted/'
    #data_dir = '/scores/'
    scoring_dir = '/ScoringFiles/'
    meta_dir    = '/Metadata/'


    def __init__(self, pgs_id, file_extension ,type):
        self.pgs_id = pgs_id
        self.file_extension = file_extension
        if type in self.allowed_types:
            self.type = type
        else:
            print("The type '"+type+"' is not recognised!")
            exit()


    def get_ftp_data_md5(self):
        """ Check that all the PGSs have a corresponding Scoring file in the PGS FTP. """

        ftp = FTP(self.ftp_root)     # connect to host, default port
        ftp.login()                  # user anonymous, passwd anonymous@

        m = hashlib.md5()
        filepath = self.ftp_path+self.data_dir+self.pgs_id+'/'
        if self.type == 'metadata':
            filepath += self.meta_dir+self.pgs_id+self.file_extension
        else:
            filepath += self.score_dir+self.pgs_id+'.txt.gz'

        try:
            ftp.retrbinary('RETR %s' % filepath, m.update)
            return m.hexdigest()
        except:
            print("Can't find or access FTP file: "+self.ftp_root+'/'+filepath)


    def get_ftp_file(self,new_filename):
        """ Download data file from the PGS FTP. """

        path = self.ftp_path
        # Metadata file
        if self.type == 'metadata':
            if self.pgs_id == 'all':
                path += self.meta_dir.lower()
                filename = self.all_meta_file
            else:
                path += self.data_dir+self.pgs_id+self.meta_dir
                filename = self.pgs_id+self.file_extension
        # Score file
        else:
            path += self.data_dir+self.pgs_id+'/'+self.score_dir
            filename = self.pgs_id+self.file_extension

        ftp = FTP(self.ftp_root)     # connect to host, default port
        ftp.login()                  # user anonymous, passwd anonymous@
        ftp.cwd(path)
        ftp.retrbinary("RETR " + filename, open(new_filename, 'wb').write)
        ftp.quit()


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
