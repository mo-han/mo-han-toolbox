@echo off
setlocal

for %%i in (%*) do call :intodir %%i
pause
goto :eof

:intodir
pushd %1
for %%i in (*) do call :rm__tag__ "%%~i"
popd
goto :eof

:rm__tag__
call :get_tag "%~n1"
if not [%_tag:~0,2%]==[__] goto :eof
if not [%_tag:~-2%]==[__] goto :eof
set newfilename="%_name%%~x1"
echo %1 -^> %newfilename%
rename %1 %newfilename%
goto :eof

:get_tag
set "_tag=%~x1"
set _tag=%_tag:~1%
set "_name=%~n1"
goto :eof