@echo off
set dst=%1
if not defined dst echo no dst && pause && goto :eof

pushd "%~dp0"
set src=mylib\easy
pyclean %src%
mkdir %dst%\%src%
xcopy /s /y %src% %dst%\%src%
set src=mylib\ex
mkdir %dst%\%src%
xcopy /s /y %src% %dst%\%src%
popd