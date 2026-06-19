#requires -Version 5.1
<#
.SYNOPSIS
    Table-driven unit tests for the PURE decision function Get-WatchdogAction
    (scripts/autofirm_resume_watchdog.ps1), plus a guard test for the recycled-PID case.

.DESCRIPTION
    No Pester dependency: the Windows-bundled Pester is v3 (incompatible syntax) and we
    must not add a heavy test dep to a tiny ops script. This harness dot-sources the
    watchdog (which, under dot-sourcing, defines functions WITHOUT running the tick),
    drives Get-WatchdogAction across the full decision table, and exits non-zero on any
    mismatch so it gates in CI / `make test` exactly like a normal failing test.

    These tests have TEETH: every row asserts an EXACT action for a precisely-constructed
    state, including the adversarial recycled-PID and corrupt-lock cases. A single wrong
    branch in the pure fn fails the suite (and would be caught by mutation testing).
#>
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# Dot-source the script under test. InvocationName '.' suppresses the entry-point tick.
$here   = Split-Path -Parent $MyInvocation.MyCommand.Path
$target = Join-Path (Split-Path -Parent $here) 'scripts/autofirm_resume_watchdog.ps1'
. $target

# --- tiny assertion helpers -------------------------------------------------------------
$script:Failures = New-Object System.Collections.Generic.List[string]
$script:Passes   = 0

function Assert-Action {
    param(
        [string] $Case,
        [string] $Expected,
        [hashtable] $State
    )
    $actual = Get-WatchdogAction `
        -LockData            $State.LockData `
        -SentinelExists      $State.SentinelExists `
        -LiveProcess         $State.LiveProcess `
        -AutoFirmProcessLive $State.AutoFirmProcessLive `
        -RepoRecentlyActive  $State.RepoRecentlyActive `
        -HasPendingWork      $State.HasPendingWork
    if ($actual -eq $Expected) {
        $script:Passes++
        Write-Host ("  PASS  {0,-46} -> {1}" -f $Case, $actual)
    }
    else {
        $msg = "FAIL  {0}: expected '{1}' but got '{2}'" -f $Case, $Expected, $actual
        $script:Failures.Add($msg)
        Write-Host ("  " + $msg) -ForegroundColor Red
    }
}

# A live process descriptor with a given start token (identity of a running PID).
function New-Live { param([long]$Ticks) [pscustomobject]@{ StartTicks = $Ticks } }
# A parsed, well-formed lock object.
function New-Lock { param($LockPid, $ProcStart) [pscustomobject]@{ pid = $LockPid; procStart = $ProcStart } }

# Idle baseline: nothing running, repo quiet, work pending. Each row overrides as needed.
function Base { @{
    LockData            = $null
    SentinelExists      = $false
    LiveProcess         = $null
    AutoFirmProcessLive = $false
    RepoRecentlyActive  = $false
    HasPendingWork      = $true
} }

Write-Host "=== Get-WatchdogAction decision table ===" -ForegroundColor Cyan

# 1. ACTIVE PROCESS -> NO-OP (the headline safety case: a live build holding no lock).
$s = Base; $s.AutoFirmProcessLive = $true
Assert-Action 'active-process -> ALREADY_ACTIVE' 'ALREADY_ACTIVE' $s

# active process wins even with a clean idle repo AND pending work present.
$s = Base; $s.AutoFirmProcessLive = $true; $s.HasPendingWork = $true; $s.RepoRecentlyActive = $false
Assert-Action 'active-process beats idle+pending' 'ALREADY_ACTIVE' $s

# 2. LIVE LOCK (identity matches) -> NO-OP.
$s = Base; $s.LockData = (New-Lock 4242 123456789); $s.LiveProcess = (New-Live 123456789)
Assert-Action 'live-lock identity-match -> ALREADY_ACTIVE' 'ALREADY_ACTIVE' $s

# 3. COMPLETE SENTINEL -> NO-OP (wins over everything, even a live process).
$s = Base; $s.SentinelExists = $true; $s.AutoFirmProcessLive = $true
Assert-Action 'sentinel -> COMPLETE (beats live process)' 'COMPLETE' $s

# 4. RECYCLED-PID LOCK -> ignored (PID live but start token differs) -> RESUME when idle+pending.
$s = Base; $s.LockData = (New-Lock 4242 111111111); $s.LiveProcess = (New-Live 999999999)
Assert-Action 'recycled-PID lock ignored -> RESUME' 'RESUME' $s

