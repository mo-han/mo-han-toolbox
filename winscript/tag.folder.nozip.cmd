@echo off
setlocal
set tagfile=FOLDER.TAG

for %%i in (%*) do echo > "%%~i"\%tagfile%