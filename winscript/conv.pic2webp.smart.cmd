@echo off
setlocal
set /a default.max=1024*384
set /a default.ratio=75
set /a default.q.max=80
set /a default.q.min=70
set /a default.scale.min=70
set default.args.cwebp.common=-short
set tmp="%temp%"\cwebptmp%random%%random%%random%
goto :bof
:help
echo Convert picture file to webp, smartly
echo Usage: %~n0 [file^|-h^|?^|/?] ["set env_vars"]
goto :eof
Dependencies:
    - cwebp.exe
    - ffprobe.exe
    - nircmdc.exe
    - wrap.ffprobe.cmd
    - drawincmd.cmd
    - wincmdlib.cmd
:bof
setlocal
if "%~1"=="" goto :help
if "%~1"=="-h" goto :help
if "%~1"=="?" goto :help
if "%~1"=="/?" goto :help
call %~2
if not defined max set /a max=default.max
if not defined ratio set /a ratio=default.ratio
if not defined q.max set /a q.max=default.q.max
if not defined q.min set /a q.min=default.q.min
if not defined scale.min set /a scale.min=default.scale.min
if not defined args.cwebp.common (set args.cwebp.common=%default.args.cwebp.common%) else (set args.cwebp.common=%default.args.cwebp.common% %args.cwebp.common%)
call :const
if /i %~x1==.jpg goto :nonwebp
if /i %~x1==.jpeg goto :nonwebp
if /i %~x1==.png goto :nonwebp
if /i %~x1==.bmp goto :nonwebp
goto :eof
:nonwebp
call drawincmd line
if %~z1==0 echo ! skip empty file & goto :eof
if exist "%~1.webp" (
    echo * drop existing "%~1.webp"
    del "%~1.webp"
)
copy /y %1 %tmp%.i >nul
call wincmdlib filesize %tmp%.i >nul
set /a ifs=_
call wincmdlib returnback wrap.ffprobe w %tmp%.i >nul
set /a iw=_
call wincmdlib returnback wrap.ffprobe h %tmp%.i >nul
set /a ih=_
set /a ipix=iw*ih
echo #%max% %iw%x%ih% scale^>=%scale.min%%% ratio^<=%ratio%%% q=%q.max%..%q.min% %1
call :smartconv %1
del %tmp%.* 2>nul
goto :eof

:smartconv
setlocal
set /a q=q.min & set /a scale=scale.min
call :cwebptmp
set /a omr=100*ofs/max
set /a rrr=100*fsr/ratio
if %ok%==0 (
    call :cwebptmp.targetsize
    goto :smartconv.output
)
set /a q=q.min
if %omr% lss 90 (if %rrr% lss 90 set /a q=q+10)
if %omr% lss 80 (if %rrr% lss 80 set /a q=q+10)
if %omr% lss 70 (if %rrr% lss 70 set /a q=q+10)
if %omr% lss 60 (if %rrr% lss 60 set /a q=q+10)
if %omr% lss 50 (if %rrr% lss 50 set /a q=q.max)
if %q%==%q.min% if %scale%==100 if %ok%==1 goto :smartconv.output
if %q% gtr %q.max% set /a q=q.max
set /a scale=100
:smartconv.guess.scale
call :cwebptmp
if %ok%==1 goto :smartconv.output
if %ofs% leq %max% (set /a scale=scale-5 && goto :smartconv.lower.scale)
if %ofs% gtr %max% (set scale=95) else (goto :smartconv.lower.q)
if %ofs% gtr %max.1.5% set scale=85
if %ofs% gtr %max.2% set scale=75
if %ofs% gtr %max.4% set scale=60
if %ofs% gtr %max.6.25% set scale=50
if %ofs% gtr %max.9% set scale=40
if %ofs% gtr %max.16% set scale=30
if %ofs% gtr %max.25% set scale=25
if %ofs% gtr %max.100% set scale=15
:smartconv.lower.scale
if %scale% lss %scale.min% goto :smartconv.lower.q
call :cwebptmp
if %ok%==1 goto :smartconv.output
set /a scale=scale-5
goto :smartconv.lower.scale
:smartconv.lower.q
set /a q=q-5 && set /a scale=100
if %q% geq %q.min% goto :smartconv.guess.scale
call :cwebptmp.targetsize
:smartconv.output
if %ok%==0 goto :eof
echo * ok
move /y %tmp%.o %1.webp >nul
nircmdc clonefiletime %1 %1.webp
goto :eof

:cwebptmp
::%~0 ["options"]
set /a ow=iw*scale/100
set /a oh=ih*scale/100
cwebp %args.cwebp.common% -q %q% -resize %ow% %oh% %~1^ %tmp%.i -o %tmp%.o
call wincmdlib filesize %tmp%.o >nul
set /a ofs=_
set /a fsr=100*ofs/ifs
echo *%ofs% %iw%x%ih%-^>%ow%x%oh%(%scale%%%) ratio=%fsr%%% -q %q% %~1
set ok=1
if %ofs% gtr %max% set ok=0
if %fsr% gtr %ratio% set ok=0
goto :eof

:cwebptmp.targetsize
set /a _=100*%max%/%ifs%
if %_% gtr %ratio% (
    set ok=0
    echo # modest file size, keep original, skip
    goto :eof
)
call :cwebptmp "-size %max%"
set ok=1
goto :eof

:const
set /a max.1.25=%max%*125/100
set /a max.1.5=%max%*15/10
set /a max.2=%max%*2
set /a max.2.8=%max%*28/10
set /a max.4=%max%*4
set /a max.6.25=%max%*625/100
set /a max.9=%max%*9
set /a max.16=%max%*16
set /a max.25=%max%*25
set /a max.100=%max%*100
goto :eof
