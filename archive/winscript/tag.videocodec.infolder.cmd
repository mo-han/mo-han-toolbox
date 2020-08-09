@echo off
setlocal
goto :bof
:bof
if not "%~1"=="" set (flag.infolder=%1) else set flag.infolder=
if defined flag.infolder pushd %flag.infolder%
for %%i in (*) do (call :tag "%%~i" || pause)
if defined flag.infolder popd

:tag
setlocal
if "%~x1"=="" goto :eof
if /i %~x1==.mp4 goto :tag.run
if /i %~x1==.mkv goto :tag.run
if /i %~x1==.m4v goto :tag.run
if /i %~x1==.flv goto :tag.run
if /i %~x1==.mov goto :tag.run
echo # %1
goto :eof
:tag.run
call wincmdlib returnback videoinfo vc %~s1 >nul
set vc=%_%
if %vc%==h264 echo Skip H264 video: %1 && goto :eof
call wincmdlib returnback videoinfo vprofile %~s1 >nul
set vp=%_%
set /a bit=%vp:~-2%
if %bit%==0 set bit=8
set tag=.%vc%%bit%b
call wincmdlib fileextension "%~n1" >nul
if defined _ set oldtag=%_%
if "%oldtag%"=="%tag%" echo Skip tagged file: %1 && goto :eof
echo %1 -^> "%~n1%tag%%~x1%"
rename %1 "%~n1.%vc%%bit%b%~x1%"
goto :eof
