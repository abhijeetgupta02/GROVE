# GROVE_Run scheduled task entry point. Runs as SYSTEM at startup and every 10 minutes ("do not start a new instance").
# 1) stops if logs\ALL_DONE.txt exists; 2) runs a requested SYSTEM probe; 3) does nothing until logs\ARMED.txt exists;
# 4) then hands over to code\run_launch.ps1 (frozen Ollama + runner, runner holds logs\runner.lock).
$ErrorActionPreference = 'Continue'
$G = 'C:\GROVE_PC'
$log = "$G\logs\task_launch.log"
function Log($m) { Add-Content -Path $log -Value "$(Get-Date -Format s)  [$(whoami)] $m" }
$env:OLLAMA_MODELS = 'C:\Users\Shruti Singh\.ollama\models'
$env:OLLAMA_MAX_LOADED_MODELS = '1'; $env:OLLAMA_NUM_PARALLEL = '1'; $env:OLLAMA_KEEP_ALIVE = '15m'
$env:HF_HOME = "$G\tools\hf"; $env:TORCH_HOME = "$G\tools\torch"; $env:HF_HUB_OFFLINE = '1'; $env:TRANSFORMERS_OFFLINE = '1'
$env:PYTHONUTF8 = '1'; $env:PYTHONIOENCODING = 'utf-8'
if (Test-Path "$G\logs\ALL_DONE.txt") { exit 0 }
$req = "$G\logs\probe_request.txt"; $done = "$G\logs\probe_done.txt"
if ((Test-Path $req) -and ((-not (Test-Path $done)) -or ((Get-Item $req).LastWriteTime -gt (Get-Item $done).LastWriteTime))) {
  Log 'probe requested'
  & powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$G\code\probe_system.ps1" *> "$G\logs\probe_system_console.log"
  Set-Content $done (Get-Date -Format o)
  Log 'probe finished'
}
if (-not (Test-Path "$G\logs\ARMED.txt")) { exit 0 }
if (Test-Path "$G\code\run_launch.ps1") { & "$G\code\run_launch.ps1" } else { Log 'ARMED but code\run_launch.ps1 missing' }
