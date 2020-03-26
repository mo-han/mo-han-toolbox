@echo off
setlocal
set cookies=%locallib_usretc%\cookies.bilibili.txt
set workdir=%locallib_usrdl%
set tempdir=you-get.%random%%random%%random%

call :%*
goto :eof

:download
pushd %workdir%
you-get -c %cookies% %*
popd
goto :eof

:rename
pushd %workdir%
for %%i in ("%~1.*") do (
echo "%%~i" -^> "%~2%%~xi"
move /y "%%~i" "%~2%%~xi" >nul
)
popd
goto :eof

:d
if exist %1 (
for /f "delims=" %%i in (%1) do call :dlurl %%i
) else call :dlurl %*
goto :eof

:dlurl
call :id2url %*
call :bilidl_worker %url%
goto :eof

:bilidl_worker
bilidl_worker.py %* && timeout /t 3 && goto :eof
goto :bilidl_worker
goto :eof

:id2url
set id=%*
if %id:~,4%==http set url=%id%
if %id:~,2%==BV set url=https://b23.tv/%id%
if %id:~,2%==av set url=https://b23.tv/%id%
if %id:~,2%==AV set url=https://b23.tv/av%id:~2%
echo %url%
goto :eof
