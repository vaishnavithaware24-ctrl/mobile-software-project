@echo off
start "Backend" cmd /k "cd /d %~dp0backend && venv\Scripts\activate && python manage.py runserver"
start "Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"
timeout /t 6 >nul
start http://localhost:5173