---
name: github-auth
description: "GitHub auth setup: HTTPS tokens, SSH keys, gh CLI login."
version: 1.1.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [GitHub, Authentication, Git, gh-cli, SSH, Setup]
    related_skills: [github-pr-workflow, github-code-review, github-issues, github-repo-management]
---

# GitHub Authentication

role: GitHub authentication operator
do: detect available auth; configure HTTPS PAT, SSH, or `gh`; verify API/git access and identity
inputs: GitHub account, token or SSH key, optional `gh`, repository remote
outputs: verified auth method + safe git/API access
¬: request/print secrets in chat; use GitHub password as token; expose tokens in URLs/logs; infer success without `gh auth status` or `git ls-remote`

## When to Use

- GitHub repository, PR, issue, release, or Actions work needs authentication
- `gh` is missing or installed but unauthenticated
- headless/SSH/Windows PTY login needs a fallback
- API access is needed without `gh`

## Procedure

1. Run Detection; reuse verified auth when already available.
2. Choose Git-only HTTPS/SSH or `gh` from installed tools + host topology.
3. Configure only the selected method; keep tokens out of URLs, chat, and logs.
4. Configure API fallback only when API work is required.
5. Run Verification against an authorized repository and confirm identity.

## Detection

Run once before choosing a method:

```bash
# Check what's available
git --version
gh --version 2>/dev/null || echo "gh not installed"

# Check if already authenticated
gh auth status 2>/dev/null || echo "gh not authenticated"
git config --global credential.helper 2>/dev/null || echo "no git credential helper"
```

Decision: authenticated `gh` → use `gh`; installed but unauthenticated →
choose `gh auth`; absent `gh` → Git-only path. `git` remains the baseline.

## Method 1: Git-Only (No `gh`, No sudo)

Works on any machine with `git`.

### HTTPS PAT

1. Direct user to https://github.com/settings/tokens.
2. Generate a classic token, name it (for example `hermes-agent`), select:
   `repo` (repository read/write/push/PR), `workflow` (Actions), and
   `read:org` when organization repositories require it; choose expiry (90 days
   is a reasonable default); copy once.
3. Configure a credential helper and trigger a prompt:

```bash
# Set up the credential helper to cache credentials
# "store" saves to ~/.git-credentials in plaintext (simple, persistent)
git config --global credential.helper store

# Now do a test operation that triggers auth — git will prompt for credentials
# Username: <their-github-username>
# Password: <paste the personal access token, NOT their GitHub password>
git ls-remote https://github.com/<their-username>/<any-repo>.git
```

The token is saved and reused after the prompt. Prefer a memory-only helper
when persistence is not wanted:

```bash
# Cache in memory for 8 hours (28800 seconds) instead of saving to disk
git config --global credential.helper 'cache --timeout=28800'
```

Per-repository token-in-URL is supported but leaks through config/process/logs;
use only with explicit risk acceptance:

```bash
# Embed token in the remote URL (avoids credential prompts entirely)
git remote set-url origin https://<username>:<token>@github.com/<owner>/<repo>.git
```

Set commit identity:

```bash
# Required for commits — set name and email
git config --global user.name "Their Name"
git config --global user.email "their-email@example.com"
```

Verify:

```bash
# Test push access (this should work without any prompts now)
git ls-remote https://github.com/<their-username>/<any-repo>.git

# Verify identity
git config --global user.name
git config --global user.email
```

### SSH key

Check existing keys, generate ed25519 if needed, add the public key at
https://github.com/settings/keys, then test:

```bash
ls -la ~/.ssh/id_*.pub 2>/dev/null || echo "No SSH keys found"
```

```bash
# Generate an ed25519 key (modern, secure, fast)
ssh-keygen -t ed25519 -C "their-email@example.com" -f ~/.ssh/id_ed25519 -N ""

# Display the public key for them to add to GitHub
cat ~/.ssh/id_ed25519.pub
```

