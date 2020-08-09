@echo off
setlocal
set ffmpegargs=-c:v hevc -pix_fmt yuv420p
set tag.origin=.__origin__
set /a thres.hd=960*720

if not "%~2"=="" set args=%~2
if defined args set ffmpegargs=%ffmpegargs% %args%
call :check_hevc8b "%~n1"
if %hevc8b%==1 echo # skip %~n1 && goto :eof
call :check_encoded "%~n1"
if %encoded%==1 echo # skip %~n1 && goto :eof
title %args% %1
set ext=%~x1
if %ext%==.webm set ext=.mkv
if %ext%==.flv set ext=.mp4
call wincmdlib.cmd returnback wrap.ffprobe res "%~1" >nul
set /a ipix=%_%
if %ipix% lss %thres.hd% set ffmpegargs=%ffmpegargs% -crf 23
ffmpeg -i "%~1" %ffmpegargs% "%~dpn1.hevc8b%ext%" && rename "%~1" "%~n1%tag.origin%%~x1" || pause
goto :eof

:check_hevc8b
if "%~x1"==".hevc8b" (set hevc8b=1) else (set hevc8b=0)
goto :eof

:check_encoded
if "%~x1"=="%tag.origin%" (set encoded=1) else (set encoded=0)
goto :eof