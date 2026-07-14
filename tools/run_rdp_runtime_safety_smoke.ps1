<#
Run the MacroFlow Windows runtime-safety RDP smoke.

This wrapper keeps stdout/stderr separate, preserves the structured JSON report,
and writes a compact evidence bundle to the Windows clipboard.
#>

param(
    [string]$LogDir = "$env:USERPROFILE\macroflow-rdp-test-logs",
    [string]$Python = ".\.venv\Scripts\python.exe"
)

$ErrorActionPreference = 'Continue'
Set-Location (Resolve-Path (Join-Path $PSScriptRoot '..'))
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$report = Join-Path $LogDir "runtime_safety_$stamp.json"
$stdoutLog = Join-Path $LogDir "runtime_safety_stdout_$stamp.log"
$stderrLog = Join-Path $LogDir "runtime_safety_stderr_$stamp.log"
$mergedLog = Join-Path $LogDir "runtime_safety_$stamp.log"

$proc = Start-Process -FilePath $Python -ArgumentList @(
    '.\tools\rdp_runtime_safety_smoke.py',
    '--report',
    $report
) -NoNewWindow -Wait -PassThru -RedirectStandardOutput $stdoutLog -RedirectStandardError $stderrLog
$exit = $proc.ExitCode

$merged = @()
if (Test-Path $stdoutLog) {
    $merged += Get-Content $stdoutLog
}
if (Test-Path $stderrLog) {
    $stderrLines = Get-Content $stderrLog
    if ($stderrLines.Count -gt 0) {
        if ($merged.Count -gt 0) {
            $merged += ''
        }
        $merged += '--- STDERR ---'
        $merged += $stderrLines
    }
}
Set-Content -Path $mergedLog -Value $merged -Encoding utf8
Remove-Item $stdoutLog, $stderrLog -ErrorAction SilentlyContinue

$reportText = if (Test-Path $report) {
    Get-Content $report -Raw -Encoding utf8
} else {
    '<missing>'
}
$summary = @(
    "RUNTIME_SAFETY_EXIT=$exit"
    "RUNTIME_SAFETY_REPORT=$report"
    "RUNTIME_SAFETY_LOG=$mergedLog"
    '---REPORT---'
    $reportText
) -join "`n"

Set-Clipboard -Value $summary
Write-Host $summary
exit $exit
