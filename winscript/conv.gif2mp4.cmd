@echo off
setlocal
set /a default.thres=1024*1024*2

if not %~x1==.gif goto :eof
if %~z1 leq %default.thres% goto :eof
call drawincmd line
echo * %~1(%~z1^>%default.thres%) -^> .hevc8b.mp4
ffmpeg -i "%~1" -c:v hevc -crf 23 %~2 "%~1.hevc8b.mp4" -y && del "%~1"
