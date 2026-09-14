@echo off
cd /d "%~dp0"
set "FFMPEG_BIN=C:\Users\Marcos\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.1-full_build\bin"
set "DENO_BIN=C:\Users\Marcos\AppData\Local\Microsoft\WinGet\Packages\DenoLand.Deno_Microsoft.Winget.Source_8wekyb3d8bbwe"
set "PATH=%FFMPEG_BIN%;%DENO_BIN%;%PATH%"
call .venv\Scripts\activate.bat
python gui.py
