:: yt-dl.bat
:: Mo Han <zmhungrown@gmail.com>
:: @ ytdl.worker.bat

@echo off
setlocal
call u_var.bat
set proxy=%u_autoproxy%
rem set proxy=%u_proxy%
pushd "%u_dl%"

set default=false
set worker=start "" cmd /c "ytdl.worker.bat || pause"
if "%1"=="m" goto :push_default
if "%1"=="w" goto :push_default
if "%1"=="b" goto :push_default
if "%1"=="j" goto :push_default
if "%1"=="n" goto :push_default

:pop_default
set "args=%*"
if "%1"=="" (
goto :i_main_loop
) else (
call set "url=%%args:*%default% =%%"
%worker%
popd
goto :eof
)

:push_default
set default=%1
if %default%==n (
set worker=call ytdl.worker.bat
) else (
set worker=start /min "" cmd /c "ytdl.worker.bat || pause"
)
shift
goto :pop_default

:i_main_loop
set url=
echo INPUT URL TO DOWNLOAD ([q] QUIT):
set /p url=#URL: 
if "%url%"=="q" (
  popd
  goto :eof
)
if not "%url%"=="" (
  %worker%
)
goto :i_main_loop

:: Changelog
:: [0.2] - 2017-12-12
:: + Three possible options: `m`, `w`, and `b`
:: 170620
:: + New param `d` for "automatically select default" (will not prompt for format).
:: 170430
:: + One-shot downloading with url provided as param.
:: 160906
::  [*] set _proxy=%u_proxy%