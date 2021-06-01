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
    data_dir = '/scores/'
    scoring_dir = '/ScoringFiles/'
    meta_dir    = '/Metadata/'
    meta_file_extension = '.tar.gz'


    def __init__(self, pgs_id, file_suffix ,type):
        self.pgs_id = pgs_id
        self.file_suffix = file_suffix
        if type in self.allowed_types:
            self.type = type
        else:
            print("The type '"+type+"' is not recognised!")
            exit()


    def get_ftp_data_md5(self):
        """ Get the MD5 of the Excel spreadsheet on FTP to compare with current Excel spreadsheet. """

        ftp = FTP(self.ftp_root)     # connect to host, default port
        ftp.login()                  # user anonymous, passwd anonymous@

        m = hashlib.md5()
        filepath = self.ftp_path+self.data_dir+self.pgs_id+'/'
        if self.type == 'metadata':
            filepath += self.meta_dir+self.pgs_id+self.file_suffix
        else:
            filepath += self.score_dir+self.pgs_id+self.file_suffix

        try:
            ftp.retrbinary('RETR %s' % filepath, m.update)
            return m.hexdigest()
        except:
            print("Can't find or access FTP file: "+self.ftp_root+'/'+filepath)


    def get_ftp_data_size(self):
        """ Get the size of the Excel spreadsheet on FTP to compare with current Excel spreadsheet. """

        ftp = FTP(self.ftp_root)     # connect to host, default port
        ftp.login()                  # user anonymous, passwd anonymous@

        filepath = self.ftp_path+self.data_dir+self.pgs_id+'/'
        if self.type == 'metadata':
            filepath += self.meta_dir+self.pgs_id+self.file_suffix
        else:
            filepath += self.score_dir+self.pgs_id+self.file_suffix

        try:
            size = ftp.size(filepath)
            return size
        except:
            print("Can't find or access FTP file: "+self.ftp_root+'/'+filepath)


    def get_ftp_file(self,ftp_filename,new_filename):
        """ Download data file from the PGS FTP. """

        path = self.ftp_path
        # Metadata file
        if self.type == 'metadata':
            if self.pgs_id == 'all':
                path += self.meta_dir.lower()
                #filename = self.all_meta_file
            else:
                path += self.data_dir+self.pgs_id+self.meta_dir
                #filename = self.pgs_id+self.file_suffix
        # Score file
        else:
            path += self.data_dir+self.pgs_id+'/'+self.score_dir
            #filename = self.pgs_id+self.file_suffix

        ftp = FTP(self.ftp_root)     # connect to host, default port
        ftp.login()                  # user anonymous, passwd anonymous@
        ftp.cwd(path)
        ftp.retrbinary("RETR " + ftp_filename, open(new_filename, 'wb').write)
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
            print("Error: the script couldn't generate a MD5 checksum for '" + filename + "'!")
            return None

        return md5.hexdigest()