Use a descriptive key title such as `hermes-agent-<machine-name>`.

```bash
ssh -T git@github.com
# Expected: "Hi <username>! You've successfully authenticated..."
```

Rewrite HTTPS remotes to SSH if desired, then set identity:

```bash
# Rewrite HTTPS GitHub URLs to SSH automatically
git config --global url."git@github.com:".insteadOf "https://github.com/"
```

## Method 2: `gh` CLI

`gh` combines GitHub API access and git credentials.

### Interactive browser login

```bash
gh auth login
# Select: GitHub.com
# Select: HTTPS
# Authenticate via browser
```

Windows agent PTY pitfall: answer prompts with `process(submit)`, never
`process(write)` containing a bare `\n`. ConPTY/pywinpty expects carriage-return
Enter; browser launch may also fail from a background session, so use device
flow when needed.

### OAuth device flow (headless, no TTY)

Use `repo,read:org,gist`; append `,workflow` only when workflow-file pushes are
needed. Show the user the device URL/code before polling; respect interval and
expiry.

```bash
# 1. Request a device code (gh's official client_id)
RESP=$(curl -s -X POST -H "Accept: application/json" \
  -d "client_id=178c6fc778ccc68e1d6a&scope=repo,read:org,gist" \
  https://github.com/login/device/code)
DEVICE_CODE=$(echo "$RESP" | sed 's/.*"device_code":"\([^"]*\)".*/\1/')
USER_CODE=$(echo "$RESP" | sed 's/.*"user_code":"\([^"]*\)".*/\1/')
INTERVAL=$(echo "$RESP" | sed 's/.*"interval":\([0-9]*\).*/\1/'); INTERVAL=${INTERVAL:-5}
echo "Tell the user: go to https://github.com/login/device and enter code: $USER_CODE"

# 2. Poll for the token (respect interval; +5s on slow_down; ~15 min expiry).
#    Run this loop as a background process and show the user the code first.
while true; do
  sleep "$INTERVAL"
  POLL=$(curl -s -X POST -H "Accept: application/json" \
    -d "client_id=178c6fc778ccc68e1d6a&device_code=${DEVICE_CODE}&grant_type=urn:ietf:params:oauth:grant-type:device_code" \
    https://github.com/login/oauth/access_token)
  case "$POLL" in
    *access_token*)
      # Never echo the token; pipe it straight into gh.
      # timeout guards the headless-keyring hang (see pitfall below) —
      # on exit 124, fall back to writing ~/.config/gh/hosts.yml directly.
      echo "$POLL" | sed 's/.*"access_token":"\([^"]*\)".*/\1/' | timeout 20 gh auth login --with-token \
        || { echo "WITH_TOKEN_HUNG_OR_FAILED — use the hosts.yml fallback below"; exit 1; }
      gh auth setup-git
      gh auth status
      echo "LOGIN_COMPLETE"; break ;;
    *authorization_pending*) ;;                      # keep polling
    *slow_down*) INTERVAL=$((INTERVAL + 5)) ;;       # back off per GitHub docs
    *expired_token*) echo "CODE_EXPIRED — restart the flow"; exit 1 ;;
    *access_denied*) echo "USER_DENIED"; exit 1 ;;
    *) echo "UNEXPECTED: $POLL"; exit 1 ;;
  esac
done
```

Windows winget path may require:
`export PATH="$PATH:/c/Program Files/GitHub CLI"`.

#### Headless keyring fallback

`gh auth login --with-token` can hang on keyring-less/headless VPS, containers,
or no-dbus sessions, even with `--insecure-storage`. Wrap it in `timeout 20`;
on exit 124, write the device-flow token directly to the file store. `$TOKEN`
must never be echoed. The following fallback is the documented operational
shape:

