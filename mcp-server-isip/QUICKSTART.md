# MCP Server iSIP - Quick Start Guide

## What You Just Built

**An MCP server that lets AI assistants make phone calls!** 🤯

Any MCP-compatible AI (Claude Desktop, Cursor, etc.) can now:
- Make SIP phone calls
- Talk to other AI agents over the phone
- Transcribe conversations
- Access call recordings

## Installation

```bash
cd /Users/nwalker/Development/Quant/isip/mcp-server-isip
pip install -e .
```

## Configure Claude Desktop

Edit `~/Library/Application Support/Claude/claude_desktop_config.json`:

**Recommended (uses project .env):**

```json
{
  "mcpServers": {
    "isip": {
      "command": "/Users/nwalker/Development/Quant/isip/sdk/python/.venv/bin/mcp-server-isip",
      "cwd": "/Users/nwalker/Development/Quant/isip"
    }
  }
}
```

**Alternative (explicit environment):**

```json
{
  "mcpServers": {
    "isip": {
      "command": "/Users/nwalker/Development/Quant/isip/sdk/python/.venv/bin/mcp-server-isip",
      "cwd": "/Users/nwalker/Development/Quant/isip",
      "env": {
        "OPENAI_API_KEY": "sk-proj-...",
        "DEEPGRAM_API_KEY": "...",
        "SIP_USERNAME": "nate@ravenhelm.co",
        "SIP_PASSWORD": "...",
        "SIP_GATEWAY": "2g0282esbg2.sip.livekit.cloud"
      }
    }
  }
}
```

**Note:** Use the **full path** to avoid `ENOENT` errors. See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) if you encounter issues.

## Configure Cursor

Add to `.cursorrules` or settings:

```json
{
  "mcp": {
    "servers": {
      "isip": {
        "command": ["mcp-server-isip"],
        "cwd": "/Users/nwalker/Development/Quant/isip"
      }
    }
  }
}
```

## Test It!

Restart Claude Desktop/Cursor, then try these prompts:

### Basic Test
```
Make a test call to +19999999999 and say "Hello from Claude!"
```

### Agent-to-Agent Communication
```
Call the agent at +19999999999 and ask them how they're doing
```

### Check Call History
```
List my recent call recordings
```

### Get a Transcript
```
Show me the transcript from call #1
```

## Available Tools

| Tool | Description |
|------|-------------|
| `make_call` | Full-featured call with custom TTS voice, timeout |
| `quick_call` | Simple one-shot call |
| `list_recordings` | List recent calls |
| `get_transcript` | Get transcript by call ID |

## Available Resources

- `transcript://call_{id}` - Access call transcripts
- `recording://call_{id}` - Access audio recordings

## Available Prompts

- `test_call` - Template for connectivity testing
- `agent_handoff` - Template for agent-to-agent handoffs

## Examples

### Claude Desktop Usage

**User:** "Make a call to +19999999999 and introduce yourself"

**Claude:** 
```
I'll make a call for you using the iSIP MCP server.

[Uses make_call tool]

✓ Call completed successfully!

Call ID: 1
Phone: +19999999999
Duration: 28.45 seconds

Transcript:
"Hello! I'm Claude, an AI assistant. I'm testing voice communication 
capabilities. Can you hear me clearly?"

Response:
"Yes, I can hear you perfectly. This is amazing - AI to AI voice 
communication working great!"
```

### Multi-Turn Conversation

**User:** "Call +19999999999, ask them for their status, then list all recordings"

**Claude:**
```
[Makes call, waits for response, lists recordings]

Call completed: Agent reported status "operational, ready for tasks"
Recent calls: 3 total, all successful
```

## Architecture

```
You: "Make a call to +19999999999"
  │
  ▼
Claude Desktop (MCP Client)
  │
  ▼
mcp-server-isip (This server)
  │
  ▼
iSIP Sippy API
  │
  ▼
PJSIP → LiveKit → Phone Network
  │
  ▼
Other AI Agent
  │
  ▼
[Conversation Happens]
  │
  ▼
Transcript returned to Claude
```

## Debugging

Check if server is running:
```bash
mcp-server-isip --help
```

Test manually:
```bash
cd /Users/nwalker/Development/Quant/isip
python -c "from mcp_server_isip.server import main; main()"
```

View logs:
```bash
# Claude Desktop logs
tail -f ~/Library/Logs/Claude/mcp*.log
```

## Security Notes

- API keys loaded from `.env` file
- Never commit credentials to git
- Rotate keys every 90 days (RUNBOOK-010)
- All calls logged in session history

## What's Next?

1. **Multi-Agent Orchestration**: Have Claude coordinate calls between multiple agents
2. **Voice Workflows**: Build complex voice-based automation
3. **Conference Calls**: Connect multiple agents on one call
4. **Persistent Agent Identities**: Give each agent their own phone number

## Related Documentation

- [iSIP README](../README.md)
- [MCP Server README](README.md)
- [iSIP Examples](../EXAMPLES.md)
- [MCP Protocol Specification](https://modelcontextprotocol.io/)

---

**You just enabled AI assistants to make phone calls. That's WILD.** 🚀

