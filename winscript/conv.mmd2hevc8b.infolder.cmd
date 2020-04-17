@echo off
setlocal
set /a pixels.fhd=1920*800
set /a pixels.hd=1280*720

set workdir="%~1"
set _args=%*
call set _args=%%_args:*%1=%%
if defined _args set _args=%_args:* =%

pushd %workdir%
for %%i in (*.mp4) do call :smart_conv "%%~i"
for %%i in (*.webm) do call :smart_conv "%%~i"
for %%i in (*.mkv) do call :smart_conv "%%~i"
popd
pause
goto :eof

:smart_conv
call wincmdlib.cmd returnback wrap.ffprobe w %1 >nul
set /a iw=_
call wincmdlib.cmd returnback wrap.ffprobe h %1 >nul
set /a ih=_
set /a ipix=iw*ih
set /a rwh=10000*iw/ih
set /a rhw=10000*ih/iw
call drawincmd.cmd line lower
if %ipix% lss %pixels.hd% (
echo Skip non-HD video %1
title skip %1
goto :eof
)
if %rhw% lss 10000 set scale=-2:1080
if %rhw% lss 5625 set scale=1920:-2
if %rwh% lss 10000 set scale=1080:-2
if %rwh% lss 5625 set scale=-2:1920
if %ipix% geq %pixels.fhd% (
set args=-crf 23 %_args% -vf scale=%scale%
) else (
set args=-crf 20 %_args%
)
if %~x1==.webm set args=-c:a copy %args%
call conv.hevc8b.cmd %1
timeout /t 1
goto :eof