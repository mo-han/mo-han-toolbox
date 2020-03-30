@echo off
setlocal
set ffprob=ffprobe -v error

call :%*
goto :eof

:res
:resolution
%ffprob% -select_streams v:0 -show_entries stream=width,height -of csv=p=0:s=* %*
goto :eof

:vc
:vcodec
:vencoder
%ffprob% -select_streams v:0 -show_entries stream=codec_name -of csv=p=0 %*
goto :eof

:all
%ffprob% -show_streams -of json %*
goto :eof

:vprofile
%ffprob% -select_streams v:0 -show_entries stream=profile -of csv=p=0 %*
goto :eof

:vpixfmt
%ffprob% -select_streams v:0 -show_entries stream=pix_fmt -of csv=p=0 %*
goto :eof
