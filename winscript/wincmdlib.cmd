@echo off
setlocal

endlocal & call :%*
goto :eof

:test
setlocal
goto :eof

:returnback
:lastline
:endof
setlocal
set "cmd=%*"
for /f "delims=" %%i in ('%cmd%') do set line=%%i
endlocal & call :return %line%
goto :eof

:filesize
setlocal
endlocal & call :return %~z1
goto :eof

:filename
:basename
setlocal
endlocal & call :return %~n1
goto :eof

:dirname
setlocal
endlocal & call :return %~dp1
goto :eof

:fext
:fileextension
setlocal
endlocal & call :return %~x1
goto :eof

:return
setlocal
echo %*
endlocal & set _=%*
goto :eof

:declare
setlocal
echo %*
call %*
goto :eof