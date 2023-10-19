@echo off
set default.dst=%locallib_env%\
set dst=%1
if not defined dst set dst=%default.dst%

pushd "%~dp0"
pyclean .

mkdir %dst%\mylib
xcopy /s /y mylib %dst%\mylib
mkdir %dst%\mykits
xcopy /s /y mykits %dst%
mkdir %dst%\i18n
xcopy /s /y i18n %dst%\i18n

mkdir %dst%\oldezpykit
xcopy /s /y oldezpykit %dst%\oldezpykit
mkdir %dst%\oldezpykitext
xcopy /s /y oldezpykitext %dst%\oldezpykitext
mkdir %dst%\websites
xcopy /s /y websites %dst%\websites
mkdir %dst%\apps
xcopy /s /y apps %dst%

popd