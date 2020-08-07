@echo off
setlocal

if %~x1==.mp4 goto :eof
set _localargs=%*
call set _localargs=%%_localargs:*%1=%%
if defined _localargs set _localargs=%_localargs:* =%
ffmpeg -i %1 -codec copy %_localargs% "%~dp1%~n1.mp4"