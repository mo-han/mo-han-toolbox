@echo off
setlocal
set "hc=%~dp0hentai_cafe.py"
title hentai_cafe_wrap.bat %u_dl% %*

:start
%hc% %* || goto :start
exit