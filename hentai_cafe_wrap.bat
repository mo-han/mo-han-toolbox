@echo off
setlocal
set "hc=%~dp0hentai_cafe.py"
title hentai.cafe dl %u_dl% %*
pushd %u_dl%
set https_proxy=%u_proxy%
set http_proxy=%u_proxy%

:start
%hc% %* || goto :start
popd
goto :eof