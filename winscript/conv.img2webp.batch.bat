@echo off
setlocal
set /a default_max=1000*300
set /a default_th=70
set /a default_q=80
goto :bof
Dependencies:
    1. cwebp.exe
    2. cwebp-resizep.exe (modified version with a percentage resize option `-resizep`, used by a software called CbxConverter)
        http://tomeko.net/software/CbxConverter/
        http://tomeko.net/software/CbxConverter/bin/cwebp.c
    3. nircmdc.exe
        https://www.nirsoft.net/utils/nircmd.html
:bof
set /a q_min=50
set tempprefix="%temp%"\cwebptemp%random%%random%%random%
set workdir="%~1"
call %~2
if not defined max set max=%default_max%
if not defined th set th=%default_th%
if not defined q set q=%default_q%
set cwebp_common_args=-q %q% -short
set /a max1.25=%max% * 125 / 100
set /a max1.5=%max% * 15 / 10
set /a max2=%max% * 2
set /a max2.8=%max% * 28 / 10
set /a max4=%max% * 4
set /a max6.25=%max% * 625 /100
set /a max9=%max% * 9
set /a max16=%max% * 16
set /a max25=%max% * 25
set /a max100=%max% * 100

title maxsize:%max%Bytes thres:%th%%% %cwebp_common_args% %workdir%
call drawincmd.bat line double
echo Working Directory: %workdir%
echo Max webp size in bytes: %max%
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
if %ratio% geq %th%  echo Skip insufficient compression %ratio%%% && goto :eof
move /y %tempprefix%.o %1.webp >nul
call :resize.init "%~1.webp"
nircmdc clonefiletime %1 "%~1.webp"
goto :eof

:resize.init
if %~z1 gtr %max% (set scale=95) else goto :eof
if %~z1 gtr %max1.25% set scale=90
if %~z1 gtr %max1.5% set scale=80
if %~z1 gtr %max2% set scale=70
if %~z1 gtr %max2.8% set scale=60
if %~z1 gtr %max4% set scale=50
if %~z1 gtr %max6.25% set scale=40
if %~z1 gtr %max9% set scale=30
if %~z1 gtr %max16% set scale=25
if %~z1 gtr %max25% set scale=20
if %~z1 gtr %max100% set scale=10
:resize.smaller
echo Resize: %scale%%%
copy /y %~n1 %tempprefix%.i >nul
:: %1 is such as `xxx.jpg.webp`, so %~n1 is `xxx.jpg`.
cwebp-resizep %cwebp_common_args% -resizep %scale%%% %tempprefix%.i -o %tempprefix%.o
move /y %tempprefix%.o %1 >nul
if %~z1 gtr %max% (set /a scale=%scale% - 5) else goto :eof
if %scale%==0 goto :eof
goto :resize.smaller

:pass
goto :eof