from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import requests

try:
    import pjsua as pj
except ImportError as exc:  # pragma: no cover - only triggered if pj not installed
    raise RuntimeError(
        "pjsua Python bindings are required. Install pjproject via Homebrew (brew install pjproject)."
    ) from exc

log = logging.getLogger(__name__)


@dataclass
class SipScenario:
    phone: str
    prompt_file: Optional[Path] = None
    record_file: Path = Path("response.wav")
    timeout: float = 30.0


@dataclass
class CallResult:
    established: bool
    recording: Optional[Path]
    duration: float


def synthesize_prompt(text: str, output_path: Path, openai_api_key: str, voice: str = "alloy") -> None:
    """Generate a WAV prompt using OpenAI TTS."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    mp3_path = output_path.with_suffix(".mp3")
    response = requests.post(
        "https://api.openai.com/v1/audio/speech",
        headers={
            "Authorization": f"Bearer {openai_api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": "tts-1",
            "input": text,
            "voice": voice,
            "response_format": "mp3",
        },
        timeout=60,
    )
    response.raise_for_status()
    mp3_path.write_bytes(response.content)

    import subprocess

    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-loglevel",
            "error",
            "-i",
            str(mp3_path),
            "-ar",
            "8000",
            "-ac",
            "1",
            "-sample_fmt",
            "s16",
            str(output_path),
        ],
        check=True,
    )
    mp3_path.unlink(missing_ok=True)


def transcribe_recording(audio_path: Path, deepgram_api_key: str) -> str:
    """Return the transcript using Deepgram."""
    resp = requests.post(
        "https://api.deepgram.com/v1/listen?model=nova-2&smart_format=true",
        headers={
            "Authorization": f"Token {deepgram_api_key}",
            "Content-Type": "audio/wav",
        },
        data=audio_path.read_bytes(),
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()["results"]["channels"][0]["alternatives"][0]["transcript"]


class _CallCallback(pj.CallCallback):
    def __init__(self, scenario: SipScenario, lib: pj.Lib, call: Optional[pj.Call] = None):
        super().__init__(call)
        self.scenario = scenario
        self.lib = lib
        self.established = False
        self.done = False
        self.player_id = None
        self.recorder_id = None
        self.start_ts: Optional[float] = None

    def on_state(self):
        info = self.call.info()
        log.debug("Call state: %s", info.state_text)
        if info.state == pj.CallState.CONFIRMED:
            self.established = True
            self.start_ts = time.time()
        if info.state == pj.CallState.DISCONNECTED:
            self.done = True

    def on_media_state(self):
        info = self.call.info()
        if info.media_state == pj.MediaState.ACTIVE:
            call_slot = info.conf_slot
            if self.scenario.prompt_file and self.scenario.prompt_file.exists():
                self.player_id = self.lib.create_player(str(self.scenario.prompt_file), loop=False)
                player_slot = self.lib.player_get_slot(self.player_id)
                self.lib.conf_connect(player_slot, call_slot)
            self.recorder_id = self.lib.create_recorder(str(self.scenario.record_file))
            recorder_slot = self.lib.recorder_get_slot(self.recorder_id)
            self.lib.conf_connect(call_slot, recorder_slot)


class SipTestClient:
    """Thin wrapper around the pjsua API."""

    def __init__(
        self,
        gateway: str,
        username: str,
        password: Optional[str] = None,
        local_ip: Optional[str] = None,
        local_port: int = 5060,
        log_level: int = 3,
    ):
        self.gateway = gateway
        self.username = username
        self.password = password or ""
        self.local_ip = local_ip
        self.local_port = local_port
        self.log_level = log_level
        self.lib = pj.Lib()
        self.account: Optional[pj.Account] = None

    def __enter__(self) -> "SipTestClient":
        self.start()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.stop()

    def start(self) -> None:
        log_cfg = pj.LogConfig(level=self.log_level, callback=self._log_cb)
        media_cfg = pj.MediaConfig()
        # Note: clock_rate must be set after init, not in MediaConfig constructor
        
        self.lib.init(log_cfg=log_cfg, media_cfg=media_cfg)
        # Set clock rate on the library after init
        # media_cfg.clock_rate = 8000  # This is set globally by PJSIP
        transport = pj.TransportConfig()
        transport.port = self.local_port
        if self.local_ip:
            transport.bound_addr = self.local_ip
        self.lib.create_transport(pj.TransportType.UDP, transport)
        self.lib.start()

        acc_cfg = pj.AccountConfig()
        # Extract just the user part if username is an email address
        user_part = self.username.split('@')[0] if '@' in self.username else self.username
        acc_cfg.id = f"sip:{user_part}@{self.gateway}"
        acc_cfg.reg_uri = f"sip:{self.gateway}"
        acc_cfg.auth_cred = [pj.AuthCred("*", self.username, self.password)]
        self.account = self.lib.create_account(acc_cfg)
        
        # Wait briefly for account to be ready (handle_events takes milliseconds as int)
        for _ in range(10):
            self.lib.handle_events(100)  # 100ms
            if self.account.info().online_status:
                break

    def stop(self) -> None:
        if self.account is not None:
            self.account.delete()
            self.account = None
        if self.lib:
            self.lib.destroy()
            self.lib = None  # type: ignore[assignment]

    def run_scenario(self, scenario: SipScenario) -> CallResult:
        if self.account is None:
            raise RuntimeError("Client not started")

        uri = f"sip:{scenario.phone}@{self.gateway}"
        callback = _CallCallback(scenario, self.lib)
        call = self.account.make_call(uri, cb=callback)

        deadline = time.time() + scenario.timeout
        while time.time() < deadline and not callback.done:  # type: ignore[attr-defined]
            self.lib.handle_events(200)  # 200ms

        if not callback.done:
            call.hangup()

        duration = 0.0
        if callback.start_ts:
            duration = max(0.0, time.time() - callback.start_ts)

        recording = scenario.record_file if scenario.record_file.exists() else None
        return CallResult(established=callback.established, recording=recording, duration=duration)

    @staticmethod
    def _log_cb(level, _, message):
        log.log(logging.DEBUG if level <= 3 else logging.INFO, "pjsua: %s", message)

