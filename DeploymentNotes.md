# Notes re: deploying the catalog 
## Resources
<u>Django Official Deployment Docs</u>: https://docs.djangoproject.com/en/2.2/howto/deployment/

<u>Deploying django application to a production server</u>: [Part 1 (downloading the requirements)](https://medium.com/@_christopher/deploying-my-django-app-to-a-real-server-part-i-de78962e95ac), [Part 2 (setting up nginx/gnuicorn)](https://medium.com/@_christopher/deploying-my-django-app-to-a-real-server-part-ii-f0c277c338f4)

<u>This one uses a helper script `gunicorn_django`, but also shows how to set a config file</u>: https://www.digitalocean.com/community/tutorials/how-to-install-and-configure-django-with-postgres-nginx-and-gunicorn#step-nine-configure-gunicorn

<u>Mozilla tutorial</u>: https://developer.mozilla.org/en-US/docs/Learn/Server-side/Django/Deployment

### How to see it on a remote development server
*This only works with `debug = True` and NO allowedhosts* https://www.saltycrane.com/blog/2012/10/how-run-django-local-development-server-remote-machine-and-access-it-your-browser-your-local-machine-using-ssh-port-forwarding/

## Notes
- There was a problem with f-strings (e.g. `f'{self.var}'` instead of `f'{}'.format(self.var)` not being available in python 3.5, only in >3.6) - it was simplest to fix these 3 cases instead of changing python versions on the VM.

## Steps
1. Clone the git repository.\
`git clone https://github.com/smlmbrt/PGS_Catalog.git`
2. Download some required software.\
Currently pip/virtualenv/sqlite are not available: `sudo apt-get install python3.6 python3.6-pip python3.6-dev virtualenv sqlite3`
We'll need nginx to deploy static files (images/css, maybe: bulk downloads/PGS zip files): `sudo apt-get install nginx`
3. Set up the virtual environment.\
`virtualenv --python=python3 pgs_env`\
`source pgs_env/bin/activate`
4. Download critical python packages.\
`pip install Django==2.2.1 django-tables2==2.1.0`
5. Edit the settings.py document.\
-- Added `STATIC_ROOT=os.path.join(BASE_DIR, 'static/')` \
-- Changed to `debug = FALSE` \
-- edited allowed hosts `ALLOWED_HOSTS = ['localhost', '127.0.0.1']` 
6. To place the static files in the project home directory `python manage.py collectstatic`
7. Asumming we're going ahead with gnuicorn + nginx:\
`pip install gunicorn`
8. Following the digital ocean tutorial I set up a gunicorn_config.py file.
9. It needs to have a service file which I've created in the home dir
From the  home directory it can be run with `gunicorn -c gunicorn_config.py pgs_web.wsgi` and put in thebackground
10. The nginx config file is at: `/etc/nginx/sites-available/pgs_web.config` \
it is started with `sudo service nginx start`
 
## Server Setup Commands


## Add Cacheing?
https://docs.djangoproject.com/en/2.2/topics/cache/

## Getting the scores to the FTP 
1. Move the scores to the VM `scp *.gz pgs_adm@193.62.55.65:/home/pgs_adm/DB_SourceFiles/Scores/`
2. Login to the EBI SSH ligation server `ssh slambert@ligate.ebi.ac.uk -p 2244`
3. Get to the ftp server & enter password `c ebi-cli`
4. Change to the PGS Catalog's ftp location `cd /nfs/ftp/pub/databases/spot/pgs`
5. Copy files to the desired scoring file directory on the ftp server `scp pgs_adm@193.62.55.65:/home/pgs_adm/DB_SourceFiles/Scores/*.txt.gz .`