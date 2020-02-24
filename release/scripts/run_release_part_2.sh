#!/bin/sh



python ../../manage.py dumpdata --exclude auth.permission --exclude contenttypes > pgs_datadump.json

# New DB
$NEW_DB = 'new'
python manage.py flush --database=${NEW_DB}
python manage.py makemigrations --database=${NEW_DB}
python manage.py migrate --database=${NEW_DB}
python manage.py loaddata data.json --database=${NEW_DB}
