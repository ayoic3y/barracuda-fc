@echo off
chcp 65001 >nul
title Peresborka saita FK Barrakuda
cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
  echo.
  echo Python ne naiden.
  echo Ustanovite ego s python.org i pri ustanovke otmette "Add python.exe to PATH".
  echo.
  pause
  exit /b 1
)

echo Peresbirau sait...
python _src\generate.py

if errorlevel 1 (
  echo.
  echo Sborka ne udalas. Chashche vsego prichina - propushchennaya zapyataya
  echo ili kavychka v fajle _src\data.py (smotrite tekst oshibki vyshe).
  echo.
  pause
  exit /b 1
)

echo.
echo Gotovo. Otkryvau sait v brauzere...
start "" "barracuda-fc\index.html"
pause
