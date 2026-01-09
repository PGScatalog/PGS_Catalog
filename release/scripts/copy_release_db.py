import os, re, subprocess
import psycopg


#=============#
#  Variables  #
#=============#

script_path = os.path.dirname(os.path.abspath(__file__))
filename = 'app.yaml'
filepath = f'{script_path}/../../{filename}'
db_new = 'pgs_db_new'
tmp_sql_dump = 'tmp_curation_dump.sql'
env_name = 'PGPASSWORD'
backed_up_password = None
db_settings = {}


#===============#
#  Main method  #
#===============#

def run():
    if not os.path.exists(filepath):
        print(f'Can\'t find the conf file {filepath}')
        exit(1)

    file = open(filepath, 'r')
    for line in file:
        line = line.strip(' \t\n')
        for type in ['HOST','NAME','USER','PORT_LOCAL','PASSWORD']:
            extract_setting(type, line)
    #print(db_settings)

    # DB connection
    conn = psycopg.connect(
        host=db_settings['host'],
        dbname=db_settings['name'],
        user=db_settings['user'],
        password=db_settings['password'],
        port=db_settings['port']
    )
    conn.autocommit = True
    set_password(db_settings['password'])


    # Drop existing DB
    cur = conn.cursor()
    print(f'\n# Drop existing database \'{db_new}\'')
    try:
        cur.execute(f'DROP DATABASE {db_new};')
        print(f'\t> Existing database {db_new} has been deleted')
    except psycopg.errors.InvalidCatalogName as e:
        print(f'\t> No pre-existing {db_new} has been found. Skip deletion.')
        print(f'\t> {e}')
    except:
        print(f'\t> No pre-existing {db_new} has been found. Skip deletion.')
    cur.close()
    conn.close()


    # Create new DB
    new_db_is_created = 0
    print(f'\n# Creation of the database \'{db_new}\'')
    try:
        cmd = ['createdb', '-h', db_settings['host'], '-p', db_settings['port'], '-U', db_settings['user'], db_new]
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        stderr = stderr.decode('utf-8')
        if stderr != '':
            print("Error: "+str(stderr))
        else:
            print(f'\t> Database \'{db_new}\' has been created')
            new_db_is_created = 1
    except psycopg.DatabaseError as e:
        print(f'\t> Error: can\'t create the database {db_new}.\n{e}')

    if not new_db_is_created:
        exit(1)


    # Dump Curation DB
    db_dump_created = 0
    print(f'\n# Dump the database \'{db_settings["name"]}\'')
    try:
        cmd = f'pg_dump -h {db_settings["host"]} -U {db_settings["user"]} --no-owner --no-acl -p {db_settings["port"]} {db_settings["name"]} > {tmp_sql_dump}'
        process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        stderr = stderr.decode('utf-8')
        if stderr != '':
            print("\t> Error: "+str(stderr))
        else:
            print(f'\t> Dump of the database \'{db_settings["name"]}\' has been created')
            db_dump_created = 1
    except psycopg.DatabaseError as e:
        print(f'\t> Error: can\'t dump the database {db_settings["name"]}.\n{e}')

    if not db_dump_created:
        exit(1)


    # Populate the new DB
    print(f'\n# Populate the database \'{db_new}\':')
    try:
        cmd = f'psql -h {db_settings["host"]} -U {db_settings["user"]} -p {db_settings["port"]} {db_new} < {tmp_sql_dump}'
        process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        stderr = stderr.decode('utf-8')
        if stderr != '':
            print("\t> Error: "+str(stderr))
        else:
            print(f'\t> SUCCESS: The database {db_new} has been populated')
            # Cleanup
            cleanup_process = subprocess.Popen(f'rm -f {tmp_sql_dump}', shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout_c, stderr_c = cleanup_process.communicate()
            stderr_c = stderr_c.decode('utf-8')
            if stderr_c != '':
                print("\t> Error: "+str(stderr_c))
            else:
                print(f'\t> The dump file \'{tmp_sql_dump}\' has been removed')
    except psycopg.DatabaseError as e:
        print(f'\t> Error: can\'t populate the database {db_new}.\n{e}')

    reset_password()


#=================#
#  Other methods  #
#=================#

def extract_setting(type,line):
    """ Extract DB connection settings from the app.yaml file """
    global db_settings
    type_label = type.split('_')[0].lower()
    if not type_label in db_settings.keys():
        if re.search(f'^\s*DATABASE_{type}\:', line):
            line_content = line.split(':')
            value = line_content[1].strip(' \'"')
            if value.startswith('/cloudsql/') and type=="HOST":
                value = 'localhost'
            db_settings[type_label] = value


def set_password(password):
    """ Save the PostgreSQL password in a temporary environment variable, using os.putenv() """
    global env_name, backed_up_password
    if env_name in os.environ:
        backed_up_password = os.environ[env_name]
    os.putenv(env_name, password)


def reset_password():
    """
    Reset the password in the environment variable 'PGPASSWORD' as an extra safety mesure,
    even though os.putenv() should assign it just for the running script.
    """
    global env_name, backed_up_password
    if backed_up_password:
        os.putenv(env_name, backed_up_password)
    else:
        if env_name in  os.environ:
            del os.environ[env_name]
