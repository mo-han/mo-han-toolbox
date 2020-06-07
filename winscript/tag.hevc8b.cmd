@echo off
setlocal
set tag.origin=.__origin__

call :check.tagged "%~n1"

:check.tagged
