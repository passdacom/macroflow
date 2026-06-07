<#
Run the MacroFlow RDP GUI smoke harness on Windows.

Expected use from the Windows RDP repo checkout:
  powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\run_rdp_gui_smoke.ps1

The script writes a compact summary to the Windows clipboard so a remote
operator can paste/read the result without scraping the whole terminal.
#>

param(
    [string]$LogDir = "$env:USERPROFILE\macroflow-rdp-test-logs",
    [string]$Python = ".\.venv\Scripts\python.exe",
    [string]$Text = "rdp-ok"
)

$ErrorActionPreference = 'Continue'
Set-Location (Resolve-Path (Join-Path $PSScriptRoot '..'))
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$log = Join-Path $LogDir "gui_smoke_$stamp.log"

& $Python .\tools\rdp_gui_smoke.py --log-dir $LogDir --text $Text 2>&1 | Tee-Object -FilePath $log
$exit = $LASTEXITCODE
$tail = Get-Content $log -Tail 160 -ErrorAction SilentlyContinue
$txt = "GUI_SMOKE_EXIT=$exit`nSCRIPT=$PWD\tools\rdp_gui_smoke.py`nLOG=$log`n" + ($tail -join "`n")
Set-Clipboard -Value $txt
Write-Host $txt
exit $exit
