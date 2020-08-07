@echo off
setlocal
set default.delimiter=.

set delimiter=%default.delimiter%
if "%~1"=="" (
    set loopmode.header=%~nx0
    set loopmode.caller=call
    set loopmode.callee=%~nx0
    call wincmdlib loopmode
    goto :eof
)
call :%*
goto :eof

:test
echo %~n1
goto :eof

:get
setlocal
:: get <filename> [set var...]
set fn=%~n1
call %~2
call set nohead=%%fn:*%delimiter%=%%
call set head=%%fn:%delimiter%%nohead%=%%
echo %head%
endlocal & set _=%head%
goto :eof

:max
setlocal
:: max [folder] [set var...]
if not "%~1"=="" pushd "%~1"
call %~2
setlocal enabledelayedexpansion
for %%i in (*) do (
    call :get "%%~i" >nul
    if not defined max set max=!_!
    if !_! gtr !max! set max=!_!
)
echo !max!
if not "%~1"=="" pushd "%~1"
goto :eof

:min
setlocal
:: min [folder] [set var...]
if not "%~1"=="" pushd "%~1"
call %~2
setlocal enabledelayedexpansion
for %%i in (*) do (
    call :get "%%~i" >nul
    if not defined min set min=!_!
    if !_! lss !min! set min=!_!
)
echo !min!
if not "%~1"=="" pushd "%~1"
goto :eof
