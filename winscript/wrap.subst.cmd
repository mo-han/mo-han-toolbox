@echo off
setlocal

set drive=%1
set pth=%2
if not defined drive set drive=z
if not defined pth set pth=.
subst %drive%: %pth%
pause
subst %drive%: /d