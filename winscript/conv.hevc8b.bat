@echo off
setlocal
set ffmpegargs=-c:v hevc
set encodedtag=.__source__

if defined args set ffmpegargs=%ffmpegargs% %args%
call :check_hevc8b "%~n1"
if %hevc8b%==1 goto :eof
call :check_encoded "%~n1"
if %encoded%==1 goto :eof
title %args% %1
ffmpeg -i %1 %ffmpegargs% "%~n1.hevc8b%~x1" && rename %1 "%~n1%encodedtag%%~x1" || pause
goto :eof

:check_hevc8b
if "%~x1"==".hevc8b" (set hevc8b=1) else (set hevc8b=0)
goto :eof

:check_encoded
if "%~x1"=="%encodedtag%" (set encoded=1) else (set encoded=0)
goto :eof