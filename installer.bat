@echo off
rem Installation de "Mes outils" : verifie Python, installe les bibliotheques,
rem cree les raccourcis (Bureau + demarrage de Windows) et lance la bulle.
chcp 65001 >nul
setlocal
cd /d "%~dp0"
title Installation de Mes outils

set "PY="
if defined MES_OUTILS_PYTHON set PY="%MES_OUTILS_PYTHON:pythonw.exe=python.exe%"
if not defined PY (
  py -3 --version >nul 2>nul && set "PY=py -3"
)
if not defined PY (
  python --version >nul 2>nul && set "PY=python"
)
if not defined PY (
  echo.
  echo Python est introuvable sur ce PC.
  echo Installez Python 3.10 ou plus recent depuis python.org, en cochant
  echo "Add python.exe to PATH", puis relancez installer.bat.
  echo.
  start "" "https://www.python.org/downloads/windows/"
  pause
  exit /b 1
)

echo Python utilise :
%PY% --version
echo.
echo Installation des bibliotheques...
%PY% -m pip install --disable-pip-version-check -q -r requirements.txt
if errorlevel 1 (
  %PY% -m pip install --disable-pip-version-check -q --user -r requirements.txt
)
echo.
%PY% outil\installation.py --installer
if errorlevel 1 (
  echo.
  echo L'installation n'a pas abouti : voir le message ci-dessus.
  pause
  exit /b 1
)
%PY% outil\installation.py --lancer
echo.
pause
