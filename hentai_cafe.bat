@echo off
setlocal
call u_var.bat
call .ve35-win32\Scripts\activate.bat
set "bin=%~dp0hentai_cafe.py"
title hentai_cafe.bat %u_dl%

if "%*"=="" (
goto :loop
) else (
%bin% %* || pause
goto :eof
)

:loop
set /p url="> "
if "%url%"=="q" goto :eof
pushd %u_dl%
start /min "%url%" cmd /c "%bin% %url% || pause"
popd
goto :loop
