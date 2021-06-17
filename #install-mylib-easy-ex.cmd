@echo off
set dst=%1
if not defined dst echo no dst && pause && goto :eof

pushd "%~dp0"
pyclean mylib\easy
pyclean mylib\ex
mkdir %dst%\easy
mkdir %dst%\ex
xcopy /s /y mylib\easy %dst%\easy
xcopy /s /y mylib\ex %dst%\ex
popd