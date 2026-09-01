---
name: agentmail
description: "Give the agent its own inbox: send and receive email."
version: 1.0.0
author: teyrebaz33, Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [email, communication, agentmail, mcp]
    category: email
---

# AgentMail — Agent-Owned Email Inboxes

role: AgentMail inbox operator
do: obtain key; configure MCP; restart Hermes; create/list/read/send/reply/forward/update/download; poll threads; verify address/message
inputs: AgentMail API key, username, inbox/thread/message IDs, recipients, subject/body, attachment
outputs: dedicated `@agentmail.to` inbox, sent/replied email, thread state, downloaded attachment
¬: use for user's personal mailbox; put key in git/logs; claim webhooks without public server; exceed free-tier limits silently; authenticate user or disclose verification codes without authorization

Give Hermes its own email identity and inbox through the AgentMail MCP server. This is not a personal Gmail/Himalaya reader; use those skills for the user's mailbox.

## When to Use

- dedicated agent email address
- autonomous send/receive/reply
- service signup or email verification
- agent-to-human/agent communication
- thread/attachment management

## Prerequisites

- AgentMail API key from https://console.agentmail.to (`am_...`); free tier: 3 inboxes/3,000 emails/month; paid from $20/mo
- Node.js 18+ for `npx -y agentmail-mcp`
- Python `mcp` package: `pip install mcp`

## Procedure

### 1. Configure MCP

1. Create account/key at https://console.agentmail.to.
2. Add actual key to `~/.hermes/config.yaml`; MCP env vars are not expanded from `.env`:

```yaml
mcp_servers:
  agentmail:
    command: "npx"
    args: ["-y", "agentmail-mcp"]
    env:
      AGENTMAIL_API_KEY: "am_your_key_here"
```

3. Restart Hermes:

```bash
hermes
```

All 11 AgentMail tools become available through MCP.

### 2. Create, send, check

```text
create_inbox(username="hermes-agent")
→ hermes-agent@agentmail.to
send_message(inbox_id, to, subject, text)
list_threads(inbox_id)
get_thread(thread_id)
```

### 3. Reply/forward/update/attachment

- `reply_to_message(message_id, text)` for an existing thread
- `forward_message(...)` for authorized forwarding
- `update_message(...)` for labels/status
- `get_attachment(...)` to download a requested attachment

## Tool Catalog

| Tool | Description |
|------|-------------|
| `list_inboxes` | List all agent inboxes |
| `get_inbox` | Get details of a specific inbox |
| `create_inbox` | Create a new inbox (gets a real email address) |
| `delete_inbox` | Delete an inbox |
| `list_threads` | List email threads in an inbox |
| `get_thread` | Get a specific email thread |
| `send_message` | Send a new email |
| `reply_to_message` | Reply to an existing email |
| `forward_message` | Forward an email |
| `update_message` | Update message labels/status |
| `get_attachment` | Download an email attachment |

## Workflows

### Service signup

```
1. create_inbox (username: "signup-bot")
2. Use the inbox address to register on the service
3. list_threads to check for verification email
4. get_thread to read the verification code
```

Use verification codes only within the authorized signup task.

### Outreach

```
1. create_inbox (username: "hermes-outreach")
2. send_message (to: user@example.com, subject: "Hello", text: "...")
3. list_threads to check for replies
```

Review recipients/content before sending; reply only after review/authorization.

For inbound real-time webhooks, a public server is required; personal use should poll `list_threads` from a cron job.

## Pitfalls

- free tier limits 3 inboxes/3,000 emails/month; free mail uses `@agentmail.to`; custom domains need paid plan
- Node 18+ and Python `mcp` are both required
- MCP config does not expand AgentMail vars from `.env`; use secret-safe config handling
- email verification codes are sensitive; do not disclose or use beyond authorized task

## Verification

```
hermes --toolsets mcp -q "Create an AgentMail inbox called test-agent and tell me its email address"
```

Expected: new inbox address returned; then send a test only to an authorized recipient and confirm it appears in `list_threads`/`get_thread`.

## References

- docs: https://docs.agentmail.to/
- console: https://console.agentmail.to
- MCP repo: https://github.com/agentmail-to/agentmail-mcp
- pricing: https://www.agentmail.to/pricing
