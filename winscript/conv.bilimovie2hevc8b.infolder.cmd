@echo off
setlocal

set args=%*
call set args=%%args:*%1=%%
if defined args set args=%args:* =%

conv.hevc8b.infolder %1 -vf "scale='min(iw,1280)':-2" -crf 25 %args%