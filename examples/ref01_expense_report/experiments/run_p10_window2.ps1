# P10 window 2: v2.1 dev re-run, candidate freeze, held-out, analysis; stop at the first non-zero exit.
$log = "experiments\p10_window2_console.log"
"P10 window 2 start $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" | Set-Content $log
$steps = @(
    @("--phase", "dev", "--candidate-tag", "v2.1"),
    @("--analyse"),
    @("--freeze-candidate", "v2.1"),
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
"P10 window 2 end $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" | Add-Content $log
