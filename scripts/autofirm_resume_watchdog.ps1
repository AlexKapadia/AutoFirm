#requires -Version 5.1
<#
.SYNOPSIS
    AutoFirm auto-resume watchdog (CLAUDE.md §4.8 option (b), the ROBUST OS-level one).

.DESCRIPTION
    Idempotent, FAIL-CLOSED guard run on a Windows Task Scheduler heartbeat (~45 min).
    Its ONLY job is resilience: if the autonomous build stalls on a quota reset, a
    crash, or full session death, this re-launches it once usage returns -- WITHOUT
    ever starting a runaway second concurrent run.

    Each tick decides exactly one of four actions (CLAUDE.md §4.8 + §5.6 fail-closed):
      ALREADY_ACTIVE   -> a live, identity-matched run holds the lock  -> do nothing
      COMPLETE         -> the BUILD_COMPLETE sentinel exists           -> do nothing
      RESUME           -> no live run, not complete, lock state clean  -> relaunch once
      REFUSE_AMBIGUOUS -> lock missing/corrupt/unparseable             -> REFUSE to launch

    The decision is factored into the PURE function Get-WatchdogAction so it is fully
    unit-testable with zero side effects and zero real process/file access (the caller
    injects the lock content, the sentinel flag, and a "live process" descriptor).

    WHY a recycled-PID guard: a PID is reused by the OS after a process exits. A stale
    lock whose PID now belongs to an UNRELATED process must NOT read as "active" (that
    would wedge the build forever). We therefore record the process START TIME at lock
    time and require BOTH a live PID AND a matching start time before trusting the lock.

.PARAMETER RepoPath
    Absolute path to the AutoFirm repo whose build this watchdog guards.
    Defaults to the MAIN checkout; the scheduler passes it explicitly.

.PARAMETER DryRun
    Resolve the action and log it, but DO NOT spawn the resume session. Used by tests
    and by operators verifying the wiring -- so no test can ever launch a real session.

.NOTES
    Security: no secrets are read, written, or logged here (CLAUDE.md §5.6). The lock
    holds only a session id, a PID, a process-start token, and timestamps.
    This script NEVER edits code, tests, or docs. It is read-only except for its own
    log file and (on RESUME) the act of spawning the build process.
