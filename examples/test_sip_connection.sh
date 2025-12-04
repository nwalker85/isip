#!/bin/bash
set -euo pipefail

# SIP Connection Test Script for iSIP
# Demonstrates connecting to sip:+19999999999@2g0282esbg2.sip.livekit.cloud

echo "=== iSIP Connection Test ==="
echo ""

# Load environment variables from .env file
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -f "$SCRIPT_DIR/.env" ]; then
    echo "Loading configuration from .env file..."
    set -a
    source "$SCRIPT_DIR/.env"
    set +a
else
    echo "WARNING: No .env file found at $SCRIPT_DIR/.env"
fi

# Configuration
GATEWAY="${SIP_GATEWAY:-2g0282esbg2.sip.livekit.cloud}"
PHONE="+19999999999"
PROMPT_TEXT="Hello, this is a test call from iSIP. Please respond if you can hear this message."

# Check for required credentials
if [ -z "${SIP_USERNAME:-}" ] || [ "${SIP_USERNAME}" = "your_username_here" ]; then
    echo "ERROR: SIP_USERNAME not set in .env file"
    echo "Please edit .env and set your SIP username"
    exit 1
fi

if [ -z "${SIP_PASSWORD:-}" ] || [ "${SIP_PASSWORD}" = "your_password_here" ]; then
    echo "ERROR: SIP_PASSWORD not set in .env file"
    echo "Please edit .env and set your SIP password"
    exit 1
fi

if [ -z "${OPENAI_API_KEY:-}" ]; then
    echo "WARNING: OPENAI_API_KEY not set - will skip TTS prompt generation"
fi

if [ -z "${DEEPGRAM_API_KEY:-}" ]; then
    echo "WARNING: DEEPGRAM_API_KEY not set - will skip transcription"
fi

# Check if we're in the virtual environment
if [ -z "${VIRTUAL_ENV:-}" ]; then
    echo "Activating virtual environment..."
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    VENV_PATH="$SCRIPT_DIR/sdk/python/.venv"
    
    if [ ! -d "$VENV_PATH" ]; then
        echo "ERROR: Virtual environment not found at $VENV_PATH"
        echo "Please run: cd sdk/python && python -m venv .venv && pip install -e ."
        exit 1
    fi
    
    source "$VENV_PATH/bin/activate"
fi

# Check if siptester is installed
if ! command -v siptester &> /dev/null; then
    echo "ERROR: siptester command not found"
    echo "Please install: cd sdk/python && pip install -e ."
    exit 1
fi

echo "Configuration:"
echo "  Gateway:  $GATEWAY"
echo "  Phone:    $PHONE"
echo "  Username: $SIP_USERNAME"
echo "  Password: ${SIP_PASSWORD:0:3}***"
echo ""
echo "Attempting SIP connection..."
echo ""

# Build the command
CMD=(
    siptester call
    --gateway "$GATEWAY"
    --user "$SIP_USERNAME"
    --password "$SIP_PASSWORD"
    --phone "$PHONE"
)

# Add optional parameters if API keys are available
if [ -n "${OPENAI_API_KEY:-}" ]; then
    CMD+=(--prompt-text "$PROMPT_TEXT")
    CMD+=(--openai-key "$OPENAI_API_KEY")
fi

if [ -n "${DEEPGRAM_API_KEY:-}" ]; then
    CMD+=(--deepgram-key "$DEEPGRAM_API_KEY")
fi

# Execute the call
echo "Executing: ${CMD[*]}"
echo ""
"${CMD[@]}"

EXIT_CODE=$?

echo ""
if [ $EXIT_CODE -eq 0 ]; then
    echo "✓ Connection test completed successfully"
else
    echo "✗ Connection test failed with exit code $EXIT_CODE"
fi

exit $EXIT_CODE

