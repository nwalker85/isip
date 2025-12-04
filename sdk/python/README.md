# SIP Tester Python SDK (Prototype)

Mac developers can run SIP play/record flows without Docker by using the Python wrapper around the [PJSIP](https://www.pjsip.org/) stack.

## Prerequisites

1. Install pjproject (provides the `pjsua` Python module):
   ```bash
   brew install pjproject
   ```
2. Create a virtual environment and install the SDK:
   ```bash
   cd sdk/python
   python -m venv .venv
   source .venv/bin/activate
   pip install -e .
   ```

## CLI

After installing, use the bundled CLI:

```bash
source .venv/bin/activate
siptester call \
  --gateway 2g0282esbg2.sip.livekit.cloud \
  --user tester \
  --password secret \
  --phone +15127812507 \
  --prompt-text "Hello, this is a test call" \
  --openai-key sk-... \
  --deepgram-key dg-...
```

Or run an entire JSON suite:

```bash
siptester suite --suite ../../tests/example_tests.json --gateway ... --user ...
```

## Usage

```python
from pathlib import Path
from siptester.client import SipTestClient, SipScenario, synthesize_prompt, transcribe_recording

prompt = Path("hello.wav")
synthesize_prompt(
    text="Hello, is anyone available?",
    output_path=prompt,
    openai_api_key="sk-...",
)

scenario = SipScenario(
    phone="+15127812507",
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
    print(result.established, result.duration)
    print(
        transcribe_recording(
            result.recording,
            deepgram_api_key="dg-...",
        )
    )
```

See [`siptester/client.py`](siptester/client.py) for additional options (custom media ports, logging, etc.).

