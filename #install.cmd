@echo off
set default.dst=%locallib_env%\
set dst=%1
if not defined dst set dst=%default.dst%

pushd "%~dp0"
pyclean .
mkdir %dst%\mylib
xcopy /s /y mylib %dst%\mylib
xcopy /s /y ezpykit %dst%\ezpykit
xcopy /s /y ezpykitext %dst%\ezpykitext
xcopy /s /y mykits %dst%
xcopy /s /y i18n %dst%\i18n
popd