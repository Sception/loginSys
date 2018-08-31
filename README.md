# loginSys
A login registration system that based on Django. 

## platform
* windows 10
* django 1.10
* python 3.5.2

## Start

``` bash
# install dependencies
pip install -r requirements.txt

# config settings.py
Update the configuration file（settings.py）for what you want.For example,the database config and the email 
config and so on.

# create records and data tables
python manage.py makemigrations login
python manage.py mikemigrate

# build for project
python manage.py runserver

```
