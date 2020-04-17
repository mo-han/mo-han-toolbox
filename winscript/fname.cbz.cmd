@echo off
rename *.zip *.cbz
Renamer.exe -b %locallib_etc%\antrenamer\cbz-1280x.arb -af *.cbz -g -x
Renamer.exe -b %locallib_etc%\antrenamer\spaces2space.arb -af *.cbz -g -x
Renamer.exe -b %locallib_etc%\antrenamer\lstripdigits-.arb -af *.cbz -g -x