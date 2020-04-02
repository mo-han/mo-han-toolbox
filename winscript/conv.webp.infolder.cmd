@echo off
setlocal
set /a default.max=1000*500
set /a default.th=70
set /a default.q.max=80
set /a default.q.min=default.q.max
set args.cwebp.common=-short
goto :bof
Dependencies:
    1. cwebp.exe
    2. cwebp-resizep.exe (modified version with a percentage resize option `-resizep`, used by a software called CbxConverter)
        http://tomeko.net/software/CbxConverter/
        http://tomeko.net/software/CbxConverter/bin/cwebp.c
    3. nircmdc.exe
        https://www.nirsoft.net/utils/nircmd.html
:bof
set tempprefix="%temp%"\cwebptemp%random%%random%%random%
set workdir="%~1"
%~2
if not defined max set /a max=default.max
if not defined th set /a th=default.th
if not defined q.max set /a q.max=default.q.max
if not defined q.min set /a q.min=default.q.min
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

call drawincmd.cmd line double
echo max=%max% th=%th% q=%q.max%...%q.min% %workdir%
pushd %workdir%
for %%i in (*) do if %%~xi==.webp (call :pass) else (call :convert "%%~i")
del %tempprefix%.* 2>nul
popd
goto :eof

:convert
setlocal
set /a q=q.max
call drawincmd.cmd line
echo %1
if %~x1==.jpg goto :convert.begin
if %~x1==.jpeg goto :convert.begin
if %~x1==.png goto :convert.begin
if %~x1==.bmp goto :convert.begin
goto :eof
:convert.begin
copy /y %1 %tempprefix%.i >nul
:convert.tempfile
title -max %max% -th %th% -q %q% %args.cwebp.common% %workdir%
cwebp %args.cwebp.common% -q %q% %tempprefix%.i -o %tempprefix%.o
call wincmdlib.cmd filesize %tempprefix%.i >nul
set /a sourcesize=_
call wincmdlib.cmd filesize %tempprefix%.o >nul
set /a webpsize=_
set /a ratio=100*webpsize/sourcesize
echo q=%q% compression: %ratio%%%
if %ratio% gtr %th% goto :reducequality
move /y %tempprefix%.o %1.webp >nul
call :resize.init "%~1.webp"
nircmdc clonefiletime %1 "%~1.webp"
goto :eof

:reducequality
if %ratio% leq %th% goto :eof
if %q% leq %q.min% echo Skip insufficient compression %ratio%%% && goto :eof
set /a q=q-10
goto :convert.tempfile

:resize.init
setlocal
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
echo resize=%scale%%%
copy /y %~n1 %tempprefix%.i >nul
:: %1 is such as `xxx.jpg.webp`, so %~n1 is `xxx.jpg`.
cwebp-resizep %args.cwebp.common% -q %q% -resizep %scale%%% %tempprefix%.i -o %tempprefix%.o
move /y %tempprefix%.o %1 >nul
if %~z1 gtr %max% (set /a scale=scale-5) else goto :eof
if %scale%==0 goto :eof
goto :resize.smaller

:pass
goto :eof