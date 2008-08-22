
GoFlow - A workflow engine for Django
-------------------------------------

1. Components:

- goflow: workflow django contrib

- leavedemo: goflow demo project



2. Requirements:

- Python 2.5

- Django 1.0 (SVN trunk)


3. Install instructions:


- cd leavedemo
  > create the database with command "python manage.py syncdb --noinput"
  > don't create the admin account, because
    leave demo data and all users required for playing with it will
    be created at this stage.
 
- superuser is "admin" with password "open"



4. Test instructions:

- run "python manage.py test" (with goflow in python path)

- run "python manage.py runserver" (with goflow in python path)

- admin interface: http://localhost:8000/leave/admin

- leave demo:      http://localhost:8000/leave/

