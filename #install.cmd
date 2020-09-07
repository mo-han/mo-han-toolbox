@echo off
set default.dst=%locallib_env%\_winbin

set dst=%1
if not defined dst set dst=default.dst

pushd "%~dp0"
mkdir %dst%\mylib
xcopy /s /y mylib %dst%\mylib
xcopy /s /y mykits %dst%
popd