# Run the pre-registered P10 sequence in one GPU window; stop at the first non-zero exit.
# Usage (from examples\ref01_expense_report):  pwsh experiments/run_p10_window.ps1
# Output: reviews\evidence\p10\ (written by the driver) and experiments\p10_window_console.log
$log = "experiments\p10_window_console.log"
"P10 window start $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" | Set-Content $log
$steps = @(
    @("--phase", "dev"),
    @("--analyse"),
    @("--freeze-candidate", "v2"),
    @("--phase", "heldout"),
    @("--analyse")
)
foreach ($s in $steps) {
    "=== $(Get-Date -Format 'HH:mm:ss') p10_trials.py $($s -join ' ')" | Add-Content $log
    python experiments\p10_trials.py @s *>> $log
    $code = $LASTEXITCODE
    "=== exit $code" | Add-Content $log
    if ($code -ne 0) { "STOPPED at step: $($s -join ' ')" | Add-Content $log; break }
}
ollama stop qwen2.5:7b 2>&1 | Out-Null
"P10 window end $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" | Add-Content $log
