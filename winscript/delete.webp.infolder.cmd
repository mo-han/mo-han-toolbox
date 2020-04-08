@echo off
setlocal
pushd "%~1"
for %%i in (*.webp) do call :delete_webp_twin "%%~i"
popd

:delete_webp_twin
if not exist "%~n1" goto :eof
del "%~1"
goto :eof
