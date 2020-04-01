@echo off
goto :bof
Draw ASCII art in console (cmd.exe).
:bof
setlocal

call :%*
goto :eof

:line
if "%*"=="" call :line.underscore && goto :eof
call :line.%* && goto :eof

:line.double
call :line.doubledash && goto :eof

:line.wave
call :line.tilde && goto :eof

:line.single
:line.dash
echo -------------------------------- && goto :eof

:line.doulbe
:line.doubledash
echo ================================ && goto :eof

:line.lower
:line.under
:line.underscore
echo ________________________________ && goto :eof

:line.tilde
echo ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ && goto :eof

:line.dot
echo ................................ && goto :eof
