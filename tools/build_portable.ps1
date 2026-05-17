param(
    [string]$OutputRoot = "release"
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$portableRoot = Join-Path $projectRoot (Join-Path $OutputRoot "GrokVideoStudio_Portable_$timestamp")
$appDir = Join-Path $portableRoot "app"
$runtimeDir = Join-Path $portableRoot "runtime\python"
$launcherBuildDir = Join-Path $projectRoot "build\portable_launcher"

$basePython = & python -c "import sys; print(sys.base_prefix)"
$sitePackages = & python -c "import site; print(site.getsitepackages()[-1])"

New-Item -ItemType Directory -Force -Path $appDir | Out-Null
New-Item -ItemType Directory -Force -Path $runtimeDir | Out-Null

function Invoke-Robocopy {
    param(
        [string]$Source,
        [string]$Destination,
        [string[]]$CopyArgs = @()
    )
    robocopy $Source $Destination @CopyArgs | Out-Host
    if ($LASTEXITCODE -gt 7) {
        throw "Robocopy failed: $Source -> $Destination, exit code $LASTEXITCODE"
    }
}

Write-Host "Copying Python runtime..."
Invoke-Robocopy $basePython $runtimeDir @("/MIR", "/XD", "__pycache__", "/XF", "*.pyc")

Write-Host "Copying installed Python packages..."
$runtimeSitePackages = Join-Path $runtimeDir "Lib\site-packages"
New-Item -ItemType Directory -Force -Path $runtimeSitePackages | Out-Null
Invoke-Robocopy $sitePackages $runtimeSitePackages @("/MIR", "/XD", "__pycache__", "/XF", "*.pyc")

Write-Host "Copying application files..."
Copy-Item -LiteralPath (Join-Path $projectRoot "main.py") -Destination $appDir -Force
foreach ($name in @("assets", "data", "materials", "models", "dependencies")) {
    $source = Join-Path $projectRoot $name
    if (Test-Path -LiteralPath $source) {
        Invoke-Robocopy $source (Join-Path $appDir $name) @("/MIR", "/XD", "__pycache__", ".locks", "/XF", "*.pyc")
    }
}
New-Item -ItemType Directory -Force -Path (Join-Path $appDir "outputs") | Out-Null

$settingsPath = Join-Path $appDir "data\settings.json"
if (Test-Path -LiteralPath $settingsPath) {
    $settings = Get-Content -Raw -Encoding UTF8 -LiteralPath $settingsPath | ConvertFrom-Json
    foreach ($keyName in @("api_key", "text_api_key", "image_api_key", "audio_api_key", "ocr_api_key")) {
        if ($settings.PSObject.Properties.Name -contains $keyName) {
            $settings.$keyName = ""
        }
    }
    $settings.local_whisper_model_dir = Join-Path $appDir "models\faster-whisper"
    $settings.parser_download_dir = Join-Path $appDir "outputs\parsed_videos"
    $settings.output_dir = Join-Path $appDir "outputs"
    $settings | ConvertTo-Json -Depth 10 | Set-Content -Encoding UTF8 -LiteralPath $settingsPath
}

Write-Host "Building portable launcher exe..."
$launcherSource = Join-Path $projectRoot "tools\portable_launcher.py"
$launcherDist = Join-Path $launcherBuildDir "dist"
$launcherWork = Join-Path $launcherBuildDir "build"
New-Item -ItemType Directory -Force -Path $launcherBuildDir | Out-Null
& python -m PyInstaller --noconfirm --onefile --windowed --name "GrokVideoStudio" --distpath $launcherDist --workpath $launcherWork --specpath $launcherBuildDir --icon (Join-Path $projectRoot "assets\app_icon.ico") $launcherSource
if ($LASTEXITCODE -ne 0) {
    throw "Launcher exe build failed."
}
Copy-Item -LiteralPath (Join-Path $launcherDist "GrokVideoStudio.exe") -Destination (Join-Path $portableRoot "GrokVideoStudio.exe") -Force

$startBat = @"
@echo off
cd /d "%~dp0app"
set PYTHONNOUSERSITE=1
"%~dp0runtime\python\python.exe" main.py
pause
"@
Set-Content -LiteralPath (Join-Path $portableRoot "start_portable.bat") -Value $startBat -Encoding ASCII

$readme = @"
Grok Video Studio portable package

Start:
1. Double click GrokVideoStudio.exe.
2. If the exe is blocked by antivirus policy, double click start_portable.bat.
3. local_gpu transcription uses runtime\python, app\models\faster-whisper, and bundled NVIDIA CUDA/cuDNN Python runtime packages.

Requirements:
- Windows x64
- NVIDIA GPU, 6GB VRAM or higher recommended
- Installed NVIDIA display driver

Notes:
- CUDA/cuBLAS/cuDNN runtime packages are included under runtime\python\Lib\site-packages.
- NVIDIA display drivers cannot be bundled with the app. The target machine still needs a working NVIDIA driver.
"@
Set-Content -LiteralPath (Join-Path $portableRoot "README_portable.txt") -Value $readme -Encoding UTF8

Write-Host "Verifying portable runtime imports..."
& (Join-Path $runtimeDir "python.exe") -c "import faster_whisper, ctranslate2, av, nvidia.cublas, nvidia.cudnn; print('portable runtime ok')"
if ($LASTEXITCODE -ne 0) {
    throw "Portable runtime import verification failed."
}

Write-Host "Portable package created:"
Write-Host $portableRoot
