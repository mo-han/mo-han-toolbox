@echo off
setlocal

endlocal & call :%*
goto :eof

:test
setlocal
echo %~0
goto :eof

:returnback
:lastline
:endof
setlocal
set "cmd=%*"
for /f "delims=" %%i in ('%cmd%') do set line=%%i
endlocal & call :return %line%
goto :eof

:lowercase
setlocal
set x=%~1
for %%i in ("A=a" "B=b" "C=c" "D=d" "E=e" "F=f" "G=g" "H=h" "I=i" "J=j" "K=k" "L=l" "M=m" "N=n" "O=o" "P=p" "Q=q" "R=r" "S=s" "T=t" "U=u" "V=v" "W=w" "X=x" "Y=y" "Z=z") do call set x=%%x:%%~i%%
endlocal & call :return %x%
goto :eof

:filesize
setlocal
endlocal & call :return %~z1
goto :eof

:filename
setlocal
endlocal & call :return %~n1
goto :eof

:basename
setlocal
endlocal & call :return %~n1%~x1
goto :eof

:parent
:parentpath
:dirname
setlocal
endlocal & call :return %~dp1
goto :eof

:realpath
:fullpath
setlocal
endlocal & call :return %~f1
goto :eof

:fileext
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