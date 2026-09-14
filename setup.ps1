$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectRoot

function Add-PathsToSession {
    $ffmpegBin = "C:\Users\Marcos\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.1-full_build\bin"
    $denoBin = "C:\Users\Marcos\AppData\Local\Microsoft\WinGet\Packages\DenoLand.Deno_Microsoft.Winget.Source_8wekyb3d8bbwe"

    if (Test-Path $ffmpegBin) {
        $env:Path = "$ffmpegBin;$env:Path"
    }

    if (Test-Path $denoBin) {
        $env:Path = "$denoBin;$env:Path"
    }
}

function Ensure-Tool {
    param(
        [string]$Name,
        [string]$WingetId
    )

    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        Write-Host "Instalando $Name..."
        winget install --id $WingetId -e --accept-source-agreements --accept-package-agreements
    }
}

Add-PathsToSession

if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
    throw "WinGet não está disponível. Instale o WinGet e tente novamente."
}

Ensure-Tool -Name "ffmpeg" -WingetId "Gyan.FFmpeg"
Ensure-Tool -Name "deno" -WingetId "DenoLand.Deno"

Add-PathsToSession

if (-not (Test-Path ".venv")) {
    Write-Host "Criando ambiente virtual do projeto..."
    python -m venv .venv
}

& ".\.venv\Scripts\python.exe" -m pip install --upgrade pip
& ".\.venv\Scripts\python.exe" -m pip install -r requirements.txt
& ".\.venv\Scripts\python.exe" -m pytest -q

Write-Host ""
Write-Host "Tudo pronto!"
Write-Host "Para abrir a interface, execute:"
Write-Host "  .\run_gui.ps1"
