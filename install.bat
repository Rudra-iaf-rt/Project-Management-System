@echo off
echo Creating virtual environment...
python -m venv venv

echo Activating virtual environment...
call venv\Scripts\activate

echo Upgrading pip...
python -m pip install --upgrade pip

echo Installing Django and core packages...
pip install Django==4.2.11
pip install djangorestframework==3.15.1
pip install djangorestframework-simplejwt==5.3.1
pip install django-cors-headers==4.3.1
pip install django-filter==24.2
pip install psycopg2-binary==2.9.9
pip install python-dotenv==1.0.1
pip install Pillow==10.2.0

echo Installing WebSocket packages...
pip install channels==4.1.0
pip install channels-redis==4.2.0

echo Installing Celery (Optional - comment out if not needed)...
pip install celery==5.3.6
pip install django-celery-beat==2.6.0
pip install redis==5.0.1

echo Installing utility packages...
pip install openpyxl==3.1.2
pip install reportlab==4.1.0
pip install django-import-export==4.0.0

echo Installation complete!
echo.
echo Next steps:
echo 1. Create .env file with your database credentials
echo 2. Run: python manage.py makemigrations
echo 3. Run: python manage.py migrate
echo 4. Run: python manage.py createsuperuser
echo 5. Run: daphne -p 8000 pms.asgi:application
pause