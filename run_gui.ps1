$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectRoot

$ffmpegBin = "C:\Users\Marcos\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.1-full_build\bin"
$denoBin = "C:\Users\Marcos\AppData\Local\Microsoft\WinGet\Packages\DenoLand.Deno_Microsoft.Winget.Source_8wekyb3d8bbwe"

if (Test-Path $ffmpegBin) {
    $env:Path = "$ffmpegBin;$env:Path"
}

if (Test-Path $denoBin) {
    $env:Path = "$denoBin;$env:Path"
}

& ".\.venv\Scripts\python.exe" gui.py
