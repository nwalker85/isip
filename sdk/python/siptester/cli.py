from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

from .client import CallResult, SipScenario, SipTestClient, synthesize_prompt, transcribe_recording


def _add_common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--gateway", required=True, help="SIP gateway (e.g. sip.example.com)")
    parser.add_argument("--user", required=True, help="SIP username")
    parser.add_argument("--password", default="", help="SIP password")
    parser.add_argument("--local-ip", default=None, help="Public IP advertised in SDP")
    parser.add_argument("--local-port", type=int, default=5060, help="Local SIP port")
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging")


def handle_call(args: argparse.Namespace) -> int:
    prompt_file: Path
    if args.prompt_file:
        prompt_file = Path(args.prompt_file)
    elif args.prompt_text:
        if not args.openai_key:
            raise SystemExit("OPENAI key required to synthesize prompt text")
        prompt_file = Path(args.output_dir) / "prompt.wav"
        synthesize_prompt(args.prompt_text, prompt_file, args.openai_key)
    else:
        prompt_file = Path(args.output_dir) / "prompt.wav"

    scenario = SipScenario(
        phone=args.phone,
        prompt_file=prompt_file if prompt_file.exists() else None,
        record_file=Path(args.output_dir) / "response.wav",
        timeout=args.timeout,
    )

    with SipTestClient(
        gateway=args.gateway,
        username=args.user,
        password=args.password,
        local_ip=args.local_ip,
        local_port=args.local_port,
        log_level=5 if args.verbose else 3,
    ) as client:
        result = client.run_scenario(scenario)
        _print_result(result, args, scenario)
    return 0


def handle_suite(args: argparse.Namespace) -> int:
    suite_path = Path(args.suite)
    data = json.loads(suite_path.read_text())
    default_phone = data.get("phone")
    tests = data["tests"]

    with SipTestClient(
        gateway=args.gateway,
        username=args.user,
        password=args.password,
        local_ip=args.local_ip,
        local_port=args.local_port,
        log_level=5 if args.verbose else 3,
    ) as client:
        for test in tests:
            phone = test.get("phone") or default_phone
            if not phone:
                raise ValueError(f"Test {test['name']} missing phone number")
            prompt_file: Path
            if args.prompt_dir:
                prompt_file = Path(args.prompt_dir) / f"{test['name']}.wav"
                if args.openai_key:
                    synthesize_prompt(test["prompt"], prompt_file, args.openai_key)
            else:
                prompt_file = Path(test.get("prompt_file", "prompt.wav"))

            scenario = SipScenario(
                phone=phone,
                prompt_file=prompt_file if prompt_file.exists() else None,
                record_file=Path(args.output_dir) / f"{test['name']}_response.wav",
                timeout=args.timeout,
            )
            result = client.run_scenario(scenario)
            _print_result(result, args, scenario, test_name=test["name"])
    return 0


def _print_result(result: CallResult, args: argparse.Namespace, scenario: SipScenario, test_name: str | None = None):
    label = test_name or "call"
    status = "PASS" if result.established else "FAIL"
    print(f"[{label}] {status} duration={result.duration:.1f}s recording={result.recording}")

    if result.recording and args.deepgram_key:
        transcript = transcribe_recording(result.recording, args.deepgram_key)
        print(f"[{label}] transcript: {transcript}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Local SIP testing CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    call_p = sub.add_parser("call", help="Place a single call")
    _add_common(call_p)
    call_p.add_argument("--phone", required=True)
    call_p.add_argument("--prompt-file")
    call_p.add_argument("--prompt-text")
    call_p.add_argument("--output-dir", default="artifacts")
    call_p.add_argument("--timeout", type=float, default=30.0)
    call_p.add_argument("--openai-key", default=None)
    call_p.add_argument("--deepgram-key", default=None)
    call_p.set_defaults(func=handle_call)

    suite_p = sub.add_parser("suite", help="Run a JSON test suite")
    _add_common(suite_p)
    suite_p.add_argument("--suite", required=True, help="Path to JSON spec")
    suite_p.add_argument("--prompt-dir", default="prompts", help="Directory to store prompts")
    suite_p.add_argument("--output-dir", default="artifacts")
    suite_p.add_argument("--timeout", type=float, default=30.0)
    suite_p.add_argument("--openai-key", default=None)
    suite_p.add_argument("--deepgram-key", default=None)
    suite_p.set_defaults(func=handle_suite)

    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())

