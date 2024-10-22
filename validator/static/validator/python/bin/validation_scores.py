import glob
import json
import tempfile
import os.path
from pathlib import Path

from js import outputFileName
# from pgscatalog.validate.cli.validate_scorefile import validate_scorefile
from pgscatalog.validate.cli.validate_scorefile import _check_args, _validate_scorefile


# local file system is mounted in /data
#input_path = Path("/data") / outputFileName


class Args:
    dir: str
    log_dir: str
    t: str
    f: str
    score_dir: str
    check_filename: bool


response = ''
error = None

try:

    # At the moment the results of score validation are stored in individual log files in log_dir
    with tempfile.TemporaryDirectory() as log_dir:

        args = Args()
        args.t = 'formatted'
        args.check_filename = False
        args.dir = None
        args.f = None
        args.log_dir = Path(log_dir)
        args.score_dir = None

        if outputFileName:
            filename = str(Path("/data") / outputFileName)
            if not os.path.exists(filename):
                raise FileNotFoundError(filename)
            args.f = filename
        else:
            args.dir = str(Path("/data"))

        # Unconventional use of private functions but temporary
        _check_args(args)
        _validate_scorefile(args)

        # Getting the validation results from the log files
        for log_file in glob.glob(str(log_dir)+'/*_log.txt'):
            file_name = log_file.split('/')[-1].removesuffix('_log.txt')
            with open(log_file, 'r') as f:
                content = f.read()
                response = response + file_name + ":\n"
                response = response + content + "\n"

except FileNotFoundError as e:
    error = "Could not read input file. Is the selected file in the in the directory with granted rights?"
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
