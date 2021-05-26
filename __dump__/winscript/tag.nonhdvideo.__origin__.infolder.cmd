@echo off
setlocal
set /a const.nonhdres=960*540
set tag.origin=.__origin__
set tag.hevc8b=.hevc8b

if not "%~1"=="" pushd "%~1"
call fname.spechar.convert *
for %%i in (*) do call :tag "%%~i"
call fname.spechar.revert *
if not "%~1"=="" popd
goto :eof

:tag
if /i %~x1==.mp4 goto :tag.video
if /i %~x1==.flv goto :tag.video
if /i %~x1==.mkv goto :tag.video
if /i %~x1==.m4v goto :tag.video
if /i %~x1==.mov goto :tag.video
if /i %~x1==.webm goto :tag.video
goto :eof
:tag.video
set _=%~n1
if "%_:~-11%"=="%tag.origin%" echo # skip %1 && goto :eof
if "%_:~-7%"=="%tag.hevc8b%" echo # skip %1 && goto :eof
call wincmdlib returnback wrap.ffprobe res %1>nul
echo %_% %1
set /a res=%_%
if %res% lss %const.nonhdres% rename %1 "%~n1.__origin__%~x1" && echo * "%~1" ^> "%~n1.__origin__%~x1"
goto :eof
