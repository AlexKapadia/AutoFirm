#requires -Version 5.1
<#
.SYNOPSIS
    AutoFirm auto-resume watchdog (CLAUDE.md §4.8 option (b), the ROBUST OS-level one).

.DESCRIPTION
    Idempotent, FAIL-CLOSED guard run on a Windows Task Scheduler heartbeat (~45 min).
    Its ONLY job is resilience: if the autonomous build stalls on a quota reset, a
    crash, or full session death, this re-launches it once usage returns -- WITHOUT
    ever starting a runaway second concurrent run.

    SAFETY MODEL (why the detection is layered, not lock-only)
    ----------------------------------------------------------
    A lock-file-only check is NOT safe here: an AutoFirm build is just a `claude` CLI
    session that this watchdog did NOT start, so it may hold NO watchdog lock at all.
    If we resumed merely because "no lock", we could spawn a SECOND concurrent build
    on top of a live one -- the worst possible failure (CLAUDE.md §4.8). We therefore
    treat the run as ACTIVE (-> NO-OP) if ANY of these independent signals hold:

      (S) the BUILD_COMPLETE sentinel exists            -> COMPLETE  (work is done)
      (L) the watchdog.lock holds a LIVE, identity-      -> ALREADY_ACTIVE
          matched PID (recycled-PID-guarded)
      (P) a live process references an AutoFirm path,    -> ALREADY_ACTIVE
          OR a live `claude` CLI-agent process exists
          that we cannot prove is unrelated
      (R) the repo committed more recently than the      -> ALREADY_ACTIVE
          stale-idle threshold (someone is working)

    We RESUME on EXACTLY ONE combination: none of S/L/P/R hold (genuinely idle) AND
    there is real pending work (git/roadmap/task-list incomplete). Every other state,
    including any ambiguity (corrupt lock, unreadable process table, indeterminate
    work state), resolves to NO-OP / REFUSE -- fail closed (CLAUDE.md §5.6).

    WHY a `claude` CLI process counts as "active": on Windows we cannot read another
    process's working directory from a LIMITED-rights scheduled task without admin
    tooling. Rather than guess, we fail closed: if an AutoFirm-capable agent binary is
    running at all, we do NOT launch -- the cost of a missed tick is one more 45-min
    wait, the cost of a false RESUME is a duplicate concurrent build. (Asymmetric risk.)

    The decision is factored into the PURE function Get-WatchdogAction so it is fully
    unit-testable with zero side effects and zero real process/file access (the caller
    injects every signal). The DECISION LOCK (write-before-launch) lives in the impure
    Invoke-AutofirmWatchdog so two scheduler ticks can never double-launch.

.PARAMETER RepoPath
    Absolute path to the AutoFirm repo whose build this watchdog guards.

.PARAMETER DryRun
    Resolve the action and log it, but DO NOT spawn the resume session and DO NOT take
    the decision lock. Used by tests and by operators verifying wiring while live builds
    run -- so no dry-run can ever launch a real session or disturb a running build.

.NOTES
    Security: no secrets are read, written, or logged (CLAUDE.md §5.6). The lock holds
    only a session id, a PID, a process-start token, and timestamps. This script NEVER
    edits code, tests, or docs; it is read-only except its own log/lock and (on RESUME)
    spawning the build process.
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

# Repo is "idle enough to maybe resume" only after this long with no new commit AND no
# AutoFirm-referencing process. 90 min comfortably exceeds one 45-min scheduler period,
# so a build that is merely between commits is never mistaken for a dead one.
$script:StaleIdleMinutes = 90


