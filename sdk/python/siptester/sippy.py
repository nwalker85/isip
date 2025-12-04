"""
Sippy - A high-level, intuitive API for SIP testing with AI voice services.

Example usage:
    from sippy import VoiceService, SipHeaders, Sippy
    
    openai = VoiceService("openai", "gpt-4o-realtime-preview", api_key=OPENAI_API_KEY)
    deepgram = VoiceService("deepgram", "nova-2", api_key=DEEPGRAM_API_KEY)
    
    sippy = Sippy(voice_service=openai, transcription_service=deepgram)
    
    target = SipHeaders(
        sip_to="sip:+19999999999@2g0282esbg2.sip.livekit.cloud",
        sip_from="tester",
        auth_user="tester",
        auth_password="secret",
    )
    
    result = sippy.call(target, prompt="Hello, this is a test call")
    print(result.transcript)
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Literal
from urllib.parse import urlparse

from .client import SipTestClient, SipScenario, CallResult, synthesize_prompt, transcribe_recording


@dataclass
class VoiceService:
    """Configuration for AI voice services (TTS/STT)."""
    
    provider: Literal["openai", "elevenlabs", "deepgram"]
    model: str
    api_key: Optional[str] = None
    voice: str = "alloy"  # For TTS services
    
    def __post_init__(self):
        """Load API key from environment if not provided."""
        if self.api_key is None:
            env_key_map = {
                "openai": "OPENAI_API_KEY",
                "elevenlabs": "ELEVENLABS_API_KEY",
                "deepgram": "DEEPGRAM_API_KEY",
            }
            env_var = env_key_map.get(self.provider)
            if env_var:
                self.api_key = os.getenv(env_var)
            
            if not self.api_key:
                raise ValueError(
                    f"API key required for {self.provider}. "
                    f"Set {env_var} environment variable or pass api_key parameter."
                )


@dataclass
class SipHeaders:
    """SIP connection headers and authentication."""
    
    sip_to: str  # Full SIP URI: sip:+19999999999@gateway.com
    sip_from: Optional[str] = None  # Username
    auth_user: Optional[str] = None
    auth_password: Optional[str] = None
    gateway: Optional[str] = None
    phone: Optional[str] = None
    local_ip: Optional[str] = None
    local_port: int = 5060
    
    def __post_init__(self):
        """Parse SIP URI and extract components."""
        # Parse the sip_to URI
        if self.sip_to.startswith("sip:"):
            uri = self.sip_to[4:]  # Remove "sip:" prefix
            if "@" in uri:
                phone_part, gateway_part = uri.split("@", 1)
                if self.phone is None:
                    self.phone = phone_part
                if self.gateway is None:
                    self.gateway = gateway_part
        
        # Use sip_from as default auth_user if not specified
        if self.auth_user is None and self.sip_from:
            self.auth_user = self.sip_from
        
        # Load from environment if still missing
        if self.auth_user is None:
            self.auth_user = os.getenv("SIP_USERNAME")
        if self.auth_password is None:
            self.auth_password = os.getenv("SIP_PASSWORD")
        if self.gateway is None:
            self.gateway = os.getenv("SIP_GATEWAY", "2g0282esbg2.sip.livekit.cloud")
        
        # Validation
        if not self.gateway:
            raise ValueError("SIP gateway required (set SIP_GATEWAY or pass gateway parameter)")
        if not self.phone:
            raise ValueError("Phone number required in sip_to URI")
        if not self.auth_user:
            raise ValueError("Authentication user required (set SIP_USERNAME or pass auth_user)")
        if not self.auth_password:
            raise ValueError("Authentication password required (set SIP_PASSWORD or pass auth_password)")


@dataclass
class CallResponse:
    """Result of a SIP call."""
    
    established: bool
    duration: float
    recording: Optional[Path] = None
    transcript: Optional[str] = None
    prompt_file: Optional[Path] = None
    error: Optional[str] = None
    
    def __bool__(self) -> bool:
        """Allow checking if call was successful with if result:"""
        return self.established and self.error is None


class Sippy:
    """High-level SIP testing client with AI voice integration."""
    
    def __init__(
        self,
        voice_service: Optional[VoiceService] = None,
        transcription_service: Optional[VoiceService] = None,
        output_dir: Optional[Path] = None,
        log_level: int = 3,
    ):
        """
        Initialize Sippy client.
        
        Args:
            voice_service: TTS service for generating prompts (OpenAI, ElevenLabs)
            transcription_service: STT service for transcribing responses (Deepgram)
            output_dir: Directory for storing recordings and prompts
            log_level: PJSIP log level (0-5, higher = more verbose)
        """
        self.voice_service = voice_service
        self.transcription_service = transcription_service
        self.output_dir = output_dir or Path.cwd() / "sippy_output"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.log_level = log_level
        self._call_counter = 0
    
    def call(
        self,
        target: SipHeaders,
        prompt: Optional[str] = None,
        prompt_file: Optional[Path] = None,
        timeout: float = 30.0,
        transcribe: bool = True,
    ) -> CallResponse:
        """
        Make a SIP call to the target.
        
        Args:
            target: SIP headers with connection details
            prompt: Text to synthesize as audio prompt (requires voice_service)
            prompt_file: Pre-recorded audio file to play
            timeout: Call timeout in seconds
            transcribe: Whether to transcribe the response (requires transcription_service)
        
        Returns:
            CallResponse with call details and transcript
        """
        self._call_counter += 1
        call_id = f"call_{self._call_counter:03d}"
        
        # Prepare prompt file
        if prompt and not prompt_file:
            if not self.voice_service:
                return CallResponse(
                    established=False,
                    duration=0.0,
                    error="Voice service required for text-to-speech. Pass voice_service to Sippy().",
                )
            
            prompt_file = self.output_dir / f"{call_id}_prompt.wav"
            try:
                self._synthesize_prompt(prompt, prompt_file)
            except Exception as e:
                return CallResponse(
                    established=False,
                    duration=0.0,
                    error=f"Failed to synthesize prompt: {e}",
                )
        
        # Prepare recording file
        record_file = self.output_dir / f"{call_id}_response.wav"
        
        # Create scenario
        scenario = SipScenario(
            phone=target.phone,
            prompt_file=prompt_file,
            record_file=record_file,
            timeout=timeout,
        )
        
        # Execute call
        try:
            with SipTestClient(
                gateway=target.gateway,
                username=target.auth_user,
                password=target.auth_password,
                local_ip=target.local_ip,
                local_port=target.local_port,
                log_level=self.log_level,
            ) as client:
                result = client.run_scenario(scenario)
        except Exception as e:
            return CallResponse(
                established=False,
                duration=0.0,
                error=f"Call failed: {e}",
            )
        
        # Transcribe response
        transcript = None
        if transcribe and result.recording and result.recording.exists():
            if not self.transcription_service:
                transcript = "[transcription service not configured]"
            else:
                try:
                    transcript = self._transcribe_recording(result.recording)
                except Exception as e:
                    transcript = f"[transcription failed: {e}]"
        
        return CallResponse(
            established=result.established,
            duration=result.duration,
            recording=result.recording,
            transcript=transcript,
            prompt_file=prompt_file,
        )
    
    def _synthesize_prompt(self, text: str, output_path: Path) -> None:
        """Generate audio prompt using configured voice service."""
        if self.voice_service.provider == "openai":
            synthesize_prompt(
                text=text,
                output_path=output_path,
                openai_api_key=self.voice_service.api_key,
                voice=self.voice_service.voice,
            )
        elif self.voice_service.provider == "elevenlabs":
            # TODO: Implement ElevenLabs TTS
            raise NotImplementedError("ElevenLabs TTS not yet implemented")
        else:
            raise ValueError(f"Unsupported TTS provider: {self.voice_service.provider}")
    
    def _transcribe_recording(self, audio_path: Path) -> str:
        """Transcribe audio recording using configured transcription service."""
        if self.transcription_service.provider == "deepgram":
            return transcribe_recording(
                audio_path=audio_path,
                deepgram_api_key=self.transcription_service.api_key,
            )
        else:
            raise ValueError(f"Unsupported STT provider: {self.transcription_service.provider}")


# Convenience function for quick calls
def quick_call(
    phone: str,
    prompt: str,
    gateway: Optional[str] = None,
    username: Optional[str] = None,
    password: Optional[str] = None,
) -> CallResponse:
    """
    Make a quick SIP call with minimal configuration.
    
    Example:
        result = quick_call(
            phone="+19999999999",
            prompt="Hello, this is a test",
            username="tester",
            password="secret"
        )
        print(result.transcript)
    """
    # Auto-configure services from environment
    openai = VoiceService("openai", "tts-1")
    deepgram = VoiceService("deepgram", "nova-2")
    
    sippy = Sippy(voice_service=openai, transcription_service=deepgram)
    
    target = SipHeaders(
        sip_to=f"sip:{phone}@{gateway or os.getenv('SIP_GATEWAY', '2g0282esbg2.sip.livekit.cloud')}",
        auth_user=username,
        auth_password=password,
    )
    
    return sippy.call(target, prompt=prompt)

