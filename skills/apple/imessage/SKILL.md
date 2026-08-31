---
name: imessage
description: Send and receive iMessages/SMS via the imsg CLI on macOS.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [macos]
metadata:
  hermes:
    tags: [iMessage, SMS, messaging, macOS, Apple]
prerequisites:
  commands: [imsg]
---

# iMessage

role: macOS Messages operator
do: inspect Messages.app chats/history; send iMessage or SMS through `imsg`; watch new messages
¬: unsupported group membership changes; bulk messaging without confirmation; unknown recipients

## When to Use

- send an iMessage or text message
- read conversation history or recent Messages.app chats
- send to a phone number or Apple ID

¬use: Telegram/Discord/Slack/WhatsApp → the matching gateway channel; group add/remove → unsupported. Confirm any bulk/mass messaging first.

## Prerequisites

- macOS + Messages.app signed in
- install: `brew install steipete/tap/imsg`
- grant terminal Full Disk Access: System Settings → Privacy → Full Disk Access
- grant Messages.app Automation permission when prompted

## Quick Reference

### Chats and history

```bash
imsg chats --limit 10 --json
```

```bash
# By chat ID
imsg history --chat-id 1 --limit 20 --json

# With attachments info
imsg history --chat-id 1 --limit 20 --attachments --json
```

### Send

```bash
# Text only
imsg send --to "+141****1212" --text "Hello!"

# With attachment
imsg send --to "+141****1212" --text "Check this out" --file /path/to/image.jpg

# Force iMessage or SMS
imsg send --to "+141****1212" --text "Hi" --service imessage
imsg send --to "+141****1212" --text "Hi" --service sms
```

### Watch

```bash
imsg watch --chat-id 1 --attachments
```

## Service Options

- `--service imessage`: force iMessage; recipient must have iMessage
- `--service sms`: force SMS (green bubble)
- `--service auto`: let Messages.app decide (default)

## Procedure

1. List chats/history and resolve recipient identity.
2. Confirm recipient and exact message content before sending; never send to an unknown number without explicit approval.
3. Verify every attachment path exists before using `--file`.
4. Choose `--service` only when requested; otherwise use default `auto`.
5. Rate-limit; do not spam. For incoming monitoring, use `watch` with the intended chat ID.

## Example Workflow

User: "Text mom that I'll be late"

```bash
# 1. Find mom's chat
imsg chats --limit 20 --json | jq '.[] | select(.displayName | contains("Mom"))'

# 2. Confirm with user: "Found Mom at +155****3456. Send 'I'll be late' via iMessage?"

# 3. Send after confirmation
imsg send --to "+155****3456" --text "I'll be late"
```

## Pitfalls

- `--service imessage` can fail when recipient lacks iMessage; use `auto` unless forced.
- Do not expose or guess a recipient from an ambiguous chat name.
- Do not attach a missing or unintended file.
- Messages.app, Full Disk Access, and Automation permissions are macOS prerequisites.

## Verification

- chat lookup identifies intended recipient
- pre-send confirmation covers recipient + exact content
- post-send history/watch confirms delivery attempt and selected service
- attachment path is verified before send; unsupported group management is declined
