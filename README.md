# isip — give your AI agent a phone ☎️

<div align="center">

**An MCP server (plus Python SDK and CLI) that lets an AI agent place and conduct real phone calls over SIP.**

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![PJSIP](https://img.shields.io/badge/PJSIP-2.16-green.svg)](https://www.pjsip.org/)
[![MCP](https://img.shields.io/badge/MCP-server-blueviolet.svg)](https://modelcontextprotocol.io/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

</div>

---

## What it does

Point Claude Desktop, Cursor, or any MCP client at `isip` and your agent can **dial a real phone number, speak (TTS), listen (STT), record the call, and report back a transcript** — no Twilio app to build, no SaaS platform, no Docker required. It's built on the native, battle-tested **PJSIP** stack.

Under the hood there are three ways to drive a call:

1. **MCP server** — expose calling as tools to any AI agent.
2. **Python SDK (`Sippy`)** — a clean high-level API: `sippy.call(target, prompt=…)` → transcript.
3. **CLI (`siptester`)** — single calls or JSON-defined test suites.

---

## Your agent, making a phone call

Once the MCP server is connected to Claude Desktop or Cursor, the model can place calls in plain language:

```
You:    "Call +1 512-555-0142, introduce yourself, and ask whether they're open today."
Claude: 📞 Calling… connected (24.1s).
        Transcript: "Hi! Yes, we're open until 6pm today. How can I help?"
```

MCP tools exposed to the agent:

| Tool | What it does |
|------|--------------|
| `place_call(phone, prompt)` | Dial a number, speak a prompt, transcribe the response |
| `list_recordings()` | Review prior call recordings + transcripts |

The agent drives the phone; `isip` handles SIP signaling, audio, TTS/STT, and recording.

---

## Why this exists

Giving an agent a phone unlocks two things:

1. **Testing voice AI** — script and regression-test SIP voice agents, trunks, gateways, and IVRs from code or from an agent itself.
2. **Agent-to-agent telephony** *(the bigger idea)* — an AI that handles the hour-long hold calls humans hate (e.g. insurance **verification of benefits**), and negotiates **AI-to-AI** when the other side is automated too — turning a one-hour hold into seconds.

---

## Quick start

### Prerequisites
- macOS (10.15+) · Python 3.12+ · Homebrew

### Install

```bash
# 1. System dependencies
brew install pjproject ffmpeg

# 2. Clone + set up the SDK
git clone https://github.com/nwalker85/isip.git
cd isip/sdk/python
python3.12 -m venv .venv && source .venv/bin/activate
pip install -e .

# 3. Configure credentials
cp ../../.env.example ../../.env   # then edit with your keys
```

`.env`:

```bash
# AI services
OPENAI_API_KEY=sk-...
DEEPGRAM_API_KEY=...
ELEVENLABS_API_KEY=...        # optional

# SIP gateway
SIP_USERNAME=your_username
SIP_PASSWORD=your_password
SIP_GATEWAY=<your-gateway>.sip.livekit.cloud
```

### Connect it to your agent (MCP)

```bash
cd mcp-server-isip
pip install -e .
```

Add to Claude Desktop (`~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "isip": {
      "command": "mcp-server-isip",
      "cwd": "/path/to/isip"
    }
  }
}
```

Then just ask Claude to place a call. See [`mcp-server-isip/QUICKSTART.md`](mcp-server-isip/QUICKSTART.md) for the full setup.

### Or call from Python

```python
from siptester import Sippy, VoiceService, SipHeaders

sippy = Sippy(
    voice_service=VoiceService("openai", "tts-1"),
    transcription_service=VoiceService("deepgram", "nova-2"),
)
target = SipHeaders(sip_to="sip:+15125550142@<your-gateway>.sip.livekit.cloud")
result = sippy.call(target, prompt="Hello, this is a test call.")

if result.established:
    print(result.duration, result.transcript)
```

One-liner:

```python
from siptester import quick_call
print(quick_call(phone="+15125550142", prompt="Hello, is anyone there?",
                 username="user", password="pass").transcript)
```

### Or from the CLI

```bash
source sdk/python/.venv/bin/activate

siptester call \
  --gateway "$SIP_GATEWAY" --user "$SIP_USERNAME" --password "$SIP_PASSWORD" \
  --phone +15125550142 --prompt-text "Hello, this is a test" \
  --openai-key "$OPENAI_API_KEY" --deepgram-key "$DEEPGRAM_API_KEY"

# Or a JSON test suite:
siptester suite --suite tests/example_tests.json \
  --gateway "$SIP_GATEWAY" --user "$SIP_USERNAME" --password "$SIP_PASSWORD"
```

---

## Architecture

```
  AI agent (Claude / Cursor)
        │  MCP
        ▼
  mcp-server-isip ──► Sippy (high-level API) ──► SipTestClient ──► PJSIP (native)
                              │                                        │
                       OpenAI TTS / Deepgram STT                 SIP gateway (e.g. LiveKit)
                                                                       │
                                                                  the phone network
```

- **MCP server** (`mcp-server-isip/`) — agent-facing tools.
- **Python SDK** (`sdk/python/siptester/`) — `Sippy` high-level API, low-level `SipTestClient`, and the `siptester` CLI.
- **PJSIP** — native SIP signaling.
- **AI services** — OpenAI TTS for prompts, Deepgram STT for transcription; ElevenLabs optional.

---

## Status

A working prototype, verified end-to-end (live calls against a LiveKit SIP gateway):

| Component | Status |
|-----------|--------|
| PJSIP bindings | ✅ working |
| Python SDK / `Sippy` | ✅ working |
| OpenAI TTS · Deepgram STT | ✅ working |
| Live SIP call (LiveKit gateway) | ✅ ~28s call, transcript received |
| Audio recording | ✅ working |
| MCP server | ✅ AI agent can place calls |
| CLI | ✅ working |

---

## Roadmap

- **SDK hardening** — packaging, unit tests with PJSIP mocking, type coverage.
- **CLI** — config file (`~/.isip/config.yaml`), JSON output, parallel runs with retries.
- **Agent telephony** — richer MCP tools (multi-turn conversations, DTMF/IVR navigation, call transfer), and the agent-to-agent VOB use case.
- **Cross-platform** — Linux validation, Docker image optimization.

---

## Troubleshooting

- **`pjsua`/PJSIP not found** → `brew install pjproject`
- **`ffmpeg` not found** → `brew install ffmpeg`
- **Microphone permissions** → System Settings → Privacy & Security → Microphone
- **NAT/firewall** → set `local_ip` to your public IP on `SipHeaders(...)`
- **SIP auth failed** → verify credentials with your SIP provider; email-style usernames are normalized automatically.

---

## Credits & license

Built with [PJSIP](https://www.pjsip.org/), [OpenAI](https://openai.com/) (TTS), [Deepgram](https://deepgram.com/) (STT), and tested against the [LiveKit](https://livekit.io/) SIP gateway.

MIT — see [LICENSE](LICENSE).

<div align="center">

**Give your agent a phone.**

</div>
