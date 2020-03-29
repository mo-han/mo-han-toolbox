@echo off
goto :bof
Dependencies:
    1. cwebp.exe
    2. cwebp-resizep.exe (modified version with a percentage resize option `-resizep`, used by a software called CbxConverter)
        http://tomeko.net/software/CbxConverter/
        http://tomeko.net/software/CbxConverter/bin/cwebp.c
    3. nircmdc.exe
        https://www.nirsoft.net/utils/nircmd.html
:bof
setlocal
set /a default_maxsize=1000*400
set /a threshold=70
set tempprefix="%temp%"\cwebptemp%random%%random%%random%
set cwebp_common_args=-short -q 80
set workdir="%~1"
set /a maxsize=%2
if not defined maxsize set maxsize=%default_maxsize%
set /a maxsize1.25=%maxsize% * 125 / 100
set /a maxsize1.5=%maxsize% * 15 / 10
set /a maxsize2=%maxsize% * 2
set /a maxsize2.8=%maxsize% * 28 / 10
set /a maxsize4=%maxsize% * 4
set /a maxsize6.25=%maxsize% * 625 /100
set /a maxsize9=%maxsize% * 9
set /a maxsize16=%maxsize% * 16
set /a maxsize25=%maxsize% * 25
set /a maxsize100=%maxsize% * 100

title %maxsize% %cwebp_common_args% %workdir%
call drawincmd.bat line double
echo Working Directory: %workdir%
echo Max webp size in bytes: %maxsize%
pushd %workdir%
for %%i in (*) do if %%~xi==.webp (call :pass) else call :convert "%%~i"
del %tempprefix%.*
popd
call drawincmd.bat line double
echo Done
goto :eof

:convert
call drawincmd.bat line single
echo %1
if %~x1==.jpg goto :convert.begin
if %~x1==.jpeg goto :convert.begin
if %~x1==.png goto :convert.begin
if %~x1==.bmp goto :convert.begin
goto :eof
:convert.begin
copy /y %1 %tempprefix%.i >nul
cwebp %cwebp_common_args% %tempprefix%.i -o %tempprefix%.o
call cmdbatchlib.bat filesize %tempprefix%.i >nul
set /a sourcesize=_
call cmdbatchlib.bat filesize %tempprefix%.o >nul
set /a webpsize=_
set /a ratio=100*webpsize/sourcesize
if %ratio% geq %threshold%  echo Skip insufficient compression %ratio%%% && goto :eof
move /y %tempprefix%.o %1.webp >nul
call :resize.init "%~1.webp"
nircmdc clonefiletime %1 "%~1.webp"
goto :eof

:resize.init
if %~z1 gtr %maxsize% (set scale=95) else goto :eof
if %~z1 gtr %maxsize1.25% set scale=90
if %~z1 gtr %maxsize1.5% set scale=80
if %~z1 gtr %maxsize2% set scale=70
if %~z1 gtr %maxsize2.8% set scale=60
if %~z1 gtr %maxsize4% set scale=50
if %~z1 gtr %maxsize6.25% set scale=40
if %~z1 gtr %maxsize9% set scale=30
if %~z1 gtr %maxsize16% set scale=25
if %~z1 gtr %maxsize25% set scale=20
if %~z1 gtr %maxsize100% set scale=10
:resize.smaller
echo Resize: %scale%%%
copy /y %~n1 %tempprefix%.i >nul
:: %1 is such as `xxx.jpg.webp`, so %~n1 is `xxx.jpg`.
cwebp-resizep %cwebp_common_args% -resizep %scale%%% %tempprefix%.i -o %tempprefix%.o
move /y %tempprefix%.o %1 >nul
if %~z1 gtr %maxsize% (set /a scale=%scale% - 5) else goto :eof
if %scale%==0 goto :eof
goto :resize.smaller

:pass
goto :eof