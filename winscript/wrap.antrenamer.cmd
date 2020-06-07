@echo off
setlocal

set arbdir=%locallib_etc%\antrenamer
call :%*
goto :eof

:spechar
:: spechar <convert|revert> [options]
set arb=%arbdir%\spechar.%~1.arb
call wincmdlib lstriparg1 %*
call antrenamer -b "%arb%" %_%
goto :eof
