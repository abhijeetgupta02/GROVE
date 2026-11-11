' POST HOC Part B resume (D28): runs code\posthoc_resume.cmd without a window and waits for it (scheduled task GROVE_PostHoc_Resume).
CreateObject("WScript.Shell").Run "cmd.exe /c C:\GROVE_PC\code\posthoc_resume.cmd", 0, True
