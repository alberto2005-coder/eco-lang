@echo off
chcp 65001 >nul
cd /d "%~dp0"
title eco IDE

rem ------------------------------------------------------------------
rem Arranca el IDE de escritorio: primero el .exe compilado, si no con
rem el intérprete de Python.
rem ------------------------------------------------------------------
if exist "dist\eco-ide.exe" (
    start "" "dist\eco-ide.exe" %*
    exit /b 0
)

set "PY=py"
py -V >nul 2>nul || set "PY=python"
%PY% -V >nul 2>nul || (
    echo.
    echo  ================================================
    echo   FALTA EL INTERPRETE
    echo  ================================================
    echo   Este IDE necesita Python para arrancar desde la fuente.
    echo   Descargalo aqui:  https://www.python.org/downloads/
    echo   ^(marca "Add Python to PATH" durante la instalacion^)
    echo.
    echo   Si solo quieres ejecutar programas .eco, no hace falta:
    echo   usa  dist\eco.exe  como se usa node.
    echo   O instala dist\eco-setup.exe
    echo  ================================================
    echo.
    pause
    exit /b 1
)

%PY% ide.py %*
exit /b 0
