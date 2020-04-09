@echo off
setlocal
set /a default.len=64

call :%*
goto :eof

:line
if "%*"=="" call :line.underscore && goto :eof
call :line.%* && goto :eof

:line.single
:line.dash
echo ---------------------------------------------------------------- && goto :eof

:line.double
:line.doubledash
echo ================================================================ && goto :eof

:line.lower
:line.under
:line.underscore
echo ________________________________________________________________ && goto :eof

:line.wave
:line.tilde
echo ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ && goto :eof

:line.dot
echo ................................................................ && goto :eof

:line.char
setlocal
call :line.char.multiply %~1 8 8
goto :eof

:line.char.multiply
setlocal
set /a i=0
call :line.char.add %~1 %~2 >nul
:line.char.multiply.loop
set s=%s%%_%
set /a i=i+1
if %i%==%~3 (
endlocal & set _=%s%
echo %s%
goto :eof) else goto :line.char.multiply.loop

:line.char.add
setlocal
set /a i=0
if "%~2"=="" (set /a len=default.len) else set /a len=%~2
:line.char.add.loop
set s=%s%%~1
set /a i=i+1
if %i%==%len% (
endlocal & set _=%s%
echo %s%
goto :eof) else goto :line.char.add.loop