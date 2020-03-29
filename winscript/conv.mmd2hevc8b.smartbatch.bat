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
popd
pause
goto :eof

:smart_conv
set _file=%1
for /f %%i in ('videoinfo.bat _file') do set /a pixels=%%i
call draw.line.lower
if %pixels% lss %pixels.hd% (
echo Skip non-HD video %1
title skip %1
goto :eof
)
if %pixels% geq %pixels.fhd% (
set args=-crf 23 %_args%
) else (
set args=-crf 18 %_args%
)
call conv.hevc8b.bat %1
goto :eof