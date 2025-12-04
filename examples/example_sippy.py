#!/usr/bin/env python3
"""
Example usage of the Sippy high-level API.

This demonstrates the clean, intuitive interface for making SIP calls
with integrated AI voice services.
"""

import os
from pathlib import Path
from siptester import Sippy, VoiceService, SipHeaders, quick_call

# Load environment variables from .env if using python-dotenv
# pip install python-dotenv
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def example_basic_call():
    """Basic call example with OpenAI TTS and Deepgram STT."""
    print("=== Basic Sippy Call ===\n")
    
    # Configure AI voice services
    openai = VoiceService(
        provider="openai",
        model="tts-1",
        voice="alloy",
        # api_key auto-loaded from OPENAI_API_KEY env var
    )
    
    deepgram = VoiceService(
        provider="deepgram",
        model="nova-2",
        # api_key auto-loaded from DEEPGRAM_API_KEY env var
    )
    
    # Create Sippy client
    sippy = Sippy(
        voice_service=openai,
        transcription_service=deepgram,
        output_dir=Path("./sippy_output"),
    )
    
    # Configure SIP target
    target = SipHeaders(
        sip_to="sip:+19999999999@2g0282esbg2.sip.livekit.cloud",
        # auth_user and auth_password auto-loaded from SIP_USERNAME/SIP_PASSWORD env vars
        # or you can specify them explicitly:
        # auth_user="your_username",
        # auth_password="your_password",
    )
    
    # Make the call
    result = sippy.call(
        target=target,
        prompt="Hello, this is a test call from Sippy. Please respond if you can hear this message.",
        timeout=30.0,
    )
    
    # Check results
    if result.established:
        print(f"✓ Call connected successfully")
        print(f"  Duration: {result.duration:.2f} seconds")
        if result.transcript:
            print(f"  Transcript: {result.transcript}")
        if result.recording:
            print(f"  Recording: {result.recording}")
    else:
        print(f"✗ Call failed: {result.error}")


def example_quick_call():
    """Quick call using the convenience function."""
    print("\n=== Quick Call Example ===\n")
    
    result = quick_call(
        phone="+19999999999",
        prompt="Hello, is anyone available?",
        username=os.getenv("SIP_USERNAME"),
        password=os.getenv("SIP_PASSWORD"),
    )
    
    if result:
        print(f"✓ Call successful: {result.transcript}")
    else:
        print(f"✗ Call failed: {result.error}")


def example_custom_gateway():
    """Example with custom gateway and configuration."""
    print("\n=== Custom Gateway Example ===\n")
    
    # Use ElevenLabs for TTS (when implemented)
    # elevenlabs = VoiceService("elevenlabs", "eleven_turbo_v2")
    
    openai = VoiceService("openai", "tts-1", voice="nova")
    deepgram = VoiceService("deepgram", "nova-2")
    
    sippy = Sippy(voice_service=openai, transcription_service=deepgram)
    
    # Custom SIP configuration
    target = SipHeaders(
        sip_to="sip:+15127812507@custom.gateway.com",
        auth_user="my_username",
        auth_password="my_password",
        local_ip="67.198.117.118",  # Your public IP if behind NAT
        local_port=5060,
    )
    
    result = sippy.call(
        target=target,
        prompt="Testing custom gateway configuration.",
        timeout=20.0,
    )
    
    print(f"Call established: {result.established}")
    print(f"Duration: {result.duration:.2f}s")


def example_without_transcription():
    """Make a call without transcription (TTS only)."""
    print("\n=== TTS Only (No Transcription) ===\n")
    
    openai = VoiceService("openai", "tts-1")
    
    # Don't pass transcription_service
    sippy = Sippy(voice_service=openai)
    
    target = SipHeaders(
        sip_to="sip:+19999999999@2g0282esbg2.sip.livekit.cloud",
    )
    
    result = sippy.call(
        target=target,
        prompt="This call won't be transcribed.",
        transcribe=False,  # Explicitly disable transcription
    )
    
    print(f"Call completed: {result.established}")


def example_pre_recorded_prompt():
    """Use a pre-recorded audio file instead of TTS."""
    print("\n=== Pre-recorded Prompt ===\n")
    
    deepgram = VoiceService("deepgram", "nova-2")
    
    # No voice_service needed if using pre-recorded audio
    sippy = Sippy(transcription_service=deepgram)
    
    target = SipHeaders(
        sip_to="sip:+19999999999@2g0282esbg2.sip.livekit.cloud",
    )
    
    prompt_file = Path("./my_custom_prompt.wav")
    
    if not prompt_file.exists():
        print(f"Note: {prompt_file} not found. Using TTS instead.")
        sippy.voice_service = VoiceService("openai", "tts-1")
        result = sippy.call(target=target, prompt="Fallback to TTS")
    else:
        result = sippy.call(
            target=target,
            prompt_file=prompt_file,
        )
    
    print(f"Transcript: {result.transcript}")


if __name__ == "__main__":
    print("Sippy - High-level SIP Testing API\n")
    print("=" * 50)
    
    # Check for required environment variables
    required_env = ["OPENAI_API_KEY", "DEEPGRAM_API_KEY", "SIP_USERNAME", "SIP_PASSWORD"]
    missing = [var for var in required_env if not os.getenv(var)]
    
    if missing:
        print(f"\n⚠️  Warning: Missing environment variables: {', '.join(missing)}")
        print("Please set them in your .env file or export them.")
        print("\nExample .env file:")
        print("  OPENAI_API_KEY=sk-...")
        print("  DEEPGRAM_API_KEY=...")
        print("  SIP_USERNAME=your_username")
        print("  SIP_PASSWORD=your_password")
        print("\nSome examples will fail without these set.")
    
    print("\nRunning examples...\n")
    
    try:
        example_basic_call()
    except Exception as e:
        print(f"Error in basic_call: {e}\n")
    
    try:
        example_quick_call()
    except Exception as e:
        print(f"Error in quick_call: {e}\n")
    
    # Uncomment to run additional examples:
    # example_custom_gateway()
    # example_without_transcription()
    # example_pre_recorded_prompt()
    
    print("\n" + "=" * 50)
    print("Examples complete!")

