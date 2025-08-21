@echo off
setlocal

set HISCORE_DAT_PATH=%~dp0console_hiscore.dat
REM set HISCORE_PATH="R:\" 

python "%~dp0tools\retroarch_hiscore_companion.py" %*
REM retroarch_hiscore_companion.exe %*

pause
