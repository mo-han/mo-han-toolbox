:: yt-dl_worker.bat
:: Mo Han <zmhungrown@gmail.com>
:: @ yt-dl.bat, python.exe (v3), youtube-dl.exe

@echo off
setlocal
title "%url%"

set /a retry=0
set retry_max=3

if %url:~0,1%==[ ( if %url:~-1%==] ( set url=https://www.youtube.com/watch?v=%url:~1,-1% ))
set base_args_uploader=-o "%%(title)s [%%(id)s][%%(uploader)s].%%(ext)s" --yes-playlist "%url%"
rem set base_args_iwara=-o "%%(title)s [%%(id)s][%%(uploader)s][%%(creator)s][%%(uploader_id)s].%%(ext)s" --yes-playlist "%url%"
set base_args_iwara=-o "%%(title)s [%%(id)s].%%(ext)s" --yes-playlist "%url%"
set arial2_args=--external-downloader aria2c --external-downloader-args "-x8 -s8 -k 1M"
set arial2_proxy_args=--proxy=%proxy% %arial2_args%
rem set arial2_proxy_args=--proxy=%proxy% %arial2_args% --external-downloader-args "--all-proxy=%proxy% -x10 -s10"

set args=%arial2_proxy_args% %base_args_uploader%
echo "%url%" | findstr "sankakucomplex" > nul
if %errorlevel%==0 set args=%arial2_proxy_args% -o "%%(id)s.%%(ext)s" "%url%"
echo "%url%" | findstr "javdove.com" > nul
if %errorlevel%==0 set args=%arial2_proxy_args% -o "%%(title)s [javdove].%%(ext)s" "%url%"
echo "%url%" | findstr "iwara" > nul
rem if %errorlevel%==0 set args=--no-check-certificate %args%
if %errorlevel%==0 set args=%arial2_proxy_args% %base_args_iwara%
echo "%url%" | findstr "bilibili" > nul
if %errorlevel%==0 set args=%arial2_args% %base_args_uploader%
rem Append `--no-check-certificate` for YouTube. Have no idea but it works. And since it's just video data downloaded, there should be no security/privacy issue.
rem echo "%url%" | findstr "youtube youtu.be" > nul
rem if %errorlevel%==0 set args=--no-check-certificate %args%
echo %args%
echo --------------------------------

:prompt
set fmt=
echo [Q]uit, [B]est, [F]ormat list (Default), [Enter]=Default
echo [M] try mp4 1080p 60fps
echo [W] try webm 1440p 60fps
if %default%==false (set /p "fmt=> ") else (set fmt=%default%)
echo --------------------------------
rem youtube-dl.exe --get-filename -q %args%
rem echo --------------------------------
if not defined fmt set fmt=f
if "%fmt%"=="q" exit
if "%fmt%"=="f" goto :formats
if "%fmt%"=="b" set "fmt=bestvideo+bestaudio/best"
if "%fmt%"=="m" set "fmt=(mp4)[height<=1080][fps<=60]+(aac/m4a)/bestvideo+bestaudio/best"
if "%fmt%"=="w" set "fmt=(webm)[height<=1440][fps<=60]+(webm/opus/vorbis)/bestvideo+bestaudio/best"
set args=-f "%fmt%" %args%
goto :download

:download
echo %args%
youtube-dl.exe %args%
:: Success or failure? 
if errorlevel 1 (
  set /a retry+=1
  if %retry% lss %retry_max% goto :download
  set /p "_fin=Try again or [q]uit ? "
  if not defined _fin goto :download
  if not "%_fin%"=="q" goto :download
  if "%_fin%"=="q" goto :end
) else (
  echo --------------------------------
  echo DOWNLOAD SUCCESS
  timeout 3
  goto :end
)
goto :end

:formats
youtube-dl.exe -F %args%
echo --------------------------------
goto :prompt

:end
exit

:: Changelog
:: [0.3.3] - 2019-07-28
:: + youtube video id inside "[]" being detected and auto-completed.
:: [0.3.2] - 2019-07-20
:: * "[W] try webm 1080p 60fps" now trying 1440p instead of 1080p.
:: [0.3.1] - 2019-07-13
:: + sankakucomplex.com support.
:: * when error occurs, prompt "Try again or [q]uit?".
:: [0.3.0] - 2019-06-28
:: * a lot of minor changes been forgotten
:: [0.2.2] 2018-02-14
:: Append `--no-check-certificate` for YouTube. Reasons unknown, but the CRL url `http://pki.google.com/GIAG2.crl` in YouTube's SSL cert is blocked by GFW, which might be the cause.
:: [0.2.1] - 2018-02-08
:: add: `--external-downloader-args "--http-proxy=%proxy% -x10 -s10"` for aria2.
:: [0.2] - 2017-12-12
:: * Now default to [F]ormat list, pressing [Enter] will list all formats.
:: 171120
:: * Default to [W] webm/mp4 1080p 60fps bestaudio (Default)
:: 170620
:: + New param `d` for "automatically select default" (will not prompt for format).
:: 170517
:: * Format list is optional now. It would only be showed chosen.
:: 170514
:: * `arial2_args` & `arial2_proxy_args`
:: 170501
:: + Auto retry downloading for 3 times, then prompt for retrying.
:: 170414
::  [*] MP4 seems better (although bigger) than WebM on YouTube
::  [*] [1] mp4/webm 1080p 60fps bestaudio (default)
::  [*] [2] webm/mp4 1080p 60fps bestaudio
:: 170331
::  [+] Use aria2c to download Bilibili videos (to avoid speed limitation)
::  [+] New download choice: webm/mp4 [1]920 60fps bestaudio (default)
::  [+] New download choice: webm/mp4 [2]560 60fps bestaudio
::  [+] Wait 5 sec to exit after download
:: 170316
::  [+] Always get filename
::  [-] Remove `fn`
::  [+] Input `q` to quit
::  [+] After an error occurs, input `r` to re-download
:: 161113
::  [+] Input `fn` to get output file name
::  [+] Exam 'bilibili' in URL to disable proxy
::  [*] Use proxy by default
::  [*] Quote URL for stablity against special characters such as ampersand
:: 160916
::  [-] Remove `IF` block of proxy switching
::  [*] Always use proxy
:: 160906
::  [*] NOT useing proxy by default
::  [-] Remove `--no-playlist` option