@echo off
rem Lance la bulle flottante "Mes outils" (sans fenetre noire).
rem Python utilise : pythonw du PATH, ou celui de la variable MES_OUTILS_PYTHON.
set "PY=pythonw"
if defined MES_OUTILS_PYTHON set "PY=%MES_OUTILS_PYTHON%"
start "" "%PY%" "%~dp0outil\bulle.py"
