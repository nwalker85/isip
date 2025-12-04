#!/usr/bin/env python3
"""
End-to-End Test for iSIP
Tests the complete flow: TTS → SIP → Recording → Transcription
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# Load environment
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from siptester import Sippy, VoiceService, SipHeaders


def print_section(title):
    """Print formatted section header"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60 + "\n")


def check_prerequisites():
    """Verify all required configuration is present"""
    print_section("Checking Prerequisites")
    
    required = {
        "OPENAI_API_KEY": "OpenAI TTS",
        "DEEPGRAM_API_KEY": "Deepgram STT",
        "SIP_USERNAME": "LiveKit SIP Username",
        "SIP_PASSWORD": "LiveKit SIP Password",
    }
    
    missing = []
    for var, desc in required.items():
        value = os.getenv(var)
        if not value or value.startswith("your_"):
            print(f"  ✗ {desc:25} - NOT SET ({var})")
            missing.append(var)
        else:
            masked = value[:15] + "..." if len(value) > 15 else value
            print(f"  ✓ {desc:25} - {masked}")
    
    if missing:
        print(f"\n⚠️  Missing: {', '.join(missing)}")
        print("\nPlease set these in your .env file:")
        for var in missing:
            print(f"  {var}=your_value_here")
        return False
    
    print("\n✓ All prerequisites satisfied")
    return True


def test_tts_generation():
    """Test OpenAI TTS prompt generation"""
    print_section("Test 1: OpenAI TTS Generation")
    
    try:
        openai = VoiceService("openai", "tts-1", voice="alloy")
        print(f"  Provider: {openai.provider}")
        print(f"  Model: {openai.model}")
        print(f"  Voice: {openai.voice}")
        
        sippy = Sippy(voice_service=openai)
        test_file = sippy.output_dir / f"e2e_test_{datetime.now():%Y%m%d_%H%M%S}.wav"
        
        print(f"\n  Generating audio prompt...")
        sippy._synthesize_prompt(
            "Hello, this is an end to end test of the iSIP system. Please respond if you can hear this message.",
            test_file
        )
        
        if test_file.exists():
            size_kb = test_file.stat().st_size / 1024
            print(f"  ✓ Generated: {test_file.name}")
            print(f"  ✓ Size: {size_kb:.1f} KB")
            print(f"  ✓ Path: {test_file}")
            return True, test_file
        else:
            print(f"  ✗ File not created")
            return False, None
            
    except Exception as e:
        print(f"  ✗ TTS generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False, None


def test_sip_headers():
    """Test SIP header parsing and configuration"""
    print_section("Test 2: SIP Configuration")
    
    try:
        target = SipHeaders(
            sip_to="sip:+19999999999@2g0282esbg2.sip.livekit.cloud"
        )
        
        print(f"  SIP URI: {target.sip_to}")
        print(f"  Phone: {target.phone}")
        print(f"  Gateway: {target.gateway}")
        print(f"  Auth User: {target.auth_user}")
        print(f"  Auth Pass: {'*' * 8}")
        print(f"  Local Port: {target.local_port}")
        
        print(f"\n  ✓ SIP configuration valid")
        return True, target
        
    except Exception as e:
        print(f"  ✗ SIP configuration failed: {e}")
        return False, None


def test_full_call(target, prompt_text):
    """Test complete SIP call with TTS and transcription"""
    print_section("Test 3: Live SIP Call")
    
    try:
        # Configure services
        openai = VoiceService("openai", "tts-1", voice="alloy")
        deepgram = VoiceService("deepgram", "nova-2")
        
        sippy = Sippy(
            voice_service=openai,
            transcription_service=deepgram,
            log_level=4  # More verbose logging
        )
        
        print(f"  Calling: {target.phone}")
        print(f"  Gateway: {target.gateway}")
        print(f"  Prompt: {prompt_text[:50]}...")
        print(f"\n  ⏳ Establishing call (this may take 30+ seconds)...\n")
        
        # Make the call
        result = sippy.call(
            target=target,
            prompt=prompt_text,
            timeout=30.0,
            transcribe=True,
        )
        
        # Report results
        print(f"\n  {'='*58}")
        print(f"  Call Results")
        print(f"  {'='*58}\n")
        
        print(f"  Established: {result.established}")
        print(f"  Duration: {result.duration:.2f} seconds")
        
        if result.error:
            print(f"  ✗ Error: {result.error}")
            return False
        
        if result.established:
            print(f"  ✓ Call connected successfully")
            
            if result.prompt_file:
                print(f"  ✓ Prompt file: {result.prompt_file}")
            
            if result.recording and result.recording.exists():
                size_kb = result.recording.stat().st_size / 1024
                print(f"  ✓ Recording: {result.recording}")
                print(f"  ✓ Recording size: {size_kb:.1f} KB")
            else:
                print(f"  ⚠️  No recording captured")
            
            if result.transcript:
                print(f"\n  Transcript:")
                print(f"  {'-'*58}")
                print(f"  {result.transcript}")
                print(f"  {'-'*58}")
            else:
                print(f"  ⚠️  No transcript available")
            
            return True
        else:
            print(f"  ✗ Call failed to establish")
            return False
            
    except KeyboardInterrupt:
        print(f"\n  ⚠️  Test interrupted by user")
        return False
    except Exception as e:
        print(f"  ✗ Call failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all end-to-end tests"""
    print("\n" + "█" * 60)
    print("  iSIP End-to-End Test Suite")
    print("█" * 60)
    
    # Check prerequisites
    if not check_prerequisites():
        print("\n❌ Cannot proceed without required configuration")
        sys.exit(1)
    
    # Test 1: TTS Generation
    tts_ok, test_file = test_tts_generation()
    if not tts_ok:
        print("\n❌ TTS test failed - cannot proceed")
        sys.exit(1)
    
    # Test 2: SIP Configuration
    sip_ok, target = test_sip_headers()
    if not sip_ok:
        print("\n❌ SIP configuration test failed - cannot proceed")
        sys.exit(1)
    
    # Test 3: Full Call
    print("\n⚠️  About to place a live SIP call")
    print("   This will:")
    print("   - Generate TTS audio with OpenAI")
    print("   - Connect to LiveKit SIP gateway")
    print("   - Place call to +19999999999")
    print("   - Play the generated prompt")
    print("   - Record the response")
    print("   - Transcribe with Deepgram")
    
    response = input("\n   Proceed with live call? [y/N]: ")
    if response.lower() != 'y':
        print("\n  Test cancelled by user")
        sys.exit(0)
    
    call_ok = test_full_call(
        target=target,
        prompt_text="Hello, this is an end to end test of the iSIP system. Please respond if you can hear this message.",
    )
    
    # Final summary
    print_section("Test Summary")
    print(f"  TTS Generation:  {'✓ PASS' if tts_ok else '✗ FAIL'}")
    print(f"  SIP Config:      {'✓ PASS' if sip_ok else '✗ FAIL'}")
    print(f"  Live SIP Call:   {'✓ PASS' if call_ok else '✗ FAIL'}")
    
    if tts_ok and sip_ok and call_ok:
        print("\n🎉 All tests passed! The iSIP stack is fully operational.")
        sys.exit(0)
    else:
        print("\n⚠️  Some tests failed. Review output above.")
        sys.exit(1)


if __name__ == "__main__":
    main()

