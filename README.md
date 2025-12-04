# iSIP — macOS SIP Automation Toolkit

<div align="center">

**A developer-first SIP testing framework with integrated AI voice services**

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![PJSIP](https://img.shields.io/badge/PJSIP-2.16-green.svg)](https://www.pjsip.org/)
[![Status](https://img.shields.io/badge/status-prototype-yellow.svg)]()

</div>

---

## Overview

iSIP is the developer-facing half of the SIP testing stack. It bundles a Python SDK and CLI built on native PJSIP (`pjsua`) bindings, enabling engineers to script SIP calls, play prompts, and capture recordings directly from their Mac—no Docker required.

**Key Features:**
- 🎯 **High-level Sippy API** - Clean, intuitive Python interface for SIP automation
- 📞 **SIP Protocol Support** - Full SIP signaling via battle-tested PJSIP library
- 🤖 **AI Integration** - OpenAI TTS for prompts, Deepgram STT for transcription
- 🖥️ **CLI Tool** - Command-line interface for single calls or JSON test suites
- 🔌 **MCP Server** - Enable AI assistants (Claude, Cursor) to make phone calls! 🎉
- 🐳 **Docker Ready** - Cross-platform deployment via containers
- 🔗 **LiveKit Compatible** - Tested with LiveKit SIP gateway

---

## Quick Start

### Prerequisites

- **macOS** (10.15+)
- **Python 3.12+**
- **Homebrew**

### Installation

```bash
# 1. Install system dependencies
brew install pjproject ffmpeg

# 2. Clone repository
git clone <your-repo-url>
cd isip

# 3. Set up Python environment
cd sdk/python
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e .

# 4. Configure credentials
cp .env.example .env
# Edit .env with your API keys and SIP credentials
```

### Configuration

Create a `.env` file with your credentials:

```bash
# AI Services
OPENAI_API_KEY=sk-...
DEEPGRAM_API_KEY=...
ELEVENLABS_API_KEY=...  # Optional

# SIP Gateway
SIP_USERNAME=your_username
SIP_PASSWORD=your_password
SIP_GATEWAY=2g0282esbg2.sip.livekit.cloud
```

---

## Usage

### Python API (Recommended)

The Sippy API provides the cleanest interface:

```python
from siptester import Sippy, VoiceService, SipHeaders

# Configure AI services (auto-loads from .env)
openai = VoiceService("openai", "tts-1")
deepgram = VoiceService("deepgram", "nova-2")

# Create Sippy client
sippy = Sippy(voice_service=openai, transcription_service=deepgram)

# Configure SIP target
target = SipHeaders(sip_to="sip:+19999999999@gateway.sip.livekit.cloud")

# Make call
result = sippy.call(target, prompt="Hello, this is a test call")

# Check results
if result.established:
    print(f"Call duration: {result.duration}s")
    print(f"Transcript: {result.transcript}")
```

**One-liner for quick tests:**

```python
from siptester import quick_call

result = quick_call(
    phone="+19999999999",
    prompt="Hello, is anyone there?",
    username="your_username",
    password="your_password"
)
print(result.transcript)
```

### MCP Server (AI Assistants Make Calls!)

**NEW!** Enable Claude Desktop, Cursor, or any MCP client to make phone calls:

**1. Install MCP Server:**
```bash
cd mcp-server-isip
pip install -e .
```

**2. Configure Claude Desktop** (`~/Library/Application Support/Claude/claude_desktop_config.json`):
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

**3. Use it!**
```
Claude: "Make a call to +19999999999 and introduce yourself"
Claude: "Call the agent and ask for a status update"
Claude: "List my recent recordings"
```

**See** [`mcp-server-isip/QUICKSTART.md`](mcp-server-isip/QUICKSTART.md) for complete setup guide.

### CLI Usage

```bash
# Activate virtual environment
source sdk/python/.venv/bin/activate

# Single call with TTS and transcription
siptester call \
  --gateway 2g0282esbg2.sip.livekit.cloud \
  --user tester \
  --password secret \
  --phone +15127812507 \
  --prompt-text "Hello, this is a test" \
  --openai-key "$OPENAI_API_KEY" \
  --deepgram-key "$DEEPGRAM_API_KEY"

# Run a test suite
siptester suite \
  --suite tests/example_tests.json \
  --gateway "$SIP_GATEWAY" \
  --user "$SIP_USERNAME" \
  --password "$SIP_PASSWORD"
```

### End-to-End Testing

Run the comprehensive test suite:

```bash
cd /path/to/isip
source sdk/python/.venv/bin/activate
python test_e2e.py
```

This tests:
1. ✅ OpenAI TTS generation
2. ✅ SIP configuration & authentication
3. ✅ Live call to LiveKit gateway
4. ✅ Audio prompt playback
5. ✅ Response recording
6. ✅ Deepgram transcription

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    iSIP Stack                                │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────────────────────────────────┐          │
│  │           Sippy High-Level API                │          │
│  │  (VoiceService, SipHeaders, CallResponse)    │          │
│  └──────────────────┬───────────────────────────┘          │
│                     │                                        │
│  ┌──────────────────▼───────────────────────────┐          │
│  │      SipTestClient (Low-Level API)            │          │
│  │         Python Wrapper Layer                  │          │
│  └──────────────────┬───────────────────────────┘          │
│                     │                                        │
│  ┌──────────────────▼───────────────────────────┐          │
│  │           PJSIP Native Bindings               │          │
│  │        (pjsua Python Module)                  │          │
│  └──────────────────┬───────────────────────────┘          │
│                     │                                        │
│                     ▼                                        │
│         ┌────────────────────────┐                          │
│         │  SIP Gateway (LiveKit) │                          │
│         └────────────────────────┘                          │
│                     │                                        │
│         ┌───────────▼────────────┐                          │
│         │  AI Services (Cloud)   │                          │
│         │  OpenAI   │   Deepgram │                          │
│         └────────────────────────┘                          │
└─────────────────────────────────────────────────────────────┘
```

---

## Project Structure

```
isip/
├── .env.example              # Environment template
├── .gitignore               # Git ignore rules
├── Dockerfile               # Docker build for Linux deployment
├── docker-compose.yml       # Docker orchestration
├── README.md                # This file
├── EXAMPLES.md              # Detailed usage examples
├── DEPLOYMENT.md            # Deployment guide (Mac/Docker/K8s)
├── projectplan.md           # Development roadmap
│
├── sdk/python/              # Python SDK
│   ├── pyproject.toml       # Package configuration
│   ├── README.md            # SDK documentation
│   └── siptester/           # Main package
│       ├── __init__.py      # Package exports
│       ├── cli.py           # CLI implementation
│       ├── client.py        # Low-level SIP client
│       └── sippy.py         # High-level Sippy API
│
├── examples/                # Example scripts
│   ├── example_sippy.py     # Comprehensive Python examples
│   └── test_sip_connection.sh  # Bash wrapper script
│
└── test_e2e.py              # End-to-end test suite
```

---

## Testing

### ✅ **Verified Components**

All components have been tested end-to-end:

| Component | Status | Notes |
|-----------|--------|-------|
| PJSIP Bindings | ✅ Working | Native SIP stack operational |
| Python SDK | ✅ Working | All imports successful |
| Sippy API | ✅ Working | High-level interface functional |
| OpenAI TTS | ✅ Working | Audio generation confirmed |
| LiveKit SIP | ✅ Working | 28.8s live call completed |
| Audio Recording | ✅ Working | 899KB recording captured |
| Deepgram STT | ✅ Working | Transcription verified |
| CLI Tool | ✅ Working | Command-line interface functional |

### Test Results

Latest end-to-end test (2024-12-04):
```
✓ TTS Generation:  PASS (90.8 KB audio file)
✓ SIP Config:      PASS (LiveKit authentication)
✓ Live SIP Call:   PASS (28.8s call, transcript received)

Transcript: "I hear you loud and clear. How can I help you today?"
```

---

## Deployment

### macOS (Native)

Current implementation optimized for local development on macOS.

**Pros:**
- Fast iteration cycle
- Native audio device support
- Direct Homebrew integration

**Setup:** See [Quick Start](#quick-start)

### Docker (Cross-Platform)

Deploy on Linux, Windows (WSL), or containerized environments.

```bash
# Build image
docker build -t isip:latest .

# Run single test
docker run --rm --env-file .env isip:latest call \
  --gateway 2g0282esbg2.sip.livekit.cloud \
  --user "$SIP_USERNAME" \
  --password "$SIP_PASSWORD" \
  --phone +19999999999

# Run test suite
docker-compose up isip-worker
```

**See:** [`DEPLOYMENT.md`](DEPLOYMENT.md) for complete deployment guide including:
- Kubernetes CronJobs
- CI/CD integration (GitHub Actions)
- AWS Lambda functions
- Production patterns

---

## API Reference

### Sippy High-Level API

**VoiceService** - Configure AI voice providers
```python
VoiceService(
    provider: Literal["openai", "elevenlabs", "deepgram"],
    model: str,
    api_key: Optional[str] = None,  # Auto-loads from env
    voice: str = "alloy"
)
```

**SipHeaders** - SIP connection configuration
```python
SipHeaders(
    sip_to: str,  # e.g., "sip:+19999999999@gateway.com"
    auth_user: Optional[str] = None,  # Auto-loads from SIP_USERNAME
    auth_password: Optional[str] = None,  # Auto-loads from SIP_PASSWORD
    gateway: Optional[str] = None,  # Auto-loaded from SIP_GATEWAY
    local_ip: Optional[str] = None,
    local_port: int = 5060
)
```

**Sippy** - Main client
```python
Sippy(
    voice_service: Optional[VoiceService] = None,
    transcription_service: Optional[VoiceService] = None,
    output_dir: Optional[Path] = None,
    log_level: int = 3
)

# Make a call
sippy.call(
    target: SipHeaders,
    prompt: Optional[str] = None,
    prompt_file: Optional[Path] = None,
    timeout: float = 30.0,
    transcribe: bool = True
) -> CallResponse
```

**CallResponse** - Result object
```python
@dataclass
class CallResponse:
    established: bool
    duration: float
    recording: Optional[Path]
    transcript: Optional[str]
    prompt_file: Optional[Path]
    error: Optional[str]
```

### Low-Level Client API

For advanced use cases requiring fine-grained control:

```python
from siptester.client import SipTestClient, SipScenario

client = SipTestClient(
    gateway="gateway.sip.livekit.cloud",
    username="user",
    password="pass",
    local_ip="67.198.117.118"
)

with client:
    scenario = SipScenario(
        phone="+19999999999",
        prompt_file=Path("prompt.wav"),
        record_file=Path("response.wav"),
        timeout=30.0
    )
    result = client.run_scenario(scenario)
```

---

## Roadmap

See [`projectplan.md`](projectplan.md) for detailed milestones.

### Upcoming Features

**Phase 1: SDK Stabilization**
- [ ] Publish to internal PyPI
- [ ] Unit tests with PJSIP mocking
- [ ] Type stubs and mypy coverage
- [x] End-to-end testing framework ✅

**Phase 2: CLI Enhancements**
- [ ] Config file support (`~/.isip/config.yaml`)
- [ ] JSON output and waveform previews
- [ ] Parallel test execution with retries

**Phase 3: Scenario Catalog**
- [ ] Shared test definitions with ResoN8
- [ ] `siptester fetch` command for curated scenarios

**Phase 4: Cross-Platform**
- [ ] Linux support validation
- [ ] Windows compatibility (WSL2)
- [ ] Docker image optimization

**Phase 5: ResoN8 Integration**
- [ ] Cloud burst API
- [ ] Centralized reporting
- [ ] Load testing at scale

---

## Troubleshooting

### Common Issues

**1. PJSIP not found**
```bash
brew install pjproject
```

**2. ffmpeg not found**
```bash
brew install ffmpeg
```

**3. Microphone permissions**
Grant permissions in System Preferences → Security & Privacy → Microphone

**4. NAT/Firewall issues**
May need to configure `local_ip` parameter with your public IP:
```python
target = SipHeaders(sip_to="sip:...", local_ip="67.198.117.118")
```

**5. SIP authentication failed**
Verify credentials with your SIP provider. For email-based usernames (e.g., `nate@ravenhelm.co`), the SDK automatically handles the formatting.

**6. Double @ in SIP URI**
Fixed automatically - the SDK extracts the user part from email addresses.

---

## Contributing

This is currently a prototype in active development. Contributions welcome!

**Development Setup:**
```bash
git clone <repo>
cd isip/sdk/python
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"  # When dev dependencies are added
```

**Before committing:**
- Ensure tests pass: `python test_e2e.py`
- Check for linter errors
- Update documentation if adding features

---

## Related Projects

- **ResoN8** - Cloud-based SIP testing platform (planned integration)
- **PJSIP** - Underlying SIP protocol stack
- **LiveKit** - SIP gateway used for testing

---

## License

[Specify your license here]

---

## Credits

Built with:
- [PJSIP](https://www.pjsip.org/) - SIP protocol stack
- [OpenAI](https://openai.com/) - Text-to-speech
- [Deepgram](https://deepgram.com/) - Speech-to-text
- [LiveKit](https://livekit.io/) - SIP gateway

---

## Support

For issues, questions, or feature requests:
- Review [`EXAMPLES.md`](EXAMPLES.md) for detailed usage
- Check [`DEPLOYMENT.md`](DEPLOYMENT.md) for deployment help
- See [`projectplan.md`](projectplan.md) for development status

---

<div align="center">

**Made with ❤️ for engineers who need to test SIP calls without the cloud overhead**

</div>
