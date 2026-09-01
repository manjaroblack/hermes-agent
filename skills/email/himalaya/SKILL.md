---
name: himalaya
description: "Himalaya CLI: IMAP/SMTP email from terminal."
version: 1.1.0
author: community
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Email, IMAP, SMTP, CLI, Communication]
    homepage: https://github.com/pimalaya/himalaya
prerequisites:
  commands: [himalaya]
---

# Himalaya Email CLI

role: terminal mailbox operator
do: configure accounts; list/search/read/move/copy/delete/flag mail; compose/reply/forward; download attachments
inputs: Himalaya CLI, `~/.config/himalaya/config.toml`, secure IMAP/SMTP credentials
outputs: structured mailbox data, sent/drafted mail, folders, attachments
¬: store plaintext credentials; retry an ambiguous send; use deprecated folder-alias syntax; confuse this skill with Hermes' Email gateway adapter

Himalaya supports IMAP, SMTP, Notmuch, and Sendmail backends. This skill lets
the agent operate a mailbox through terminal tools; the Hermes Email gateway
adapter is a separate surface.

## When to Use

- list, search, read, move, copy, flag, delete, or export email
- compose, reply, forward, or download attachments
- configure Himalaya accounts or diagnose IMAP/SMTP behavior
- operate multiple accounts with JSON output

## Procedure

1. Verify install + config; select account and resolve folder aliases.
2. List/search before acting; re-list whenever folder context changes.
3. Run the matching operation below with JSON output when structure matters.
4. For outbound mail, inspect headers/thread linkage before send; after any
   ambiguous non-zero exit, inspect Sent before retrying.
5. Verify resulting folder/message/attachment state.

## References

- `references/configuration.md`: config + IMAP/SMTP authentication
- `references/message-composition.md`: MML composition syntax

## Prerequisites + Installation

1. Himalaya installed; verify `himalaya --version`.
2. `~/.config/himalaya/config.toml` exists.
3. IMAP/SMTP credentials configured through a secure password command/keyring.

```bash
# Pre-built binary (Linux/macOS — recommended)
curl -sSL https://raw.githubusercontent.com/pimalaya/himalaya/master/install.sh | PREFIX=~/.local sh

# macOS via Homebrew
brew install himalaya

# Or via cargo (any platform with Rust)
cargo install himalaya --locked
```

## Configuration

Interactive setup:

```bash
himalaya account configure
```

Manual `~/.config/himalaya/config.toml`:

```toml
[accounts.personal]
email = "you@example.com"
display-name = "Your Name"
default = true

backend.type = "imap"
backend.host = "imap.example.com"
backend.port = 993
backend.encryption.type = "tls"
backend.login = "you@example.com"
backend.auth.type = "password"
backend.auth.cmd = "pass show email/imap"  # or use keyring

message.send.backend.type = "smtp"
message.send.backend.host = "smtp.example.com"
message.send.backend.port = 587
message.send.backend.encryption.type = "start-tls"
message.send.backend.login = "you@example.com"
message.send.backend.auth.type = "password"
message.send.backend.auth.cmd = "pass show email/smtp"

# Folder aliases (himalaya v1.2.0+ syntax). Required whenever the
# server's folder names don't match himalaya's canonical names
# (inbox/sent/drafts/trash). Gmail is the common case — see
# `references/configuration.md` for the `[Gmail]/Sent Mail` mapping.
folder.aliases.inbox = "INBOX"
folder.aliases.sent = "Sent"
folder.aliases.drafts = "Drafts"
folder.aliases.trash = "Trash"
```

Use plural dotted `folder.aliases.X` directly under `[accounts.NAME]`. The
deprecated `[accounts.NAME.folder.alias]` form parses but v1.2.0 ignores it;
lookups fall through to canonical names. On Gmail, save-to-Sent can fail after
SMTP delivery, and retrying the non-zero exit sends duplicates.

## Hermes Integration

- reading/listing/searching/moving/deleting: terminal commands
- composing/replying/forwarding: pipe input; interactive `$EDITOR` needs
  `pty=true` + background `terminal` + `process`, with editor commands known
- use `--output json` for machine-readable output
- `himalaya account configure` needs PTY:
  `terminal(command="himalaya account configure", pty=true)`

## Operations

### Folders + envelopes

```bash
himalaya folder list
himalaya envelope list
himalaya envelope list --folder "Sent"
himalaya envelope list --page 1 --page-size 20
himalaya envelope list from john@example.com subject meeting
```

### Read/export

```bash
himalaya message read 42
himalaya message export 42 --full
```

### Reply

Read the original, edit the template, and pipe it:

```bash
# Get the reply template, edit it, and send
himalaya template reply 42 | sed 's/^$/\nYour reply text here\n/' | himalaya template send
```

Manual non-interactive message:

```bash
cat << 'EOF' | himalaya template send
From: you@example.com
To: sender@example.com
Subject: Re: Original Subject
In-Reply-To: <original-message-id>

Your reply here.
EOF
```

Reply-all is interactive; prefer the template path:

```bash
himalaya message reply 42 --all
```

### Forward + compose

```bash
# Get forward template and pipe with modifications
himalaya template forward 42 | sed 's/^To:.*/To: newrecipient@example.com/' | himalaya template send
```

```bash
cat << 'EOF' | himalaya template send
From: you@example.com
To: recipient@example.com
Subject: Test Message

Hello from Himalaya!
EOF
```

```bash
himalaya message write -H "To:recipient@example.com" -H "Subject:Test" "Message body here"
```

Without piped input, `himalaya message write` opens `$EDITOR`; use PTY,
background mode, and `process` if interactive editing is necessary. For rich
mail/attachments, load `references/message-composition.md` and use MML.

### Move/copy/delete + flags

Target folder precedes message ID:

```bash
himalaya message move "Archive" 42
himalaya message copy "Important" 42
himalaya message delete 42
himalaya flag add 42 --flag seen
himalaya flag remove 42 --flag seen
```

### Accounts

```bash
himalaya account list
himalaya --account work envelope list
```

### Attachments

```bash
himalaya attachment download 42
himalaya attachment download 42 --downloads-dir ~/Downloads
```

### Output + debugging

```bash
himalaya envelope list --output json
himalaya envelope list --output plain
RUST_LOG=debug himalaya envelope list
RUST_LOG=trace RUST_BACKTRACE=1 himalaya envelope list
```

## Pitfalls

- Message IDs are relative to the current folder; re-list after folder changes.
- `folder.aliases.X` is required in v1.2.0+; singular legacy syntax silently
  fails to map Gmail folders.
- SMTP success plus a non-zero `himalaya message send` from save-to-Sent
  failure is an ambiguous send; inspect Sent before retrying.
- Store passwords with `pass`, system keyring, or another secure command.
- For exact flags, use `himalaya --help` or `himalaya <command> --help`.

## Verification

- [ ] `himalaya --version` succeeds and config path exists.
- [ ] account/folder listing succeeds with expected account selected.
- [ ] folder aliases map server names to `inbox/sent/drafts/trash`.
- [ ] read/search uses `--output json` when structured data is needed.
- [ ] composed output has correct headers/thread linkage before send.
- [ ] ambiguous send checks Sent before any retry.
- [ ] downloaded attachments exist at the stated directory.