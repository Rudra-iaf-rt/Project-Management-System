@echo off
echo ========================================
echo Fixing all import errors in PMS Project
echo ========================================
echo.

echo 1. Fixing apps/accounts/views.py...
powershell -Command "(Get-Content apps/accounts/views.py) -replace 'from apps.projects.models import Project, Task', 'from apps.projects.models import Project`nfrom apps.tasks.models import Task' | Set-Content apps/accounts/views.py"

echo 2. Fixing apps/reports/views.py...
powershell -Command "(Get-Content apps/reports/views.py) -replace 'from apps.projects.models import Project, Task', 'from apps.projects.models import Project`nfrom apps.tasks.models import Task' | Set-Content apps/reports/views.py"

echo 3. Creating missing __init__.py files...
if not exist apps\reports\__init__.py echo. > apps\reports\__init__.py
if not exist apps\chat\__init__.py echo. > apps\chat\__init__.py
if not exist apps\notifications\__init__.py echo. > apps\notifications\__init__.py

echo 4. Creating logs directory...
if not exist logs mkdir logs

echo.
echo ========================================
echo All fixes applied!
echo ========================================
echo.
echo Now run these commands:
echo python manage.py makemigrations
echo python manage.py migrate
echo python manage.py createsuperuser
echo python manage.py runserver
echo.
pause