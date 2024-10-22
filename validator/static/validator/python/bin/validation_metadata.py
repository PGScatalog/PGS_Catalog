import io
import js
import json
from pyodide.http import open_url
from validator.main_validator import PGSMetadataValidator
from validator.request.connector import Connector, UnknownError, NotFound, Logger

# Need a proxy for OLS as Pyodide causes a cross-origin issue with the OLS url
OLS_URL = "https://ols-proxy-dot-pgs-catalog.appspot.com/ols-proxy/efo/%s"

file = io.BytesIO(bytes(js.file_content))
file_name = js.file_name


class PyodideLogger(Logger):
    def debug(self, message, name):
        print(f'ERROR: {message}')


class PyodideConnector(Connector):
    def __init__(self):
        super().__init__(logger=PyodideLogger())

    def request(self, url, payload=None) -> dict:
        if payload:
            query = '&'.join([f"{k}={v}" for k, v in payload.items()])
            url = url + '?' + query
        query_result_io = open_url(url)
        query_result = query_result_io.read()

        result_json = json.loads(query_result)
        return result_json

    def get_efo_trait(self, efo_id) -> dict:
        url = OLS_URL % efo_id.replace('_', ':')
        response = self.request(url)
        # If not found the response should return 404.
        if '_embedded' in response and 'terms' in response['_embedded'] and len(response['_embedded']['terms']) == 1:
            return response['_embedded']['terms'][0]
        elif 'status' in response and response['status'] == 404:
            raise NotFound(message=response['error'], url=url)
        else:
            raise UnknownError(message="Unexpected response from URL: %s" % url, url=url)


def validate():
    metadata_validator = PGSMetadataValidator(file, False, PyodideConnector())
    metadata_validator.template_columns_schema_file = '/home/pyodide/TemplateColumns2Models.xlsx'
    metadata_validator.parse_spreadsheets()
    metadata_validator.parse_publication()
    metadata_validator.parse_scores()
    metadata_validator.parse_cohorts()
    metadata_validator.parse_performances()
    metadata_validator.parse_samples()
    metadata_validator.post_parsing_checks()

    report_text = 'No error'

    response = {}

    status = 'success'
    if metadata_validator.report['error']:
        status = 'failed'
        response['error'] = {}
        error_report = metadata_validator.report['error']
        for error_spreadsheet in error_report:
            response['error'][error_spreadsheet] = []
            for error_msg in error_report[error_spreadsheet]:
                error_entry = {'message': error_msg}
                if error_report[error_spreadsheet][error_msg][0] != None:
                    error_entry['lines'] = error_report[error_spreadsheet][error_msg]
                response['error'][error_spreadsheet].append(error_entry)

    if metadata_validator.report['warning']:
        response['warning'] = {}
        warning_report = metadata_validator.report['warning']
        for warning_spreadsheet in warning_report:
            response['warning'][warning_spreadsheet] = []
            for warning_msg in warning_report[warning_spreadsheet]:
                warning_entry = {'message': warning_msg}
                if warning_report[warning_spreadsheet][warning_msg][0] != None:
                    warning_entry['lines'] = warning_report[warning_spreadsheet][warning_msg]
                response['warning'][warning_spreadsheet].append(warning_entry)

    response['status'] = status
    return response


response = validate()

json.dumps(response)  # Is returned by pyodide.runPythonAsync()
