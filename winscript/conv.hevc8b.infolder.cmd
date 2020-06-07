@echo off
setlocal

set workdir="%~1"
set args=%*
call set args=%%args:*%1=%%
if defined args set args=%args:* =%

pushd %workdir%
for %%i in (*.mp4) do call conv.hevc8b "%%~i"
for %%i in (*.mkv) do call conv.hevc8b "%%~i"
for %%i in (*.flv) do call conv.hevc8b "%%~i"
popd
goto :eof
