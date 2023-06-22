import re


class GenericData():

    # Needed for parsing confidence intervals
    insquarebrackets = re.compile('\\[([^)]+)\\]')
    interval_format = r'^\-?\d+.?\d*\s\-\s\-?\d+.?\d*$'
    inparentheses = re.compile(r'\((.*)\)')
    # Non ascii symbols (unicode notation)
    non_ascii_chars = {
        '\u2009': ' ', # Thin Space
        '\u2013': '-', # En dash
        '\u2014': '-', # Em dash
        '\u2022': '-', # Bullet
        '\u2019': "'", # Right single quotation mark
        '\u201A': '',  # Single low-9 quotation mark
        '\uFEFF': ''   # byte order mark (BOM)
    }

    def __init__(self,spreadsheet_name='NA'):
        self.model = None
        self.spreadsheet_name = spreadsheet_name
        self.data = {}
        self.report = {'error': {}, 'warning': {}, 'import': {} }
        self.report_types = self.report.keys()

    def add_data(self, field, value):
        ''' Insert new data into the 'data' dictionary. '''
        if type(value) == str:
            value = value.strip()
            # Remove/replace some of the non-ascii characters
            value = self.replace_non_ascii_chars(field,value)
        self.data[field] = value


    def next_id_number(self, model):
        ''' Fetch the new primary key value. '''
        assigned = 1
        if len(model.objects.all()) != 0:
            assigned = model.objects.latest().pk + 1
        return assigned


    def replace_non_ascii_chars(self,field,value):
        """ Remove/replace some of the non-ascii characters """
        for char in self.non_ascii_chars.keys():
            if char in value:
                self.parsing_report_warning(f'Found non ascii character "{char}" for "{field}": "{value}"')
                value = value.replace(char, self.non_ascii_chars[char])
        return value


    def add_parsing_report(self, rtype, msg):
        """
        Store the reported error/warning.
        - rtype: type of report (e.g. error, warning)
        - msg: error message
        """
        if rtype in self.report_types:
            spreadsheet_name = self.spreadsheet_name
            if not spreadsheet_name in self.report[rtype]:
                self.report[rtype][spreadsheet_name] = set()
            self.report[rtype][spreadsheet_name].add(msg)
        else:
            print(f'ERROR: Can\'t find the report category "{rtype}"!')


    def parsing_report_error(self, msg):
        """
        Store the reported error.
        - msg: error message
        """
        self.add_parsing_report('error', msg)


    def parsing_report_warning(self, msg):
        """
        Store the reported warning.
        - msg: warning message
        """
        self.add_parsing_report('warning', msg)


    def parsing_report_error_import(self, msg):
        """
        Store the reported import error.
        - msg: import error message
        """
        self.add_parsing_report('import', 'error', msg)
