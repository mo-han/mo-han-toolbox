@echo off
setlocal

call :%*
goto :eof

:line
if "%*"=="" call :line.underscore && goto :eof
call :line.%* && goto :eof

:line.single
:line.dash
echo -------------------------------- && goto :eof

:line.double
:line.doubledash
echo ================================ && goto :eof

:line.lower
:line.under
:line.underscore
echo ________________________________ && goto :eof

:line.wave
:line.tilde
echo ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ && goto :eof

:line.dot
echo ................................ && goto :eof
