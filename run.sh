python manage.py migrate
#gunicorn history4feed.wsgi:application --bind 0.0.0.0:8002 --reload
python manage.py runserver 0.0.0.0:8002