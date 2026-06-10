@echo off
echo Creating logs directory...
mkdir logs 2>nul

echo Creating .gitkeep file...
type nul > logs\.gitkeep

echo Fixing permissions...
icacls logs /grant "%USERNAME%:(OI)(CI)F" /T /Q

echo Logging directory created successfully!
echo.
echo You can now run:
echo python manage.py check
echo python manage.py migrate
echo python manage.py runserver

pause