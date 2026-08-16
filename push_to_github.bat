@echo off
title Push AutoInspect AI to GitHub
echo ========================================================
echo   Pushing AutoInspect AI to GitHub Repository
echo   Target: https://github.com/Anshuhole/Auto_damage_detection
echo ========================================================
echo.

set "PATH=C:\Program Files\Git\cmd;C:\Users\VISHNU\dev_tools\git\cmd;C:\Users\VISHNU\dev_tools\node-v20.18.0-win-x64;C:\Users\VISHNU\dev_tools\python311;%PATH%"

git branch -M main
git remote set-url origin https://github.com/Anshuhole/Auto_damage_detection.git

echo Uploading commits...
git push -u origin main

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================================
    echo   SUCCESS! Pushed to https://github.com/Anshuhole/Auto_damage_detection
    echo ========================================================
) else (
    echo.
    echo If GitHub asks for login, please authenticate in the browser popup or enter your token.
)

echo.
pause
