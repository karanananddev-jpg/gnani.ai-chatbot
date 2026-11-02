@echo off
title Push Gnani.ai Chatbot to GitHub
echo ======================================================================
echo    Pushing Gnani.ai Chatbot to:
echo    https://github.com/karanananddev-jpg/gnani.ai-chatbot
echo ======================================================================
echo.

git push -u origin main

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ======================================================================
    echo  SUCCESS! Code pushed to GitHub successfully.
    echo  Now go to https://dashboard.render.com to deploy and get 24/7 link!
    echo ======================================================================
) else (
    echo.
    echo If authentication failed, please sign in with your GitHub account
    echo or use a GitHub Personal Access Token.
)

echo.
pause

