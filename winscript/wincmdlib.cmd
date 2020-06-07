@echo off
setlocal

if "%~1"=="" goto :help
endlocal & call :%*
goto :eof

:help
cd /d "%~dp0"
where grep >nul 2>&1
if not errorlevel 1 (
    call 
)
goto :eof

:test
setlocal
set x=1
set y.1=2
if x lss y.1 echo yes
goto :eof

:procprio
:processpriority
setlocal
wmic process where name=%1 CALL setpriority %2
goto :eof

:infoldercall
setlocal
call :lstriparg1 %*
if "%~1"=="" (
    call %*
) else (
    pushd %1
    call %_%
    popd
)
goto :eof

:mergelines
:: %~0 <"'command'"> <EOL>
setlocal enabledelayedexpansion
for /f "delims=" %%i in (%~1) do (
    set line=!line!%~2%%i
)
endlocal enabledelayedexpansion & call :return "%line%"
goto :eof

:lstriparg1
setlocal
set args=%*
call set args=%%args:*%1=%%
if defined args set args=%args:* =%
endlocal & call :return %args% >nul
goto :eof

:returnback
:lastline
:endof
setlocal
set "cmd=%*"
for /f "delims=" %%i in ('%cmd%') do set line=%%i
endlocal & call :return %line%
goto :eof

:lowercase
setlocal
set x=%~1
for %%i in ("A=a" "B=b" "C=c" "D=d" "E=e" "F=f" "G=g" "H=h" "I=i" "J=j" "K=k" "L=l" "M=m" "N=n" "O=o" "P=p" "Q=q" "R=r" "S=s" "T=t" "U=u" "V=v" "W=w" "X=x" "Y=y" "Z=z") do call set x=%%x:%%~i%%
endlocal & call :return %x%
goto :eof

:filesize
setlocal
endlocal & call :return %~z1
goto :eof

:filename
setlocal
endlocal & call :return %~n1
goto :eof

:basename
setlocal
endlocal & call :return %~n1%~x1
goto :eof

:dirpath
setlocal
endlocal & call :return %~dp1
goto :eof

:realpath
:fullpath
setlocal
endlocal & call :return %~f1
goto :eof

:fileext
:fileextension
setlocal
endlocal & call :return %~x1
goto :eof

:return
setlocal
echo %*
endlocal & set _=%*
goto :eof

:echocall
setlocal
echo %*
call %*
goto :eof

:loopmode
setlocal
if "%~1"=="-h" (
    echo set env_var: loopmode.callee
    echo set optional env_var: loopmode.{title^|header^|prompt^|caller}
    goto :eof
)
if defined loopmode.title title %loopmode.title% (%~0)
if not defined loopmode.caller set loopmode.caller=start "" /min cmd /c
if defined loopmode.header echo # %loopmode.header%
echo # %loopmode.caller% %loopmode.callee% ^<^<^<
echo #
:loopmode.loop
set input=
set /p "input=%loopmode.prompt%"
if not defined input goto :loopmode.loop
if "%input:"=%"=="q" goto :eof
if "%input:"=%"=="quit" goto :eof
%loopmode.caller% %loopmode.callee% %input%
goto :loopmode.loop