function Get-WatchdogAction {
    <#
    .SYNOPSIS
        PURE decision function: given injected signals, return the action to take.
    .DESCRIPTION
        No file/process/git access here -- every input is a parameter so the full
        decision table is unit-testable. Returns exactly one of:
        ALREADY_ACTIVE | COMPLETE | RESUME | REFUSE_AMBIGUOUS.

        Order of checks (fail-closed wherever state is unclear):
          1. COMPLETE wins outright -- a finished build is never relaunched.
          2. AutoFirmProcessLive -> a build-capable process is running -> ALREADY_ACTIVE.
             (covers a live build that holds NO watchdog lock -- the key safety case.)
          3. Lock present + corrupt/unparseable -> REFUSE_AMBIGUOUS (can't prove no run).
          4. Lock present + missing required fields -> REFUSE_AMBIGUOUS.
          5. Lock present + a live process whose identity MATCHES -> ALREADY_ACTIVE.
          6. RepoRecentlyActive (committed within the stale window) -> ALREADY_ACTIVE.
          7. NoPendingWork -> nothing to resume -> COMPLETE (treat as done; never spin).
          8. Otherwise (idle, no live run, work pending) -> RESUME. <-- the ONLY resume.

        Note checks 2 and 6 are deliberately BEFORE the lock-field checks: a real live
        build (process or recent commit) must read as active even if its lock is absent
        or malformed, because the lock belongs to the watchdog, not to the build.
    .PARAMETER LockData
        $null when no lock file exists; [pscustomobject] with pid/procStart when a lock
        parsed cleanly; the string 'CORRUPT' when a lock exists but did not parse.
    .PARAMETER SentinelExists
        $true when the BUILD_COMPLETE sentinel is present.
    .PARAMETER LiveProcess
        $null when the LOCK's recorded PID is not running; else a [pscustomobject] with a
        StartTicks property. The caller does the (PID -> live process) lookup so this
        function stays pure.
    .PARAMETER AutoFirmProcessLive
        $true when the caller detected ANY live process that references an AutoFirm path
        or is an AutoFirm-capable agent binary we cannot prove unrelated (fail-closed).
    .PARAMETER RepoRecentlyActive
        $true when the repo's HEAD commit is younger than the stale-idle threshold.
    .PARAMETER HasPendingWork
        $true when git/roadmap/task-list show incomplete work; $false when none remains;
        $null when the caller could not determine it (treated as ambiguous -> no resume).
    #>
    [CmdletBinding()]
    [OutputType([string])]
    param(
        [Parameter(Mandatory = $true)] [AllowNull()] $LockData,
        [Parameter(Mandatory = $true)] [bool] $SentinelExists,
        [Parameter(Mandatory = $true)] [AllowNull()] $LiveProcess,
        [Parameter(Mandatory = $true)] [bool] $AutoFirmProcessLive,
        [Parameter(Mandatory = $true)] [bool] $RepoRecentlyActive,
        [Parameter(Mandatory = $true)] [AllowNull()] $HasPendingWork
    )

    # 1. COMPLETE wins outright: a finished build must never be relaunched. (fail-safe)
    if ($SentinelExists) { return 'COMPLETE' }

    # 2. ANY live AutoFirm-capable process -> a build may be running RIGHT NOW even with
    #    no lock of ours. This is the primary guard against a second concurrent run.
    if ($AutoFirmProcessLive) { return 'ALREADY_ACTIVE' }

    # 3. Lock exists but is corrupt/unparseable -> we CANNOT prove no run is active.
    #    Fail closed: refuse rather than risk a second concurrent run (CLAUDE.md §5.6).
    if ($LockData -is [string] -and $LockData -eq 'CORRUPT') { return 'REFUSE_AMBIGUOUS' }

    # 4. A parsed lock MUST carry both a PID and a process-start token to be trustworthy.
    #    (Only enforced when a lock object actually exists; $null lock = no lock, fine.)
    if ($null -ne $LockData) {
        $hasPid   = ($LockData.PSObject.Properties.Name -contains 'pid')       -and ($null -ne $LockData.pid)
        $hasStart = ($LockData.PSObject.Properties.Name -contains 'procStart') -and ($null -ne $LockData.procStart)
        if (-not $hasPid -or -not $hasStart) { return 'REFUSE_AMBIGUOUS' }

        # 5. Lock PID live AND start-token matches -> genuinely the same run -> NO-OP.
        if ($null -ne $LiveProcess) {
            $liveTicks = if ($LiveProcess.PSObject.Properties.Name -contains 'StartTicks') { $LiveProcess.StartTicks } else { $null }
            if (($null -ne $liveTicks) -and ("$liveTicks" -eq "$($LockData.procStart)")) {
                return 'ALREADY_ACTIVE'
            }
            # Live PID but start differs/absent -> recycled PID, original run gone -> fall through.
        }
        # Lock PID not live -> the run that held the lock is gone -> fall through to resume gate.
    }

    # 6. The repo committed within the stale window -> someone is actively working it,
    #    even if no process matched our filters and no lock is held -> NO-OP.
    if ($RepoRecentlyActive) { return 'ALREADY_ACTIVE' }

    # 7. No live run and the work is genuinely finished -> COMPLETE (never spin on a
    #    repo with nothing to do). $null (indeterminate) is NOT $true -> falls through
    #    to the final fail-closed REFUSE rather than resuming on a guess.
    if ($HasPendingWork -eq $false) { return 'COMPLETE' }

    # 8. THE ONLY RESUME PATH: idle (no sentinel, no live process, no live/own lock, no
    #    recent commit) AND pending work is definitely present. Anything ambiguous about
    #    pending work ($null) lands here as REFUSE, not RESUME -- fail closed.
    if ($HasPendingWork -eq $true) { return 'RESUME' }
    return 'REFUSE_AMBIGUOUS'
}


function Read-WatchdogLock {
    <#
    .SYNOPSIS
        Side-effecting adapter: read the lock file and normalise it for the pure fn.
    .OUTPUTS
        $null            when no lock file exists,
        'CORRUPT'        when the file exists but is not parseable JSON,
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
        $null when the PID is not running, else a [pscustomobject] with the live
        process's StartTime ticks (the identity token compared against the lock).
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


function Test-AutofirmProcessLive {
    <#
    .SYNOPSIS
        Side-effecting adapter: is ANY live process an AutoFirm build, or build-capable?
    .DESCRIPTION
        Returns $true (fail-closed) if EITHER:
          (a) a live process's command line or executable path references an AutoFirm
              path (the repo root or any sibling worktree, matched case-insensitively); OR
          (b) a live `claude` CLI-AGENT process exists (the agent binary, NOT the desktop
              app and NOT this watchdog's own PID). We cannot read an arbitrary process's
              CWD from a limited-rights task, so we refuse to launch while ANY agent runs.
        Also returns $true (fail-closed) if the process table itself cannot be read.
    .PARAMETER RepoPath
        The guarded repo path; its parent dir is used to recognise sibling worktrees
        (e.g. AutoFirm-w2, AutoFirm-watchdog) without hard-coding any names.
    .PARAMETER SelfPid
        This watchdog's own PID, excluded so the watchdog never sees itself as the build.
    #>
    param(
        [Parameter(Mandatory = $true)][string] $RepoPath,
        [Parameter(Mandatory = $true)][int]    $SelfPid
    )

    # Build a case-insensitive needle from the repo's own folder name (e.g. "autofirm"),
    # so this matches the main checkout AND every sibling worktree (AutoFirm-w2, etc.)
    # without baking in project-specific names (CLAUDE.md: keep it general).
    $leaf = Split-Path -Leaf ($RepoPath.TrimEnd('\', '/'))
    $needle = $leaf.ToLowerInvariant()

    try {
        $procs = Get-CimInstance Win32_Process -Filter "Name='claude.exe' OR Name='node.exe'" -ErrorAction Stop
    }
    catch {
        # Cannot enumerate processes -> we cannot prove no build is running -> fail closed.
        return $true
    }

    foreach ($p in $procs) {
        if ($p.ProcessId -eq $SelfPid) { continue }   # never count ourselves

        $cmd  = if ($p.CommandLine)    { $p.CommandLine.ToLowerInvariant() }    else { '' }
        $exe  = if ($p.ExecutablePath) { $p.ExecutablePath.ToLowerInvariant() } else { '' }

        # (a) explicit AutoFirm reference anywhere in the command line / exe path.
        if ($cmd.Contains($needle) -or $exe.Contains($needle)) { return $true }

        # (b) a `claude` CLI-AGENT binary (excludes the WindowsApps desktop app, which
        #     never drives a headless build). Its CWD is unknowable to us, so fail closed.
        if ($p.Name -eq 'claude.exe' -and $exe -notlike '*windowsapps*' -and $exe -like '*claude.exe') {
            return $true
        }
    }
    return $false
}


function Test-RepoRecentlyActive {
    <#
    .SYNOPSIS
        Side-effecting adapter: did the repo commit within the stale-idle window?
    .DESCRIPTION
        Reads the HEAD committer timestamp via git. A repo that just committed is being
        worked on -- treat as active. On ANY git error we return $true (fail-closed:
        better to skip a tick than risk launching over a live build).
    #>
    param(
        [Parameter(Mandatory = $true)][string] $RepoPath,
        [Parameter(Mandatory = $true)][int]    $StaleMinutes
    )
    try {
        $epoch = & git -C $RepoPath log -1 --format=%ct 2>$null
        if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($epoch)) { return $true }
        $commitTime = [DateTimeOffset]::FromUnixTimeSeconds([long]$epoch).UtcDateTime
        $ageMin = ([DateTime]::UtcNow - $commitTime).TotalMinutes
        return ($ageMin -lt $StaleMinutes)
    }
    catch {
        return $true   # cannot determine recency -> fail closed (assume active).
    }
}


function Get-PendingWorkState {
    <#
    .SYNOPSIS
        Side-effecting adapter: is there genuinely incomplete work to resume?
    .OUTPUTS
        $true  when work clearly remains (uncommitted changes, OR a roadmap/task-list
               with unchecked items),
        $false when no signal of remaining work is found,
        $null  when the state cannot be determined (treated as ambiguous -> no resume).
    .DESCRIPTION
        Resume state is derived from git + the roadmap + the task list (CLAUDE.md §4.8).
        A "[ ]" unchecked checkbox in docs/roadmap.md (or a tracked TODO/task file) is
        the durable "work remains" signal. We are conservative: unknown -> $null, so the
        pure fn never RESUMEs on a guess.
    #>
    param([Parameter(Mandatory = $true)][string] $RepoPath)

    try {
        # Uncommitted tracked changes = work in flight that a resumed agent should finish.
        $dirty = & git -C $RepoPath status --porcelain 2>$null
        if ($LASTEXITCODE -ne 0) { return $null }
        if (-not [string]::IsNullOrWhiteSpace($dirty)) { return $true }
    }
    catch { return $null }

    # Unchecked roadmap items = pending gates. Look at the roadmap, then any task list.
    $candidates = @('docs/roadmap.md', 'docs/ROADMAP.md', 'ROADMAP.md', 'docs/tasks.md')
    $sawAnyDoc = $false
    foreach ($rel in $candidates) {
        $full = Join-Path $RepoPath $rel
        if (Test-Path -LiteralPath $full) {
            $sawAnyDoc = $true
            try {
                $text = Get-Content -LiteralPath $full -Raw -ErrorAction Stop
                if ($text -match '(?m)^\s*[-*]\s*\[\s\]') { return $true }   # an unchecked "[ ]" box
            }
            catch { return $null }
        }
    }
    # Docs existed and none had open items -> work looks done. No docs at all -> unknown.
    if ($sawAnyDoc) { return $false }
    return $null
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
        §4.8) -- passed EXPLICITLY in the prompt so we do not rely on a bare
        `claude --continue` resolving the right session when several exist. We still use
        --continue to reuse the most-recent in-repo conversation, but the prompt pins the
        agent to the next unmet roadmap gate so the target is unambiguous.
    .OUTPUTS
        A [pscustomobject] { Exe; ArgList; WorkDir } -- returned (not executed) so it is
        testable and so RESUME under -DryRun can log the precise command without spawning.
    #>
    param([Parameter(Mandatory = $true)][string] $Repo)

    $prompt = 'Resume the autonomous AutoFirm build. Read current git state (branch, ' +
              'log, status), docs/roadmap.md, and the task list, then continue from the ' +
              'NEXT UNMET roadmap gate only -- do not restart completed work and do not ' +
              'start a second concurrent run. Honour CLAUDE.md in full.'
    return [pscustomobject]@{
        Exe     = 'claude'
        ArgList = @('--continue', '-p', $prompt, '--permission-mode', 'acceptEdits')
        WorkDir = $Repo   # repo root so --continue resolves THIS project's session/state.
    }
}


function Test-DecisionLockAcquired {
    <#
    .SYNOPSIS
        Atomically claim the right to launch by writing the watchdog lock BEFORE spawning.
    .DESCRIPTION
        Two scheduler ticks must never both launch. We create the lock file with
        CreateNew semantics (.NET FileMode::CreateNew throws if it already exists), so the
        first tick wins and any racing tick fails to acquire and refuses to launch. The
        lock records THIS watchdog's PID + process-start token + timestamp so the next
        tick's recycled-PID guard can validate it. Returns $true iff WE took the lock.
    .OUTPUTS
        $true when this process created the lock (clear to launch); $false otherwise.
    #>
    param([Parameter(Mandatory = $true)][string] $LockPath)

    $dir = Split-Path -Parent $LockPath
    if (-not (Test-Path -LiteralPath $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }

    $self = Get-Process -Id $PID
    $payload = [pscustomobject]@{
        sessionId = [guid]::NewGuid().ToString()
        pid       = $PID
        procStart = $self.StartTime.Ticks      # recycled-PID guard token
        stamp     = (Get-Date).ToString('o')
        note      = 'held by autofirm_resume_watchdog resume launch'
    } | ConvertTo-Json -Compress

    try {
        # CreateNew = exclusive create; throws if the lock already exists -> we lose the race.
        $fs = [System.IO.File]::Open($LockPath, [System.IO.FileMode]::CreateNew,
                                     [System.IO.FileAccess]::Write, [System.IO.FileShare]::None)
        try {
            $bytes = [System.Text.Encoding]::UTF8.GetBytes($payload)
            $fs.Write($bytes, 0, $bytes.Length)
        }
        finally { $fs.Dispose() }
        return $true
    }
    catch {
        return $false   # lock already exists / could not create -> do NOT launch. Fail closed.
    }
}


function Invoke-AutofirmWatchdog {
    <#
    .SYNOPSIS
        Top-level tick: gather real state, decide via the pure fn, act fail-closed.
    .OUTPUTS
        The resolved action string (also written to the log). On RESUME, returns
        'RESUME' only if the decision lock was taken AND launch occurred (or DryRun);
        returns 'REFUSE_LOCK_LOST' if a racing tick already holds the lock.
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

    $live = $null
    if (($null -ne $lockData) -and ($lockData -isnot [string])) {
        $lockedPid = if ($lockData.PSObject.Properties.Name -contains 'pid') { $lockData.pid } else { $null }
        $live = Get-LiveProcessDescriptor -ProcessId $lockedPid
    }

    $procLive    = Test-AutofirmProcessLive -RepoPath $Repo -SelfPid $PID
    $repoActive  = Test-RepoRecentlyActive -RepoPath $Repo -StaleMinutes $script:StaleIdleMinutes
    $pendingWork = Get-PendingWorkState -RepoPath $Repo

    $action = Get-WatchdogAction `
        -LockData $lockData `
        -SentinelExists $sentinelExists `
        -LiveProcess $live `
        -AutoFirmProcessLive $procLive `
        -RepoRecentlyActive $repoActive `
        -HasPendingWork $pendingWork

    switch ($action) {
        'ALREADY_ACTIVE'   { Write-WatchdogLog -LogPath $logPath -Action $action -Message 'A live AutoFirm run/process/recent-commit was detected; nothing to do.' }
        'COMPLETE'         { Write-WatchdogLog -LogPath $logPath -Action $action -Message 'Build complete (sentinel present or no pending work); not relaunching.' }
        'REFUSE_AMBIGUOUS' { Write-WatchdogLog -LogPath $logPath -Action $action -Message 'State ambiguous (corrupt/invalid lock or indeterminate work) -> REFUSING to launch (fail-closed).' }
        'RESUME' {
            $cmd = Get-ResumeCommand -Repo $Repo
            $printable = '{0} {1}' -f $cmd.Exe, ($cmd.ArgList -join ' ')
            if ($NoLaunch) {
                Write-WatchdogLog -LogPath $logPath -Action 'RESUME-DRYRUN' -Message ("Would launch (no lock taken under DryRun): " + $printable)
            }
            else {
                # SAFETY: take the decision lock BEFORE launching. If a racing tick beat
                # us to it, we lose and refuse -- two ticks can never double-launch.
                if (Test-DecisionLockAcquired -LockPath $lockPath) {
                    Write-WatchdogLog -LogPath $logPath -Action $action -Message ("Decision lock acquired; launching resume: " + $printable)
                    Start-Process -FilePath $cmd.Exe -ArgumentList $cmd.ArgList -WorkingDirectory $cmd.WorkDir -WindowStyle Hidden
                }
                else {
                    $action = 'REFUSE_LOCK_LOST'
                    Write-WatchdogLog -LogPath $logPath -Action $action -Message 'Could not acquire decision lock (a racing tick holds it) -> NOT launching.'
                }
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