# 4b. dead-PID lock (no live process) -> ignored -> RESUME when idle+pending.
$s = Base; $s.LockData = (New-Lock 4242 111111111); $s.LiveProcess = $null
Assert-Action 'dead-PID lock ignored -> RESUME' 'RESUME' $s

# 5. CORRUPT LOCK -> REFUSE_AMBIGUOUS (fail closed; cannot prove no run).
$s = Base; $s.LockData = 'CORRUPT'
Assert-Action 'corrupt lock -> REFUSE_AMBIGUOUS' 'REFUSE_AMBIGUOUS' $s

# 5b. structurally-invalid lock (missing procStart) -> REFUSE_AMBIGUOUS.
$s = Base; $s.LockData = ([pscustomobject]@{ pid = 4242 })
Assert-Action 'lock missing procStart -> REFUSE_AMBIGUOUS' 'REFUSE_AMBIGUOUS' $s

# 5c. structurally-invalid lock (missing pid) -> REFUSE_AMBIGUOUS.
$s = Base; $s.LockData = ([pscustomobject]@{ procStart = 123 })
Assert-Action 'lock missing pid -> REFUSE_AMBIGUOUS' 'REFUSE_AMBIGUOUS' $s

# 6. REPO RECENTLY ACTIVE -> NO-OP (someone is working even with no process/lock).
$s = Base; $s.RepoRecentlyActive = $true
Assert-Action 'repo recently committed -> ALREADY_ACTIVE' 'ALREADY_ACTIVE' $s

# 7. NO PENDING WORK -> COMPLETE (idle and nothing left to do; never spin).
$s = Base; $s.HasPendingWork = $false
Assert-Action 'idle + no pending work -> COMPLETE' 'COMPLETE' $s

# 8. AMBIGUOUS PENDING WORK ($null) while idle -> REFUSE (never resume on a guess).
$s = Base; $s.HasPendingWork = $null
Assert-Action 'idle + indeterminate work -> REFUSE_AMBIGUOUS' 'REFUSE_AMBIGUOUS' $s

# 9. THE ONLY RESUME: idle, no sentinel, no process, no live/own lock, no recent commit,
#    work definitely pending.
$s = Base
Assert-Action 'idle + pending + stale -> RESUME (only resume case)' 'RESUME' $s

# 9b. RESUME still holds when an old dead lock is present but everything else is idle.
$s = Base; $s.LockData = (New-Lock 13 13); $s.LiveProcess = $null
Assert-Action 'idle + pending + stale dead-lock -> RESUME' 'RESUME' $s

# --- adversarial composition: a live process must NEVER yield RESUME, regardless of the
#     rest of the state (the property that matters most while W1/W2 are live).
foreach ($pend in @($true, $false, $null)) {
    foreach ($recent in @($true, $false)) {
        $s = Base; $s.AutoFirmProcessLive = $true; $s.HasPendingWork = $pend; $s.RepoRecentlyActive = $recent
        $r = Get-WatchdogAction -LockData $s.LockData -SentinelExists $s.SentinelExists -LiveProcess $s.LiveProcess `
             -AutoFirmProcessLive $s.AutoFirmProcessLive -RepoRecentlyActive $s.RepoRecentlyActive -HasPendingWork $s.HasPendingWork
        if ($r -eq 'RESUME') {
            $script:Failures.Add("FAIL invariant: live process produced RESUME (pend=$pend recent=$recent)")
            Write-Host "  FAIL invariant: live process -> RESUME (pend=$pend recent=$recent)" -ForegroundColor Red
        } else { $script:Passes++ }
    }
}
Write-Host ("  PASS  invariant: live process never RESUMEs (6 combos)") -ForegroundColor Green

# --- summary / exit code (this is what gates CI) ---------------------------------------
Write-Host ""
if ($script:Failures.Count -eq 0) {
    Write-Host ("ALL GREEN: {0} assertions passed." -f $script:Passes) -ForegroundColor Green
    exit 0
}
else {
    Write-Host ("RED: {0} passed, {1} FAILED." -f $script:Passes, $script:Failures.Count) -ForegroundColor Red
    $script:Failures | ForEach-Object { Write-Host ("  - " + $_) -ForegroundColor Red }
    exit 1
}
