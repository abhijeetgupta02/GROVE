# Called by task_launch.ps1 once logs\ARMED.txt exists: start the frozen Ollama if nothing is listening, then the runner (it exits at once if another runner holds the lock).
$G = 'C:\GROVE_PC'
if (Test-Path "$G\logs\ALL_DONE.txt") { exit 0 }
$c = Get-NetTCPConnection -LocalPort 11434 -ErrorAction SilentlyContinue | Where-Object { $_.OwningProcess -ne 0 -and $_.RemotePort -eq 0 }
if (-not $c) {
  Start-Process "$G\ollama\0.40.14\ollama.exe" -ArgumentList 'serve' -WorkingDirectory "$G\ollama\0.40.14" -RedirectStandardOutput "$G\logs\ollama_serve_task.out.log" -RedirectStandardError "$G\logs\ollama_serve_task.log" -WindowStyle Hidden
  Start-Sleep 10
}
& "$G\venv\Scripts\python.exe" "$G\code\runner.py" --mode main *>> "$G\logs\runner_console.log"