#>
[CmdletBinding()]
param(
    [string] $RepoPath = 'C:/dev/AutoFirm',
    [switch] $DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# --- Layout constants (all machine-local; .autofirm/ is git-fenced, see .gitignore) ---
$script:LockRelPath     = '.autofirm/watchdog.lock'        # this watchdog's own lock
$script:SentinelRelPath = '.autofirm/BUILD_COMPLETE'       # build-finished sentinel
$script:LogRelPath      = '.autofirm/logs/watchdog.log'    # append-only operator log


function Get-WatchdogAction {
    <#
    .SYNOPSIS
        PURE decision function: given injected state, return the action to take.
    .DESCRIPTION
        No file or process access here -- every input is a parameter so the full
        decision table is unit-testable. Returns exactly one of:
        ALREADY_ACTIVE | COMPLETE | RESUME | REFUSE_AMBIGUOUS.

        Order of checks (fail-closed where state is unclear):
          1. COMPLETE wins outright -- if the build already finished, never relaunch.
          2. No lock at all -> genuinely idle -> RESUME (nothing is running).
          3. Lock present but corrupt/unparseable -> REFUSE_AMBIGUOUS (can't prove
             a run is NOT active, so we must not risk a second one -- fail closed).
          4. Lock present + a live process whose identity MATCHES -> ALREADY_ACTIVE.
          5. Lock present but process dead, or live with a MISMATCHED start time
             (recycled PID), or live with no start token to compare -> the original
             run is gone -> RESUME.
    .PARAMETER LockData
        $null when no lock file exists; [pscustomobject] with pid/procStart when a
        lock exists and parsed cleanly; the string 'CORRUPT' when a lock file exists
        but could not be parsed.
    .PARAMETER SentinelExists
        $true when the BUILD_COMPLETE sentinel is present.
    .PARAMETER LiveProcess
        $null when the recorded PID is not currently a running process; otherwise a
        [pscustomobject] with a StartTicks property for the live PID. The caller is
        responsible for the (PID -> live process) lookup so this function stays pure.
    #>
    [CmdletBinding()]
    [OutputType([string])]
    param(
        [Parameter(Mandatory = $true)] [AllowNull()] $LockData,
        [Parameter(Mandatory = $true)] [bool] $SentinelExists,
        [Parameter(Mandatory = $true)] [AllowNull()] $LiveProcess
    )

    # 1. COMPLETE wins outright: a finished build must never be relaunched. (fail-safe)
    if ($SentinelExists) { return 'COMPLETE' }

    # 2. No lock -> nothing is running -> safe to resume.
    if ($null -eq $LockData) { return 'RESUME' }

    # 3. Lock exists but is corrupt/unparseable -> we CANNOT prove no run is active.
    #    Fail closed: refuse rather than risk a second concurrent run (CLAUDE.md §5.6).
    if ($LockData -is [string] -and $LockData -eq 'CORRUPT') { return 'REFUSE_AMBIGUOUS' }

    # A parsed lock MUST carry both a PID and a process-start token to be trustworthy.
    # Missing either field means the lock is structurally invalid -> fail closed.
    $hasPid   = ($LockData.PSObject.Properties.Name -contains 'pid')       -and ($null -ne $LockData.pid)
    $hasStart = ($LockData.PSObject.Properties.Name -contains 'procStart') -and ($null -ne $LockData.procStart)
    if (-not $hasPid -or -not $hasStart) { return 'REFUSE_AMBIGUOUS' }

    # 4./5. The recorded PID is not live -> the run that held the lock is gone -> RESUME.
    if ($null -eq $LiveProcess) { return 'RESUME' }

    # The PID IS live -- but is it the SAME process, or a recycled PID? Compare the
    # process-start token. A live process with no comparable start token is ambiguous,
    # but a recycled PID is the more dangerous failure (it would wedge us as "active"
    # forever), so we treat a missing/zero start token as NOT a match -> RESUME.
    $liveTicks   = if ($LiveProcess.PSObject.Properties.Name -contains 'StartTicks') { $LiveProcess.StartTicks } else { $null }
    $lockedTicks = $LockData.procStart

    if (($null -ne $liveTicks) -and ("$liveTicks" -eq "$lockedTicks")) {
        # Live PID AND matching start time -> genuinely the same run -> do nothing.
        return 'ALREADY_ACTIVE'
    }

    # Live PID but start time differs (or is absent) -> a DIFFERENT process now owns
    # this PID. The original run is gone -> RESUME. (recycled-PID guard)
    return 'RESUME'
}


function Read-WatchdogLock {
    <#
    .SYNOPSIS
        Side-effecting adapter: read the lock file and normalise it for the pure fn.
    .OUTPUTS
        $null            when no lock file exists,
        'CORRUPT'        when the file exists but is not parseable JSON with a pid,
        [pscustomobject] (the parsed lock) otherwise.
    #>
    param([Parameter(Mandatory = $true)][string] $Path)

    if (-not (Test-Path -LiteralPath $Path)) { return $null }
    try {
        $raw = Get-Content -LiteralPath $Path -Raw -ErrorAction Stop
        if ([string]::IsNullOrWhiteSpace($raw)) { return 'CORRUPT' }   # empty -> ambiguous
        return ($raw | ConvertFrom-Json -ErrorAction Stop)
    }
    catch {
        # Unparseable lock -> ambiguous, NOT idle. Surface as CORRUPT so the pure
        # decision fails closed rather than mistaking a broken lock for "no run".
        return 'CORRUPT'
    }
}


function Get-LiveProcessDescriptor {
    <#
    .SYNOPSIS
        Side-effecting adapter: look up a PID and return a {StartTicks} descriptor.
    .OUTPUTS
        $null when the PID is not a running process, else a [pscustomobject] with the
        live process's StartTime ticks (the identity token compared against the lock).
    #>
    param([Parameter(Mandatory = $true)] $ProcessId)

    if ($null -eq $ProcessId) { return $null }
    try {
        $proc = Get-Process -Id ([int]$ProcessId) -ErrorAction Stop
    }
    catch {
        return $null   # PID not running -> caller treats the run as gone.
    }
    $ticks = $null
    try { $ticks = $proc.StartTime.Ticks } catch { $ticks = $null }  # access can be denied
    return [pscustomobject]@{ StartTicks = $ticks }
}


function Write-WatchdogLog {
    <#
    .SYNOPSIS
        Append one structured line to the operator log. No secrets ever (CLAUDE.md §5.6).
    #>
    param(
        [Parameter(Mandatory = $true)][string] $LogPath,
        [Parameter(Mandatory = $true)][string] $Action,
        [Parameter(Mandatory = $true)][string] $Message
    )
    $dir = Split-Path -Parent $LogPath
    if (-not (Test-Path -LiteralPath $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
    $stamp = (Get-Date).ToString('o')
    $line  = '{0} [{1}] {2}' -f $stamp, $Action, $Message
    Add-Content -LiteralPath $LogPath -Value $line
}


function Get-ResumeCommand {
    <#
    .SYNOPSIS
        The EXACT command used to resume the autonomous build (documented, not hidden).
    .DESCRIPTION
        Resume state is derived from git + the task list + the roadmap doc (CLAUDE.md
        §4.8), so the resumed agent picks up exactly where it left off. We use the
        Claude Code CLI's --continue (resume the most recent conversation in this repo)
        with -p so it runs non-interactively and headless on the scheduler.
    .OUTPUTS
        A [pscustomobject] { Exe; ArgList } -- returned (not executed) so it is testable
        and so RESUME under -DryRun can log the precise command without spawning it.
    #>
    param([Parameter(Mandatory = $true)][string] $Repo)

    $prompt = 'Resume the autonomous AutoFirm build from current git state, the task ' +
              'list, and docs/roadmap.md. Continue from the next unmet roadmap gate; ' +
              'do not restart completed work. Honour CLAUDE.md.'
    return [pscustomobject]@{
        Exe     = 'claude'
        ArgList = @('--continue', '-p', $prompt, '--permission-mode', 'acceptEdits')
        # Working directory is the repo root so --continue resolves THIS project's
        # most-recent session and git/roadmap state.
        WorkDir = $Repo
    }
}


function Invoke-AutofirmWatchdog {
    <#
    .SYNOPSIS
        Top-level tick: gather real state, decide via the pure fn, act fail-closed.
    .OUTPUTS
        The resolved action string (also written to the log).
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string] $Repo,
        [switch] $NoLaunch
    )

    $lockPath     = Join-Path $Repo $script:LockRelPath
    $sentinelPath = Join-Path $Repo $script:SentinelRelPath
    $logPath      = Join-Path $Repo $script:LogRelPath

    $lockData       = Read-WatchdogLock -Path $lockPath
    $sentinelExists = Test-Path -LiteralPath $sentinelPath
    $live           = $null
    if (($null -ne $lockData) -and ($lockData -isnot [string])) {
        $lockedPid = if ($lockData.PSObject.Properties.Name -contains 'pid') { $lockData.pid } else { $null }
        $live = Get-LiveProcessDescriptor -ProcessId $lockedPid
    }

    $action = Get-WatchdogAction -LockData $lockData -SentinelExists $sentinelExists -LiveProcess $live

    switch ($action) {
        'ALREADY_ACTIVE'   { Write-WatchdogLog -LogPath $logPath -Action $action -Message 'Live identity-matched run holds the lock; nothing to do.' }
        'COMPLETE'         { Write-WatchdogLog -LogPath $logPath -Action $action -Message 'BUILD_COMPLETE sentinel present; build is finished.' }
        'REFUSE_AMBIGUOUS' { Write-WatchdogLog -LogPath $logPath -Action $action -Message 'Lock missing fields/corrupt; cannot prove no run is active -> REFUSING to launch (fail-closed).' }
        'RESUME' {
            $cmd = Get-ResumeCommand -Repo $Repo
            $printable = '{0} {1}' -f $cmd.Exe, ($cmd.ArgList -join ' ')
            if ($NoLaunch) {
                Write-WatchdogLog -LogPath $logPath -Action 'RESUME-DRYRUN' -Message ("Would launch: " + $printable)
            }
            else {
                Write-WatchdogLog -LogPath $logPath -Action $action -Message ("Launching resume: " + $printable)
                Start-Process -FilePath $cmd.Exe -ArgumentList $cmd.ArgList -WorkingDirectory $cmd.WorkDir -WindowStyle Hidden
            }
        }
    }
    return $action
}


# --- Entry point: only run the tick when invoked directly (not when dot-sourced by ---
# --- tests). $MyInvocation.InvocationName is '.' under dot-sourcing.                 ---
if ($MyInvocation.InvocationName -ne '.') {
    $resolvedRepo = (Resolve-Path -LiteralPath $RepoPath).Path
    $result = Invoke-AutofirmWatchdog -Repo $resolvedRepo -NoLaunch:$DryRun
    Write-Output $result
}
