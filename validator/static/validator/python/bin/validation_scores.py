import glob
import json
import os.path
from pathlib import Path

# Variables taken from the context of the pyodide.runPythonAsync() call in validator/static/validator/python/validation_scores.js
from js import outputFileName, max_errors

# From the pgscatalog_validate wheel
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
        file_response = {"filename": os.path.basename(filename), "errors": []}
        for validation_error in validation.get_errors():
            file_response['errors'].append({
                "row": validation_error.row,
                "messages": list(map(lambda err: (f"[{err.attr}] " if err.attr else '') + err.msg, validation_error.errors))
            })
            if len(file_response['errors']) >= max_errors:
                file_response['errors'].append({
                    "row": None,
                    "messages": [f"Too many errors, stopping validation and showing only the first {max_errors} errors."]
                })
                break
        file_response['valid'] = len(file_response['errors']) == 0
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
