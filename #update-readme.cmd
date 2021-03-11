@echo off
setlocal
set file.input=readme-src.md
set file.output=README.MD
cd /d "%~dp0"

gh-md-toc %file.input% > %file.output%
echo=>> %file.output%
echo=>> %file.output%
type %file.input% >> %file.output%