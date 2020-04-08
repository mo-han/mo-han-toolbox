@echo off
setlocal

if not "%~1"=="" pushd %1
call :folder
if not "%~1"=="" popd
goto :eof

:folder
setlocal
for /d %%i in (*) do (
call drawincmd line double
echo %%i
pushd "%%~i"
call :infolder "%%~i"
popd
)
for /d %%i in (*) do call delete.nonwebp.infolder "%%~i"
goto :eof

:infolder
setlocal
for %%i in (*) do call :file "%%~i"
goto :eof


:file
setlocal
set /a max=1024*768
set /a th=20
set /a scale.min=75
set /a q.max=80
set /a q.min=70
call conv.webp.lower "%~1"
if exist "%~1.webp" goto :eof
set /a max=1024*512
set /a th=40
set /a scale.min=75
set /a q.max=80
set /a q.min=50
call conv.webp.lower "%~1"
if exist "%~1.webp" goto :eof
set /a max=1024*512
set /a th=60
set /a scale.min=75
set /a q.max=60
set /a q.min=50
call conv.webp.lower "%~1"
if exist "%~1.webp" goto :eof
set /a max=1024*768
set /a th=60
set /a scale.min=75
set /a q.max=60
set /a q.min=50
call conv.webp.lower "%~1"
if exist "%~1.webp" goto :eof
set /a max=1024*768
set /a th=60
set /a scale.min=50
set /a q.max=60
set /a q.min=50
call conv.webp.lower "%~1"
if exist "%~1.webp" goto :eof
goto :eof
