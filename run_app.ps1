# EcoAI Application Launcher for Windows PowerShell
Write-Host "==========================================================" -ForegroundColor Green
Write-Host "  EcoAI – Intelligent E-Waste Management System           " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Green

$pythonExe = "C:\Users\medis\AppData\Local\Python\pythoncore-3.14-64\python.exe"

if (-not (Test-Path $pythonExe)) {
    $pythonExe = "python"
}

Write-Host "[*] Using Python: $pythonExe" -ForegroundColor Yellow
Write-Host "[*] Starting production server on http://127.0.0.1:5000" -ForegroundColor Green
Write-Host "[*] Default Admin: admin / Admin@EcoAI2026" -ForegroundColor Cyan
Write-Host "[*] Demo Citizen:  demo_user / User@EcoAI2026" -ForegroundColor Cyan

& $pythonExe server_production.py
