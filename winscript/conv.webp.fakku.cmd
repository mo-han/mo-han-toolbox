@echo off
setlocal

call :subroutine

:subroutine
set /a max=1000*600
set q.min=40
for /d %%i in (*) do conv.webp.infolder "%%i"
for /d %%i in (*) do delete.nonwebp "%%i"
goto :eof
