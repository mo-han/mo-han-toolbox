@echo off
rename *.zip *.cbz
Renamer.exe -b %locallib_etc%\antrenamer\cbz-1280x.arb -af *.cbz -g -x
Renamer.exe -b %locallib_etc%\antrenamer\spaces2vbar.arb -af *.cbz -g -x