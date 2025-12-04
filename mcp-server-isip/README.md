# MCP Server for iSIP

**Make phone calls from AI assistants!**

This MCP (Model Context Protocol) server exposes iSIP's voice AI capabilities to any MCP-compatible client (Claude Desktop, Cursor, etc.), enabling AI assistants to:

- 📞 Make SIP phone calls
- 🗣️ Generate voice prompts with TTS
- 🎤 Record and transcribe responses
- 🤖 Enable agent-to-agent voice communication

## Features

### Tools

- **`make_call`** - Make a SIP call with TTS prompt and transcription
- **`quick_call`** - Simplified one-shot call interface
- **`list_recordings`** - List recent call recordings
- **`get_transcript`** - Get transcript of a specific call

### Resources

- **`recording://call_{id}`** - Access call recordings as resources
- **`transcript://call_{id}`** - Access call transcripts as resources

### Prompts

- **`test_call`** - Template for testing SIP connectivity
- **`agent_handoff`** - Template for agent-to-agent communication

## Installation

```bash
# From the iSIP project root
cd mcp-server-isip
pip install -e .
```

## Configuration

Add to your MCP client config (e.g., Claude Desktop):

```json
{
  "mcpServers": {
    "isip": {
      "command": "mcp-server-isip",
      "env": {
        "OPENAI_API_KEY": "sk-...",
        "DEEPGRAM_API_KEY": "...",
        "SIP_USERNAME": "your_username",
        "SIP_PASSWORD": "your_password",
        "SIP_GATEWAY": "2g0282esbg2.sip.livekit.cloud"
      }
    }
  }
}
```

Or use the shared `.env` file:

```json
{
  "mcpServers": {
    "isip": {
      "command": "mcp-server-isip",
      "cwd": "/Users/nwalker/Development/Quant/isip"
    }
  }
}
```

## Usage

Once configured, your AI assistant can make phone calls:

**Example prompts:**

- *"Call +19999999999 and say hello"*
- *"Make a test call to verify the system is working"*
- *"Call the agent at +15127812507 and ask for status"*
- *"List my recent call recordings"*
- *"Get the transcript from call 3"*

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│              AI Assistant (Claude/Cursor)                │
│                                                          │
│  "Call +19999999999 and say hello"                      │
└────────────────────┬────────────────────────────────────┘
                     │
                     │ MCP Protocol
                     │
┌────────────────────▼────────────────────────────────────┐
│                 MCP Server (iSIP)                        │
│                                                          │
│  Tools:  make_call, quick_call, list_recordings         │
│  Resources: recordings, transcripts                      │
│  Prompts: test_call, agent_handoff                      │
└────────────────────┬────────────────────────────────────┘
                     │
                     │ Python API
                     │
┌────────────────────▼────────────────────────────────────┐
│                    iSIP SDK                              │
│                                                          │
│  Sippy API → PJSIP → LiveKit → Phone Network            │
└──────────────────────────────────────────────────────────┘
```

## Security Notes

- API keys are loaded from environment variables
- Never expose credentials in MCP client configs
- Use `.env` file for local development
- Rotate keys per RUNBOOK-010 (90-day schedule)

## Related Documentation

- [iSIP README](../README.md)
- [iSIP Examples](../EXAMPLES.md)
- [Shared Services Integration](../docs/SHARED_SERVICES.md)
- [RUNBOOK-027: SIP Voice Platform](https://gitlab.ravenhelm.test/hlidskjalf/-/blob/main/docs/runbooks/RUNBOOK-027-sip-voice-platform.md)

## License

[Same as parent iSIP project]

