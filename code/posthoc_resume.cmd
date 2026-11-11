@echo off
rem POST HOC Part B resume (owner's request of 2026-11-10 15:55; logs\deviations.md D28).
rem Started by the scheduled task GROVE_PostHoc_Resume through code\posthoc_hidden.vbs, outside the Claude desktop app,
rem so an app update cannot close it. Same runner, code path, options, image encoding, retries and context as the first start;
rem finished images are skipped (same config hash). New console log files; nothing existing is overwritten.
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
cd /d C:\GROVE_PC
"C:\GROVE_PC\venv\Scripts\python.exe" "C:\GROVE_PC\code\posthoc_runner.py" >> "C:\GROVE_PC\results_posthoc\logs\console_resume1.out.log" 2>> "C:\GROVE_PC\results_posthoc\logs\console_resume1.err.log"
