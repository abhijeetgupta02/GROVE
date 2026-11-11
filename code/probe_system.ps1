# SYSTEM-context probe: frozen Ollama on a spare port, one short call on qwen3.5:9b, GPU share, torch and optional extra checks.
$G = 'C:\GROVE_PC'; $out = "$G\logs\probe_system.txt"; $port = 11435; $base = "http://127.0.0.1:$port"
function W($m) { Add-Content $out "$(Get-Date -Format s)  $m" }
W "=== probe as $(whoami), session $([System.Diagnostics.Process]::GetCurrentProcess().SessionId) ==="
W ("nvidia-smi: " + ((nvidia-smi --query-gpu=name,driver_version,memory.used --format=csv,noheader) -join ' '))
$env:OLLAMA_HOST = "127.0.0.1:$port"
$p = Start-Process "$G\ollama\0.40.14\ollama.exe" -ArgumentList 'serve' -RedirectStandardError "$G\logs\probe_serve.log" -RedirectStandardOutput "$G\logs\probe_serve.out.log" -WindowStyle Hidden -PassThru
Start-Sleep 8
try { W ("ollama version: " + (Invoke-RestMethod "$base/api/version").version) } catch { W "version error: $($_.Exception.Message)" }
$body = @{ model = 'qwen3.5:9b'; messages = @(@{ role = 'user'; content = "Reply with OK`n/nothink" }); stream = $false; think = $false; keep_alive = '5m'; options = @{ temperature = 0; num_ctx = 8192; num_predict = 32; seed = 20260422 } } | ConvertTo-Json -Depth 6
try { $r = Invoke-RestMethod -Method Post -Uri "$base/api/chat" -Body $body -ContentType 'application/json' -TimeoutSec 900; W ("reply: [" + $r.message.content.Trim() + "] done_reason=" + $r.done_reason) } catch { W "chat error: $($_.Exception.Message)" }
try { foreach ($m in (Invoke-RestMethod "$base/api/ps").models) { W ("ps: {0} size={1} size_vram={2} gpu_share={3:N3} ctx={4}" -f $m.name, $m.size, $m.size_vram, ($m.size_vram / [double]$m.size), $m.context_length) } } catch { W "ps error: $($_.Exception.Message)" }
try { Invoke-RestMethod -Method Post -Uri "$base/api/generate" -Body (@{ model = 'qwen3.5:9b'; keep_alive = 0 } | ConvertTo-Json) -ContentType 'application/json' | Out-Null } catch {}
if (Test-Path "$G\venv\Lib\site-packages\torch") { W ("torch: " + ((& "$G\venv\Scripts\python.exe" -c "import torch;print(torch.__version__, torch.version.cuda, torch.cuda.is_available(), torch.cuda.get_device_name(0) if torch.cuda.is_available() else '')" 2>&1) -join ' ')) }
if (Test-Path "$G\code\probe_extra.py") { W ("probe_extra: " + ((& "$G\venv\Scripts\python.exe" "$G\code\probe_extra.py" 2>&1 | Select-Object -Last 15) -join ' | ')) }
Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue
W '=== probe end ==='
