# setup-xtts.ps1 - Install Coqui XTTS v2 and accept terms automatically
[CmdletBinding()]
param(
  [string]$Python = "python",
  [string]$EnvPath = ".xtts_env"
)
$ErrorActionPreference = "Stop"
function Info($m){ Write-Host "[INFO] $m" -ForegroundColor Cyan }
function Ok($m){ Write-Host "[ OK ] $m" -ForegroundColor Green }
function Warn($m){ Write-Host "[WARN] $m" -ForegroundColor Yellow }
function Err($m){ Write-Host "[ERR ] $m" -ForegroundColor Red }

Set-Location -Path (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location ..

Info "Creating/Using venv at $EnvPath"
& $Python -m venv $EnvPath
$activate = Join-Path $EnvPath "Scripts\Activate.ps1"
. $activate

Info "Upgrading pip toolchain"
python -m pip install --upgrade pip wheel setuptools

Info "Installing Coqui TTS (this may take several minutes)"
pip install -v --prefer-binary "TTS>=0.22.0"

Info "Downloading xtts_v2 model with terms acceptance"
tts --model_name "tts_models/multilingual/multi-dataset/xtts_v2" --agree-terms --text "Model ready" --out_path "xtts_install_test.wav"

if (Test-Path "xtts_install_test.wav") { Ok "XTTS installed. Test: xtts_install_test.wav" } else { Warn "Test file not found, check logs." }
