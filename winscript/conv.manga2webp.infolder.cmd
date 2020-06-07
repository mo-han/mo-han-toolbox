@echo off
setlocal

set title=%~nx0
%~2
if not "%~1"=="" pushd %1
call fname.spechar.convert -aF *
call :folders
call fname.spechar.revert -aF *
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
