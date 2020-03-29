@echo off
setlocal

for %%i in (*.webm) do (call :webm2gif "%%~i")
del temp.i.webm
del temp.o.gif
goto :eof

:webm2gif
copy /y "%~1" temp.i.webm
ffmpeg -i temp.i.webm temp.o.gif -y
call :setsize temp.o.gif
if %__size% gtr 10000000 ffmpeg -i temp.i.webm -vf "scale=iw/2:ih/2" temp.o.gif -y
call :setsize temp.o.gif
if %__size% gtr 10000000 ffmpeg -i temp.i.webm -vf "scale=iw/3:ih/3" temp.o.gif -y
call :setsize temp.o.gif
if %__size% gtr 10000000 ffmpeg -i temp.i.webm -vf "scale=iw/4:ih/4" temp.o.gif -y
copy /y temp.o.gif "%~n1.gif"
goto :eof

:setsize
set __size=%~z1
goto :eof