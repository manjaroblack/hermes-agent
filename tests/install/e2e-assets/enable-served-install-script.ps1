# Insert the served-commit install-script pin into windows-e2e.ps1.
# The published Hermes-Setup.exe downloads NousResearch/hermes-agent main's
# install.ps1, which requires pm/lock.json. The commits this fork serves do
# not have that file. The pin points HERMES_SETUP_DEV_REPO_ROOT at the script
# from the commit serve.git is cloning.
param(
    [string]$Driver = ""
)

$ErrorActionPreference = "Stop"
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
