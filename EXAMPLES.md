# iSIP Usage Examples

## Table of Contents
- [Quick Start](#quick-start)
- [Sippy High-Level API](#sippy-high-level-api) ⭐ **Recommended**
- [CLI Examples](#cli-examples)
- [Low-Level Python API](#low-level-python-api)

## Quick Start

### One-Time Setup

Install dependencies and create virtual environment:

```bash
brew install pjproject ffmpeg
cd /Users/nwalker/Development/Quant/isip/sdk/python
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Sippy High-Level API

The Sippy API provides a clean, object-oriented interface for SIP testing with AI voice services.

### Basic Example

```python
from siptester import Sippy, VoiceService, SipHeaders

# Configure AI services
openai = VoiceService("openai", "tts-1", api_key=OPENAI_API_KEY)
deepgram = VoiceService("deepgram", "nova-2", api_key=DEEPGRAM_API_KEY)

# Create Sippy client
sippy = Sippy(voice_service=openai, transcription_service=deepgram)

# Configure target
target = SipHeaders(
    sip_to="sip:+19999999999@2g0282esbg2.sip.livekit.cloud",
    auth_user="your_username",
    auth_password="your_password",
)

# Make call
result = sippy.call(target, prompt="Hello, this is a test call")

if result.established:
    print(f"Call successful! Duration: {result.duration}s")
    print(f"Transcript: {result.transcript}")
```

### Quick Call

For simple one-off calls:

```python
from siptester import quick_call

result = quick_call(
    phone="+19999999999",
    prompt="Hello, is anyone there?",
    username="your_username",
    password="your_password",
)

print(result.transcript)
```

### Auto-loading from .env

VoiceService and SipHeaders automatically load credentials from environment variables:

```python
# These will use OPENAI_API_KEY, DEEPGRAM_API_KEY from environment
openai = VoiceService("openai", "tts-1")
deepgram = VoiceService("deepgram", "nova-2")

sippy = Sippy(voice_service=openai, transcription_service=deepgram)

# These will use SIP_USERNAME, SIP_PASSWORD, SIP_GATEWAY from environment
target = SipHeaders(sip_to="sip:+19999999999@2g0282esbg2.sip.livekit.cloud")

result = sippy.call(target, prompt="Fully automated test")
```

### Different Voice Models

```python
# OpenAI TTS with different voices
openai_alloy = VoiceService("openai", "tts-1", voice="alloy")
openai_nova = VoiceService("openai", "tts-1", voice="nova")
openai_shimmer = VoiceService("openai", "tts-1", voice="shimmer")

# ElevenLabs (when implemented)
# elevenlabs = VoiceService("elevenlabs", "eleven_turbo_v2")
```

### Complete Example Script

See `example_sippy.py` for comprehensive examples:

```bash
cd /Users/nwalker/Development/Quant/isip
source sdk/python/.venv/bin/activate
python example_sippy.py
```

---

## CLI Examples

### Minimal Connection Test

Test basic SIP connectivity without TTS or transcription:

```bash
source /Users/nwalker/Development/Quant/isip/sdk/python/.venv/bin/activate && \
siptester call \
  --gateway 2g0282esbg2.sip.livekit.cloud \
  --user YOUR_USERNAME \
  --password YOUR_PASSWORD \
  --phone +19999999999
```

### Call with TTS Prompt

Generate a voice prompt using OpenAI TTS and play it during the call:

```bash
source /Users/nwalker/Development/Quant/isip/sdk/python/.venv/bin/activate && \
siptester call \
  --gateway 2g0282esbg2.sip.livekit.cloud \
  --user YOUR_USERNAME \
  --password YOUR_PASSWORD \
  --phone +19999999999 \
  --prompt-text "Hello, this is a test call from iSIP" \
  --openai-key "$OPENAI_API_KEY"
```

### Full End-to-End Test

Complete call with TTS prompt generation and Deepgram transcription:

```bash
source /Users/nwalker/Development/Quant/isip/sdk/python/.venv/bin/activate && \
siptester call \
  --gateway 2g0282esbg2.sip.livekit.cloud \
  --user YOUR_USERNAME \
  --password YOUR_PASSWORD \
  --phone +19999999999 \
  --prompt-text "Hello, this is a test call. Please respond if you can hear this message." \
  --openai-key "$OPENAI_API_KEY" \
  --deepgram-key "$DEEPGRAM_API_KEY"
```

## Using Environment Variables (.env file)

Configure your credentials once in the `.env` file:

```bash
# Copy the example file
cp .env.example .env

# Edit .env with your actual credentials
# SIP_USERNAME=your_actual_username
# SIP_PASSWORD=your_actual_password
# OPENAI_API_KEY=sk-...
# DEEPGRAM_API_KEY=dg-...
```

Load the environment and run:

```bash
# Load environment variables
set -a && source .env && set +a

# Run simplified commands
source /Users/nwalker/Development/Quant/isip/sdk/python/.venv/bin/activate && \
siptester call \
  --gateway "$SIP_GATEWAY" \
  --user "$SIP_USERNAME" \
  --password "$SIP_PASSWORD" \
  --phone +19999999999 \
  --prompt-text "Hello, this is a test" \
  --openai-key "$OPENAI_API_KEY" \
  --deepgram-key "$DEEPGRAM_API_KEY"
```

## Test Suite Execution

Run multiple test scenarios from a JSON file:

```bash
source /Users/nwalker/Development/Quant/isip/sdk/python/.venv/bin/activate && \
siptester suite \
  --suite /path/to/tests/example_tests.json \
  --gateway 2g0282esbg2.sip.livekit.cloud \
  --user "$SIP_USERNAME" \
  --password "$SIP_PASSWORD"
```

## Automated Test Script

Use the provided bash script for automated testing. It automatically loads credentials from `.env`:

```bash
# First, configure your .env file with credentials
# Then simply run:
./test_sip_connection.sh
```

The script will automatically:
- Load credentials from `.env` file
- Activate the virtual environment
- Check for required SIP credentials
- Run the test with all configured API keys

## Low-Level Python API

For advanced use cases requiring fine-grained control, use the low-level client API.

### Basic Scenario

```python
from pathlib import Path
from siptester.client import SipTestClient, SipScenario

scenario = SipScenario(
    phone="+19999999999",
    prompt_file=Path("prompt.wav"),
    record_file=Path("response.wav"),
)

with SipTestClient(
    gateway="2g0282esbg2.sip.livekit.cloud",
    username="tester",
    password="secret",
    local_ip="67.198.117.118",
) as client:
    result = client.run_scenario(scenario)
    print(f"Call established: {result.established}")
    print(f"Duration: {result.duration}s")
```

### With TTS and Transcription

```python
from pathlib import Path
from siptester.client import SipTestClient, SipScenario, synthesize_prompt, transcribe_recording

# Generate prompt
prompt = Path("hello.wav")
synthesize_prompt(
    text="Hello, is anyone available?",
    output_path=prompt,
    openai_api_key="sk-...",
)

# Run scenario
scenario = SipScenario(
    phone="+19999999999",
    prompt_file=prompt,
    record_file=Path("response.wav"),
    timeout=30,
)

with SipTestClient(
    gateway="2g0282esbg2.sip.livekit.cloud",
    username="tester",
    password="secret",
    local_ip="67.198.117.118",
) as client:
    result = client.run_scenario(scenario)
    
    # Transcribe response
    if result.recording.exists():
        transcript = transcribe_recording(
            result.recording,
            deepgram_api_key="dg-...",
        )
        print(f"Response: {transcript}")
```

## Troubleshooting

### Common Issues

1. **PJSIP not found**: Install via `brew install pjproject`
2. **ffmpeg not found**: Install via `brew install ffmpeg`
3. **Microphone permissions**: Grant permissions in System Preferences → Security & Privacy → Microphone
4. **NAT/Firewall issues**: May need to configure local_ip parameter with your public IP
5. **SIP authentication failed**: Verify credentials with your SIP provider

### Debug Mode

Enable verbose logging to troubleshoot connection issues:

```bash
export PJSUA_LOG_LEVEL=5
siptester call --gateway ... [other options]
```

## Supported SIP Endpoints

- **LiveKit SIP Gateway**: `2g0282esbg2.sip.livekit.cloud`
- **Custom SIP Trunks**: Any SIP URI in format `gateway.domain.com`
- **Direct Phone Numbers**: Format as E.164 (e.g., `+19999999999`)

