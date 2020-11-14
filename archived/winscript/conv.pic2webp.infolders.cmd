@echo off
setlocal

for %%i in (%*) do call conv.pic2webp.infolder %%i
pause