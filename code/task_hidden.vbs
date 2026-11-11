' Runs task_launch.ps1 without a visible window and waits for it (so "do not start a new instance" applies).
CreateObject("WScript.Shell").Run "powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -File C:\GROVE_PC\code\task_launch.ps1", 0, True
