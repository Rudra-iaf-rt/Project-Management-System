@echo off
title PMS Server - Daphne with WebSockets
echo ========================================
echo Project Management System
echo Starting Daphne Server with WebSocket Support
echo ========================================
echo.
echo Server will run at: http://127.0.0.1:8000
echo WebSocket endpoint: ws://127.0.0.1:8000/ws/chat/1/
echo.
echo Press Ctrl+C to stop the server
echo ========================================
echo.

call venv\Scripts\activate
daphne -b 127.0.0.1 -p 8000 pms.asgi:application

pause
