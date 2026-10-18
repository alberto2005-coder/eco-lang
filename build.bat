@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Compilando eco

set "PY=py"
py -V >nul 2>nul || set "PY=python"
%PY% -V >nul 2>nul || (
    echo.
    echo  [FALTA] No encontre Python en tu equipo.
    echo  Descargalo desde  https://www.python.org/downloads/
    echo  y marca la casilla "Add Python to PATH" al instalar.
    echo.
    pause
    exit /b 1
)

%PY% -m PyInstaller --version >nul 2>nul || (
    echo  Instalando PyInstaller...
    %PY% -m pip install pyinstaller --disable-pip-version-check
)

echo  [1/3] Compilando dist\eco.exe ...
%PY% -m PyInstaller --onefile --name eco --distpath dist --workpath build ^
    --specpath build --clean --noconfirm main.py >nul
if errorlevel 1 goto fallo

echo  [2/3] Compilando dist\eco-ide.exe ...
%PY% -m PyInstaller --onefile --windowed --name eco-ide ^
    --add-data "%~dp0ejemplos;ejemplos" --distpath dist --workpath build ^
    --specpath build --clean --noconfirm ide.py >nul
if errorlevel 1 goto fallo

echo  [3/3] Compilando el instalador ...
set "ISCC="
if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"
if exist "%ProgramFiles(x86)%\Inno Setup 7\ISCC.exe" set "ISCC=%ProgramFiles(x86)%\Inno Setup 7\ISCC.exe"
if exist "%ProgramFiles%\Inno Setup 7\ISCC.exe" set "ISCC=%ProgramFiles%\Inno Setup 7\ISCC.exe"
if not defined ISCC for %%I in (ISCC.exe) do if not "%%~$PATH:I"=="" set "ISCC=%%~$PATH:I"
if not defined ISCC goto sin_inno
echo       usando: %ISCC%
"%ISCC%" /Qp instalador.iss
if errorlevel 1 (
    echo  [ERROR] ISCC devolvio un error: revisa instalador.iss
    set "SIN_INSTALADOR=1"
)
goto fin_inno
:sin_inno
echo  [AVISO] No encontre Inno Setup 6 ni 7: se omite dist\eco-setup.exe
:fin_inno

echo.
if defined SIN_INSTALADOR echo  [AVISO] El instalador NO se genero (los .exe estan bien).
if exist "dist\eco.exe" if exist "dist\eco-ide.exe" (
    echo  OK:  dist\eco.exe, dist\eco-ide.exe
    if exist "dist\eco-setup.exe" if not defined SIN_INSTALADOR echo        dist\eco-setup.exe
) else (
    echo  Hubo un error en la compilacion.
)
echo.
pause
exit /b 0

:fallo
echo.
echo  [ERROR] La compilacion fallo.
echo  Casi siempre es porque hay un eco.exe o un eco-ide.exe en marcha:
echo  cierra el IDE, las ventanas de eco, y vuelve a ejecutar build.bat.
echo.
pause
exit /b 1
