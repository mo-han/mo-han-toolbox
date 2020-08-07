@echo off
setlocal
echo %~nx0 %1
pushd "%~1"
for %%i in (*) do call :save_only_webp "%%~i"
popd
goto :eof

:save_only_webp
if not exist "%~1.webp" goto :eof
if not %~x1==.webp del "%~1"
goto :eof
