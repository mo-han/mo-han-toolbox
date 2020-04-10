@echo off
setlocal

set title=%~nx0
if not "%~1"=="" pushd %1
call :folder
if not "%~1"=="" popd
goto :eof

:folder
setlocal
for /d %%i in (*) do (
call drawincmd line double
echo %%i
title %title% %%i
pushd "%%~i"
call :infolder "%%~i"
popd
)
call drawincmd line double
for /d %%i in (*) do call delete.nonwebp.infolder "%%~i"
goto :eof

:infolder
setlocal
for %%i in (*) do call :file "%%~i"
goto :eof

:file
setlocal
set /a ratio=67
set /a q.max=80
set /a q.min=50
if /i %~x1==.webp goto :eof
call wincmdlib returnback wrap.ffprobe w %1 >nul
set /a w=_
call wincmdlib returnback wrap.ffprobe h %1 >nul
set /a h=_
set /a res=w*h
set /a max=1024*512
:: 1280*1920=2457600  2457600*2=4915200  4915200*1.5=7372800
if %res% leq 2457600 (set /a max=1024*256) else (set /a max=1024*384)
if %res% gtr 4915200 (set /a max=1024*512 & set /a scale.min=85) else (set /a scale.min=100)
if %res% gtr 7372800 (set /a scale.min=70)
call conv.webp.smart %1
goto :eof
