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
set /a ratio=66
set /a q.max=80
set /a q.min=50
if /i %~x1==.webp goto :eof
call wincmdlib returnback wrap.ffprobe w %1 >nul
set /a w=_
call wincmdlib returnback wrap.ffprobe h %1 >nul
set /a h=_
set /a res=w*h
set /a max=1024*512
rem :: e-hentai 1280x
rem if %w% leq 1280 (if %h% leq 2560 set /a max=1024*256)
:: 2000x3000
if %res% leq 3000000 set /a max=1024*256
if %res% gtr 6000000 (set /a scale.min=70) else (set /a scale.min=100)
call conv.webp.smart %1
goto :eof
