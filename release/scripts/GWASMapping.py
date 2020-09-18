import urllib.request
import requests

class GWASMapping:

    gwas_trait_mapping_url = 'https://www.ebi.ac.uk/gwas/api/search/downloads/trait_mappings'
    line_sep = '\n'
    column_sep = '\t'
    efo_header = 'EFO URI'
    cat_header = 'Parent term'
    parent_header = 'Parent URI'

    def __init__(self):
        self.file_header = []
        self.efo_col_id = None
        self.cat_col_id = None
        self.parent_col_id = None
        self.file_content = []
        self.trait_mapping = {}
        self.categories = {}

    def download_file(self):
        response = urllib.request.urlopen(self.gwas_trait_mapping_url)
        data = response.read()      # a `bytes` object
        self.file_content = data.decode('utf-8').split(self.line_sep)
        self.file_header = self.file_content.pop(0).split(self.column_sep)

    def parse_file(self):
        # Get indexes of the columns of interest
        if self.efo_header in self.file_header:
            self.efo_col_id = self.file_header.index(self.efo_header)
        if self.cat_header in self.file_header:
            self.cat_col_id = self.file_header.index(self.cat_header)
        if self.parent_header in self.file_header:
            self.parent_col_id = self.file_header.index(self.parent_header)

        if self.efo_col_id != None and self.cat_col_id != None:
            for line in self.file_content:
                line_columns = line.split(self.column_sep)
                trait_url = line_columns[self.efo_col_id]
                cat_col = line_columns[self.cat_col_id]
                parent_url = line_columns[self.parent_col_id]
                trait_id = self.extract_id_from_url(trait_url)
                parent_id = self.extract_id_from_url(parent_url)
                if not trait_id in self.trait_mapping:
                    self.trait_mapping[trait_id] = cat_col
                if not cat_col in self.categories:
                    self.categories[cat_col] = { 'eg': parent_id }

        else:
            print("Error: can't find the columns headers '"+self.efo_header+"' and/or '"+self.cat_header+"' in the GWAS EFO Mapping file")

    def extract_id_from_url(self,url):
        return url.split('/')[-1]

    def get_category_information(self):

        for category in self.categories:
            trait_id = self.categories[category]['eg']

            response = requests.get('https://www.ebi.ac.uk/gwas/rest/api/parentMapping/%s'%trait_id)
            response_json = response.json()
            if response_json and response_json['trait'] != 'None':
                category_label  = response_json['colourLabel']
                category_colour = response_json['colour']
                category_parent = response_json['parent']
                if category_label == category:
                    self.categories[category]['colour'] = category_colour
                    self.categories[category]['parent'] = category_parent
                else:
                    print("Error: discrepancies between the GWASMapping file and the REST API regarding the trait category for '"+trait_id+"' ("+category+' vs '+category_label+")")
                    #exit(1)

    def get_gwas_mapping(self):
        try:
            self.download_file()
        except:
            print("Error: can't download the GWAS EFO Mapping file ("+self.gwas_trait_mapping_url+")!")
        self.parse_file()
        self.get_category_information()


def run():
    gwas_mapping = GWASMapping()
    gwas_mapping.get_gwas_mapping()
    print(len(gwas_mapping.trait_mapping.keys()))
    cat_list = list(gwas_mapping.categories.keys())
    cat_list.sort()
    for category in cat_list:
        print(" - "+category+": "+gwas_mapping.categories[category]['colour']+" | "+gwas_mapping.categories[category]['parent']+" | "+gwas_mapping.categories[category]['eg'])
