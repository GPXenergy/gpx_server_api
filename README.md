# GPX API

## Setup environment

requirements:
* Python 3.5+ installed
  * check with `$ python --version` or  `$ python3 --version`
* pip installed (python package manager)
  * check with `$ pip --version`
* Postgresql (10+) database wuth Postgis (2.2+) extension
  * Install postgres from [their download page](https://www.postgresql.org/download/) or cli package manager
  * Install postgis from [their download page](https://postgis.net/install/) or cli package manager


Setup local env
1. Create new virtual environment
   * `$ virtualenv -p python3 venv`
2. Activate environment
   * `$ source venv/bin/activate`
   * or `$ venv\Scripts\Activate` on windows machines
3. Install requirements
   * `(venv)$ pip install -r requirements.txt`


## Run application

Django has a few commands to make your life easy:
* Run development server
  * `(venv)$ python manage.py runserver`
* Create database migration files (after changing models)
  * `(venv)$ python manage.py makemigrations`
* Apply database migrations
  * `(venv)$ python manage.py migrate`
