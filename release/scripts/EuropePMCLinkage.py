import os, re
import os.path
import requests
from lxml import etree as ET
from catalog.models import Publication
from pgs_web import constants


class EuropePMCLinkage:

    provider_id = '2090'
    pgs_url = constants.USEFUL_URLS['PGS_WEBSITE_URL']
    link_root = pgs_url+'publication/'
    default_filename = '../PGSLinks.xml'

    xml_document = ET.Element('links')

    pgp_with_ppr = []
    missing_links = []

    publications = Publication.objects.filter(date_released__isnull=False).order_by('num')

    def __init__(self, filename=default_filename):
        self.filename = filename


    def get_ppr(self, doi):
        '''
        Retrieve the PPR of the preprint via Europe PMC REST API, using the DOI
        Return the PPR if found
        '''
        ppr = None
        payload = {'format': 'json'}
        payload['query'] = 'doi:' + doi
        r = requests.get(constants.USEFUL_URLS['EPMC_REST_SEARCH'], params=payload)
        r = r.json()
        if r['resultList']['result']:
            r = r['resultList']['result'][0]
            if r['pubType'] == 'preprint':
                ppr = r['id']
        return ppr


    def generate_xml_file(self):
        ''' Build and write the XML "Link" file with the PGP Publication information. '''
        # Add PGS Citation
        title = 'Link to the Polygenic Score (PGS) Catalog resource'
        url = self.pgs_url
        source = 'MED'
        pmid = constants.PGS_PUBLICATIONS[-1]['PMID']  # to be restored with constants.CITATION when preprint gets published
        self.create_xml_link(title,url,source,pmid)

        # Add PGS Publications
        for publication in self.publications:
            id = publication.id
            url = self.link_root+id

            if publication.PMID:
                record_id = publication.PMID
                record_source = 'MED'
            else:
                ppr = None
                if publication.doi:
                    ppr = self.get_ppr(publication.doi)
                if ppr:
                    record_id = ppr
                    record_source = 'PPR'
                    self.pgp_with_ppr.append(id+': '+ppr)
                else:
                    extra = 'no DOI'
                    if publication.doi:
                        extra = 'has DOI'
                    print(f'> Can\'t find PubMed ID for the publication {id} - {extra}')
                    self.missing_links.append(id)
                    continue

            self.create_xml_link(id,url,record_source,record_id)

            # Create a new XML file from the XML document
            tree = ET.ElementTree(self.xml_document)
            tree.write(self.filename, encoding='utf-8', xml_declaration=True, pretty_print=True)


    def create_xml_link(self,id,url,record_source,record_id):
        ''' Generate a XML "Link" node. '''
        # New Link node
        xml_link = ET.SubElement(self.xml_document, 'link')
        xml_link.set('providerId', self.provider_id)

        # New Resource node
        xml_resource = ET.SubElement(xml_link, 'resource')
        xml_resource_title = ET.SubElement(xml_resource, 'title')
        xml_resource_url = ET.SubElement(xml_resource, 'url')
        xml_resource_title.text = id
        xml_resource_url.text = url

        # New Record node
        xml_record = ET.SubElement(xml_link, 'record')
        xml_record_source = ET.SubElement(xml_record, 'source')
        xml_record_id = ET.SubElement(xml_record, 'id')
        xml_record_source.text = record_source
        xml_record_id.text = str(record_id)


    def print_xml_report(self):
        ''' Print the report of the generated XML file '''

        # Display list of entry with a PPR ID (pre-prints)
        pgp_with_ppr_count = len(self.pgp_with_ppr)
        print("\n# Pre-prints with PPR links: "+str(pgp_with_ppr_count))
        for entry in self.pgp_with_ppr:
            print("- "+entry)

        # Display if there were some missing Publication (not having PubMed IDs)
        missing_links_count = len(self.missing_links)
        print("\n# Missing links: "+str(missing_links_count))
        for pgp_id in self.missing_links:
            print("- "+pgp_id)

        # Check the generated file
        if os.path.isfile(self.filename):
            filesize = os.stat(self.filename).st_size
            # Empty file
            if filesize == 0:
                print(f'\n/!\ ERROR: Linkage XML file ({self.filename}) is empty!')
            # Count discrepancies
            else:
                count_links = -1 # Remove PGS Citation entry from count
                xml_file = open(self.filename, "r")
                for line in xml_file:
                    if re.search('<link ', line):
                        count_links += 1
                xml_file.close()
                count_pub = len(self.publications)
                if count_links != count_pub:
                    print(f'\n/!\ ERROR: Number of entries between the fetched Publications from the database and the XML file differs ({count_links}/{count_pub})')
        else:
            print(f'\n/!\ ERROR: Linkage XML file "{self.filename}" doesn\'t exist!')
        print("\n")


################################################################################

def run():

    xml_link = EuropePMCLinkage()

    # Fetch data and generate XML file
    xml_link.generate_xml_file()

    # Print the report of the generated XML file
    xml_link.print_xml_report()
