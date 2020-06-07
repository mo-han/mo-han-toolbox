@echo off
setlocal
set cookies=%locallib_usretc%\cookies.bilibili.txt
set workdir=%locallib_usrdl%
set args=%*
if not defined args (
    set loopmode.title=%~nx0
    set loopmode.header=download from bilibili
    set loopmode.callee=bldl
    call wincmdlib loopmode
    goto :eof
)
if not defined root set root=%workdir%
pushd %root%
title bldl %*
bilidl_worker.py %* -c %cookies%
popd
goto :eof