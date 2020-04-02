@echo off
setlocal
set /a max=1000*600
set q.min=40

call :subroutine
goto :eof

:subroutine
for /d %%i in (*) do call conv.webp.infolder "%%~i"
for /d %%i in (*) do call delete.nonwebp "%%~i"
goto :eof