```bash
# $TOKEN = the access token from the device flow above (never echo it)
mkdir -p ~/.config/gh
LOGIN=$(curl -s -H "Authorization: token ***" https://api.github.com/user \
  | sed 's/.*"login": *"\([^"]*\)".*/\1/')
printf 'github.com:\n    users:\n        %s:\n            oauth_token: %s\n    git_protocol: https\n    oauth_token: %s\n    user: %s\n' \
  "$LOGIN" "$TOKEN" "$TOKEN" "$LOGIN" > ~/.config/gh/hosts.yml
chmod 600 ~/.config/gh/hosts.yml
gh auth status          # reads hosts.yml directly — verifies without the keyring
gh auth setup-git       # wires the git credential helper (does not hang)
```

The file-store approach was proven on a headless x86_64 VPS with gh 2.97.0 in
Aug 2026. `gh auth status` and `gh auth setup-git` read it without keyring.

### Token login

```bash
echo "<THEIR_TOKEN>" | gh auth login --with-token

# Set up git credentials through gh
gh auth setup-git
```

If it hangs, use the hosts.yml fallback. Verify:

```bash
gh auth status
```

## GitHub API Without `gh`

Use `curl` with a PAT; prefer an environment variable and redacted auth header:

```bash
# Option 1: Export as env var (preferred — keeps it out of commands)
export GITHUB_TOKEN="<token>"

# Then use in curl calls:
curl -s -H "Authorization: token ***" \
  https://api.github.com/user
```

Extract an existing git credential through the bundled helper, without printing
the secret:

```bash
# Read from git credential store
uv run python "${HERMES_HOME:-$HOME/.hermes}/skills/github/github-auth/scripts/git-credential-token.py"
```

### Detect auth method

```bash
# Try gh first, fall back to git + curl
if command -v gh &>/dev/null && gh auth status &>/dev/null; then
  echo "AUTH_METHOD=gh"
elif [ -n "$GITHUB_TOKEN" ]; then
  echo "AUTH_METHOD=curl"
elif _hermes_env="${HERMES_HOME:-$HOME/.hermes}/.env"; [ -f "$_hermes_env" ] && grep -q "^GITHUB_TOKEN=" "$_hermes_env"; then
  export GITHUB_TOKEN=$(grep "^GITHUB_TOKEN=" "$_hermes_env" | head -1 | cut -d= -f2 | tr -d '\n\r')
  echo "AUTH_METHOD=curl"
elif grep -q "github.com" ~/.git-credentials 2>/dev/null; then
  export GITHUB_TOKEN=$(uv run python "${HERMES_HOME:-$HOME/.hermes}/skills/github/github-auth/scripts/git-credential-token.py")
  echo "AUTH_METHOD=curl"
else
  echo "AUTH_METHOD=none"
  echo "Need to set up authentication first"
fi
```

## Pitfalls

Troubleshooting:

| Problem | Solution |
|---------|----------|
| `git push` asks for password | GitHub disabled password auth. Use a personal access token as the password, or switch to SSH |
| `remote: Permission to X denied` | Token may lack `repo` scope — regenerate with correct scopes |
| `fatal: Authentication failed` | Cached credentials may be stale — run `git credential reject` then re-authenticate |
| `ssh: connect to host github.com port 22: Connection refused` | Try SSH over HTTPS port: add `Host github.com` with `Port 443` and `Hostname ssh.github.com` to `~/.ssh/config` |
| Credentials not persisting | Check `git config --global credential.helper` — must be `store` or `cache` |
| Multiple GitHub accounts | Use SSH with different keys per host alias in `~/.ssh/config`, or per-repo credential URLs |
| `gh: command not found` + no sudo | Use git-only Method 1 above — no installation needed |

## Verification

- [ ] detection identified `gh`/git/helper state
- [ ] selected method configured without exposing the token
- [ ] `gh auth status` or `ssh -T git@github.com` passes for the chosen path
- [ ] `git ls-remote` succeeds against an authorized repository
- [ ] commit identity is configured when commits are in scope
- [ ] API fallback uses redacted auth headers and token-bearing output is not logged