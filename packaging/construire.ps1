# Construit dist\Mes-outils-Setup.exe : le programme (PyInstaller) puis
# l'installateur (Inno Setup). Utilisé à la main et par GitHub Actions.
#   powershell -ExecutionPolicy Bypass -File packaging\construire.ps1
# Prérequis (seulement pour construire) : pip install -r requirements.txt pyinstaller,
# et Inno Setup 6 (iscc).
param([string]$Python = "python")
$ErrorActionPreference = "Stop"
$racine = Split-Path -Parent $PSScriptRoot
Set-Location $racine

$version = (Select-String -Path "outil\config.py" -Pattern '^VERSION = "([\d.]+)"').Matches[0].Groups[1].Value
Write-Host "Mes outils $version"

# 1. Le programme : dist\Mes outils\Mes outils.exe
Remove-Item -Recurse -Force "dist", "build" -ErrorAction SilentlyContinue
& $Python -m PyInstaller "packaging\mes_outils.spec" --noconfirm --distpath dist --workpath build\pyinstaller
if ($LASTEXITCODE -ne 0) { throw "PyInstaller a échoué" }

# 2. L'installateur : dist\Mes-outils-Setup.exe
$iscc = @(
  (Get-Command iscc -ErrorAction SilentlyContinue).Source,
  "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
  "$env:ProgramFiles\Inno Setup 6\ISCC.exe",
  "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe"
) | Where-Object { $_ -and (Test-Path $_) } | Select-Object -First 1
if (-not $iscc) { throw "Inno Setup 6 (ISCC.exe) introuvable" }
& $iscc "/DVersion=$version" "packaging\installateur.iss"
if ($LASTEXITCODE -ne 0) { throw "Inno Setup a échoué" }

$setup = Get-Item "dist\Mes-outils-Setup.exe"
Write-Host ("Prêt : {0} ({1:N1} Mo)" -f $setup.FullName, ($setup.Length / 1MB))
