@echo off
setlocal
goto :bof
:bof
for %%i in (%*) do (call :settag "%%~i" || pause)
goto :eof

:settag
setlocal
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
