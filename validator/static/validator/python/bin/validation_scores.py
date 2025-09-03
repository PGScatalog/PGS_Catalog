import glob
import json
import os.path
from pathlib import Path

from js import outputFileName
from pgscatalog.validate.lib.validation import ScoringFileValidation

response = []
error = None

try:

    filenames = []
    if outputFileName:
        filename = str(Path("/data") / outputFileName)
        if not os.path.exists(filename):
            raise FileNotFoundError(filename)
        filenames.append(filename)
    else:
        for score_file in glob.glob("/data/*"):
            filenames.append(score_file)

    for filename in filenames:
        validation = ScoringFileValidation(filename, header=False)
        file_response = {"filename": os.path.basename(filename), "valid": not bool(validation.errors), "errors": []}
        for validation_error in validation.errors:
            file_response['errors'].append({
                "row": validation_error.row,
                "messages": list(map(lambda err: err['msg'], validation_error.error.errors()))
            })
        response.append(file_response)


except FileNotFoundError as e:
    error = "Could not read input file. Is the selected file in the directory with granted rights?"
except Exception as e:
    error = str(e)


data = {}
if error:
    data = {
        'status': 'error',
        'error': error
    }
else:
    data = {
        'status': 'success',
        'response': response
    }

json.dumps(data)  # Is returned by pyodide.runPythonAsync()
