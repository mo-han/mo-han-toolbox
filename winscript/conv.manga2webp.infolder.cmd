@echo off
setlocal

set title=%~nx0
%~2
if not "%~1"=="" pushd %1
call :folders
if not "%~1"=="" popd
goto :eof

:folders
setlocal
for /d %%i in (*) do (
    call drawincmd line double
    echo %%i
    title %title% %%i
    pushd "%%~i"
    call conv.manga2webp
    popd
    if not exist "%%~i"\FOLDER.TAG 7za a "%%~i.zip" "%%~i" -r && rd /s /q "%%~i"
)
call drawincmd line double
call fname.cbz.cmd
goto :eof

:infolder
setlocal
move .ehviewer 0.ehviewer.txt >nul 2>&1
move .thumb 0.thumb.jpg >nul 2>&1
if exist 0.thumb.jpg (call wincmdlib filesize 0.thumb.jpg >nul) else set _=0
if %_%==0 del 0.thumb.jpg >nul 2>&1
for %%i in (*) do call :file "%%~i"
goto :eof

:file
setlocal
set /a ratio=67
set /a q.max=80
set /a q.min=50
if /i %~x1==.gif (
    call conv.gif2mp4 "%~1"
    goto :eof
)
if /i %~x1==.mp4 goto :eof
if /i %~x1==.webm goto :eof
if /i %~x1==.webp goto :eof
if /i %~x1==.txt goto :eof
if /i %~x1==.tag goto :eof
if /i %~x1==.json goto :eof
call wincmdlib returnback wrap.ffprobe w %1 >nul
set /a w=_
call wincmdlib returnback wrap.ffprobe h %1 >nul
set /a h=_
set /a res=w*h
set /a max=1024*512
:: 1280*1920=2457600 _*2=4915200 _*1.5=7372800
if %res% leq 2457600 (set /a max=1024*256) else (set /a max=1024*384)
if %res% gtr 4915200 (set /a max=1024*512 & set /a scale.min=85) else (set /a scale.min=100)
if %res% gtr 7372800 (set /a scale.min=70)
call conv.pic2webp.smart %1
goto :eof
