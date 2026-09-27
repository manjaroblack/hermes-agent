# Insert the served-commit install-script pin into windows-e2e.ps1.
# The published Hermes-Setup.exe downloads NousResearch/hermes-agent main's
# install.ps1, which requires pm/lock.json. The commits this fork serves do
# not have that file. The pin points HERMES_SETUP_DEV_REPO_ROOT at the script
# from the commit serve.git is cloning.
param(
    [string]$Driver = ""
)


function Update-LaunchFromSpecCompletion {
    $launch = Join-Path $PSScriptRoot "launch-from-spec.mjs"
    if (-not (Test-Path -LiteralPath $launch)) {
        throw "enable-served-install-script: launch-from-spec.mjs not found at $launch"
    }
    $text = [System.IO.File]::ReadAllText($launch)
    $text = $text -replace "`r`n", "`n"
    if ($text.Contains("export function updateCompletionReached")) {
        Write-Host "update marker wait already present in $launch"
        return
    }
    $fn = @'
/**
 * Decide whether a desktop "Update now" hand-off is finished.
 *
 * The Windows updater claims HERMES_HOME/.hermes-update-in-progress before
 * it runs `hermes update`. That command checks out the target commit, then
 * renames venv\Scripts\hermes.exe to hermes.exe.old.* while it syncs
 * dependencies, and only restores the launcher when the update returns.
 * A SHA match during that window is not completion: the e2e driver would
 * tear the app down and assert on a launcher that is still quarantined.
 *
 * @param {{ resultExists: boolean, shaMatches: boolean, markerExists: boolean }} state
 * @returns {boolean}
 */
export function updateCompletionReached({ resultExists, shaMatches, markerExists }) {
  if (resultExists) return true;
  return Boolean(shaMatches && !markerExists);
}

/**
 * Marker written beside the hand-off result file.
 *
 * @param {string | undefined} resultPath
 * @returns {string}
 */
export function updateMarkerPath(resultPath) {
  if (!resultPath) return '';
  return path.join(path.dirname(resultPath), '.hermes-update-in-progress');
}

'@
    $old = @'
  const repoDir = values['repo-dir'];
  /** @returns {string} */
  const headSha = () => {
    try {
      return execFileSync('git', ['-C', /** @type {string} */ (repoDir), 'rev-parse', 'HEAD'], {
        encoding: 'utf8',
      }).trim();
    } catch {
      return '';
    }
  };
  for (;;) {
    if (resultPath && fs.existsSync(resultPath)) {
      log(`update result present: ${fs.readFileSync(resultPath, 'utf8').slice(0, 200)}`);
      break;
    }
    if (expectSha && repoDir && headSha() === expectSha) {
      log(`checkout reached expected sha ${expectSha}`);
      break;
    }
'@
    $new = @'
  const repoDir = values['repo-dir'];
  const markerPath = updateMarkerPath(resultPath);
  let loggedMarkerWait = false;
  /** @returns {string} */
  const headSha = () => {
    try {
      return execFileSync('git', ['-C', /** @type {string} */ (repoDir), 'rev-parse', 'HEAD'], {
        encoding: 'utf8',
      }).trim();
    } catch {
      return '';
    }
  };
  for (;;) {
    const resultExists = Boolean(resultPath && fs.existsSync(resultPath));
    const markerExists = Boolean(markerPath && fs.existsSync(markerPath));
    const shaMatches = Boolean(expectSha && repoDir && headSha() === expectSha);
    if (updateCompletionReached({ resultExists, shaMatches, markerExists })) {
      if (resultExists && resultPath) {
        log(`update result present: ${fs.readFileSync(resultPath, 'utf8').slice(0, 200)}`);
      } else {
        log(`checkout reached expected sha ${expectSha}`);
      }
      break;
    }
    if (markerExists && shaMatches && !loggedMarkerWait) {
      loggedMarkerWait = true;
      log('checkout is at the expected sha but the update marker is still held; waiting');
    }
'@
    $fn = $fn -replace "`r`n", "`n"
    $old = $old -replace "`r`n", "`n"
    $new = $new -replace "`r`n", "`n"
    $anchor = "/** @param {string} msg */`nfunction log(msg) {"
    if (-not $text.Contains($anchor)) {
        throw "enable-served-install-script: could not find the launch log function"
    }
    if (-not $text.Contains($old)) {
        throw "enable-served-install-script: could not find the sha-only update poll"
    }
    $text = $text.Replace($anchor, ($fn + $anchor))
    $text = $text.Replace($old, $new)
    $utf8 = New-Object System.Text.UTF8Encoding $false
    [System.IO.File]::WriteAllText($launch, $text, $utf8)
    Write-Host "launch-from-spec now waits for .hermes-update-in-progress"
}

$ErrorActionPreference = "Stop"
Update-LaunchFromSpecCompletion
if (-not $Driver) {
    $Driver = Join-Path $PSScriptRoot "..\windows-e2e.ps1"
}

$text = Get-Content -LiteralPath $Driver -Raw
if ($text -match 'function Set-ServedInstallScript') {
    Write-Host "served install script hook already present"
    exit 0
}

$function = @'
function Set-ServedInstallScript([string]$Ref) {
    # Hermes-Setup's dev-checkout hook. The published binary would otherwise
    # download NousResearch/hermes-agent main's install.ps1, which reads
    # pm/lock.json out of whatever tree the git redirect cloned.
    $helper = Join-Path $PSScriptRoot "e2e-assets\stage-served-install-scripts.sh"
    $bash = Join-Path $env:ProgramFiles "Git\bin\bash.exe"
    if (-not (Test-Path -LiteralPath $bash)) {
        $found = Get-Command bash.exe -ErrorAction SilentlyContinue
        if (-not $found) { throw "bash is required to stage the served install script" }
        $bash = $found.Source
    }
    $prevEap = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        $output = & $bash $helper ($RepoRoot -replace '\\', '/') ($Ref -replace '\\', '/') ($WorkRoot -replace '\\', '/') 2>&1
        if ($LASTEXITCODE -ne 0) {
            throw "stage-served-install-scripts.sh failed (exit $LASTEXITCODE): $output"
        }
    } finally {
        $ErrorActionPreference = $prevEap
    }
    $root = ("$output".Trim() -split "`r?`n" | Where-Object { $_ })[-1].Trim()
    $script = Join-Path $root "scripts\install.ps1"
    Assert-True (Test-Path -LiteralPath $script) "served install.ps1 staged from $Ref at $script"
    $env:HERMES_SETUP_DEV_REPO_ROOT = $root
    Write-Host "  HERMES_SETUP_DEV_REPO_ROOT=$root (install script from $Ref)"
}

'@

$readState = "function Read-State {"
if (-not $text.Contains($readState)) {
    throw "enable-served-install-script: could not find Read-State in $Driver"
}
$text = $text.Replace($readState, $function + $readState)

$remove = "    Remove-Item Env:HERMES_SETUP_DEV_REPO_ROOT -ErrorAction SilentlyContinue"
$call = @"
    # Script and tree have to be the same commit. Upstream main's install.ps1
    # requires pm/lock.json, which these served commits do not have.
    Set-ServedInstallScript `$ExpectedSha
"@
if (-not $text.Contains($remove)) {
    throw "enable-served-install-script: could not find the dev-root removal in $Driver"
}
$text = $text.Replace($remove, $call.TrimEnd())

Set-Content -LiteralPath $Driver -Value $text -NoNewline
Write-Host "pinned desktop installer script hook in $Driver"
