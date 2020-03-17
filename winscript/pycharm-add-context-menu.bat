@echo off
setlocal

pushd "%~dp0"
set bin_dir=%cd%
if exist "%bin_dir%"\pycharm64.exe (
set bin=%bin_dir%\pycharm64.exe
goto :editreg
)
if exist "%bin_dir%"\pycharm.exe (
set bin=%bin_dir%\pycharm.exe
goto :editreg
)
if not defined %bin% (
echo Can not find pycharm*.exe
pause
goto :eof
)

:editreg
echo File
@reg add "HKEY_CLASSES_ROOT\*\shell\Open in PyCharm" /t REG_SZ /v "" /d "Open in PyCharm (&Y)"   /f
@reg add "HKEY_CLASSES_ROOT\*\shell\Open in PyCharm" /t REG_EXPAND_SZ /v "Icon" /d "%bin%,0" /f
@reg add "HKEY_CLASSES_ROOT\*\shell\Open in PyCharm\command" /t REG_SZ /v "" /d "%bin% \"%%1\"" /f
echo Folder
@reg add "HKEY_CLASSES_ROOT\Directory\shell\Open directory in PyCharm" /t REG_SZ /v "" /d "Open with PyCharm (&Y)"   /f
@reg add "HKEY_CLASSES_ROOT\Directory\shell\Open directory in PyCharm" /t REG_EXPAND_SZ /v "Icon" /d "%bin%,0" /f
@reg add "HKEY_CLASSES_ROOT\Directory\shell\Open directory in PyCharm\command" /t REG_SZ /v "" /d "%bin% \"%%1\"" /f
echo Folder background
@reg add "HKEY_CLASSES_ROOT\Directory\background\shell\Open directory in PyCharm" /t REG_SZ /v "" /d "Open with PyCharm (&Y)"   /f
@reg add "HKEY_CLASSES_ROOT\Directory\background\shell\Open directory in PyCharm" /t REG_EXPAND_SZ /v "Icon" /d "%bin%,0" /f
@reg add "HKEY_CLASSES_ROOT\Directory\background\shell\Open directory in PyCharm\command" /t REG_SZ /v "" /d "%bin% \"%%V\"" /f

pause