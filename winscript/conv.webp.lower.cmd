@echo off
setlocal
set /a default.max=1024*384
set /a default.th=70
set /a default.q.max=80
set /a default.q.min=default.q.max
set /a default.scale.min=5
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
call %~2
if not defined max set /a max=default.max
if not defined th set /a th=default.th
if not defined q.max set /a q.max=default.q.max
if not defined q.min set /a q.min=default.q.min
if not defined scale.min set /a scale.min=default.scale.min
call :const
if %~x1==.webp (call :pass) else (call :convert %1)
del %tempprefix%.* 2>nul
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
title -max %max% -th %th% -q %q% %args.cwebp.common% %1 %2
cwebp %args.cwebp.common% -q %q% %tempprefix%.i -o %tempprefix%.o
call wincmdlib.cmd filesize %tempprefix%.i >nul
set /a sourcesize=_
call wincmdlib.cmd filesize %tempprefix%.o >nul
set /a ratio=100*_/sourcesize
echo q=%q% compression: %ratio%%%
if %ratio% gtr %th% goto :reducequality
call wincmdlib filesize %tempprefix%.o >nul
set /a outputsize=_
if %outputsize% gtr %max% (
goto :resize.init
) else (
move /y %tempprefix%.o %1.webp >nul
nircmdc clonefiletime %1 "%~1.webp"
)
goto :eof

:reducequality
if %q% leq %q.min% echo Skip insufficient compression %ratio%%% && goto :eof
set /a q=q-10
goto :convert.tempfile

:resize.init
if %outputsize% gtr %max% (set scale=95) else goto :eof
if %outputsize% gtr %max1.25% set /a scale=90
if %outputsize% gtr %max1.5% set /a scale=80
if %outputsize% gtr %max2% set /a scale=70+5
if %outputsize% gtr %max2.8% set /a scale=60+10
if %outputsize% gtr %max4% set /a scale=50+10
if %outputsize% gtr %max6.25% set /a scale=40+10
if %outputsize% gtr %max9% set /a scale=30+10
if %outputsize% gtr %max16% set /a scale=25+5
if %outputsize% gtr %max25% set /a scale=20
if %outputsize% gtr %max100% set /a scale=10
:resize.smaller
if %scale% lss %scale.min% echo Refuse low scale %scale%%% && goto :reducequality
echo resize=%scale%%%
cwebp-resizep %args.cwebp.common% -q %q% -resizep %scale%%% %tempprefix%.i -o %tempprefix%.o
call wincmdlib filesize %tempprefix%.o >nul
if %_% gtr %max% (
set /a scale=scale-5
goto :resize.smaller
) else (
move /y %tempprefix%.o %1.webp >nul
nircmdc clonefiletime %1 "%~1.webp"
)
goto :eof

:pass
goto :eof

:const
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
