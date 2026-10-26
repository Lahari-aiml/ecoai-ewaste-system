@echo off
title EcoAI - Intelligent E-Waste Management System
echo ==========================================================
echo   EcoAI - Intelligent E-Waste Management System
echo ==========================================================

set PYTHON_EXE=C:\Users\medis\AppData\Local\Python\pythoncore-3.14-64\python.exe

if not exist "%PYTHON_EXE%" (
    set PYTHON_EXE=python
)

echo [*] Starting server on http://127.0.0.1:5000
echo [*] Admin Credentials: admin / Admin@EcoAI2026
echo [*] Demo User: demo_user / User@EcoAI2026

"%PYTHON_EXE%" server_production.py
pause
