import glob
import json
import tempfile
import os.path
from pathlib import Path

from js import outputFileName
# from pgscatalog.validate.cli.validate_scorefile import validate_scorefile
from pgscatalog.validate.cli.validate_cli import _run_validator


# local file system is mounted in /data
#input_path = Path("/data") / outputFileName

response = ''
error = None

try:

    # At the moment the results of score validation are stored in individual log files in log_dir
    with tempfile.TemporaryDirectory() as log_dir:

        filenames = []
        if outputFileName:
            filename = str(Path("/data") / outputFileName)
            if not os.path.exists(filename):
                raise FileNotFoundError(filename)
            filenames.append(filename)
        else:
            for score_file in glob.glob("/data/*"):
                filenames.append(score_file)

        # Unconventional use of private functions but temporary
        for filename in filenames:
            _run_validator(filename, Path(log_dir), None, False, False)

        # Getting the validation results from the log files
        for log_file in glob.glob(str(log_dir)+'/*_log.txt'):
            file_name = log_file.split('/')[-1].removesuffix('_log.txt')
            with open(log_file, 'r') as f:
                content = f.read()
                response = response + file_name + ":\n"
                response = response + content + "\n"

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
