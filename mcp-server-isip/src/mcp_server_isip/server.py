#!/usr/bin/env python3
"""
MCP Server for iSIP - Make phone calls from AI assistants

This server exposes iSIP's voice AI capabilities via the Model Context Protocol,
enabling AI assistants to make phone calls, generate TTS prompts, and transcribe responses.
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
    Resource,
    Prompt,
    PromptMessage,
    GetPromptResult,
)
from pydantic import BaseModel, Field

# Add parent SDK to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "sdk" / "python"))

try:
    from siptester import Sippy, VoiceService, SipHeaders, CallResponse, quick_call
except ImportError:
    print("ERROR: iSIP SDK not found. Please install: cd sdk/python && pip install -e .", file=sys.stderr)
    sys.exit(1)


class CallRecord(BaseModel):
    """Record of a call made through the MCP server."""
    id: int
    timestamp: str
    phone: str
    prompt: str
    duration: float
    established: bool
    transcript: Optional[str] = None
    recording_path: Optional[Path] = None
    error: Optional[str] = None


class MCPServerState:
    """State management for the MCP server."""
    
    def __init__(self):
        self.calls: list[CallRecord] = []
        self.call_counter = 0
        self.output_dir = Path(os.getenv("ISIP_OUTPUT_DIR", "./sippy_output"))
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Load environment variables
        from dotenv import load_dotenv
        env_path = Path(__file__).parent.parent.parent.parent / ".env"
        if env_path.exists():
            load_dotenv(env_path)
    
    def add_call(self, result: CallResponse, phone: str, prompt: str) -> CallRecord:
        """Add a call to the history."""
        self.call_counter += 1
        record = CallRecord(
            id=self.call_counter,
            timestamp=datetime.now().isoformat(),
            phone=phone,
            prompt=prompt,
            duration=result.duration,
            established=result.established,
            transcript=result.transcript,
            recording_path=result.recording,
            error=result.error,
        )
        self.calls.append(record)
        return record
    
    def get_call(self, call_id: int) -> Optional[CallRecord]:
        """Get a specific call by ID."""
        for call in self.calls:
            if call.id == call_id:
                return call
        return None


# Initialize server and state
app = Server("mcp-server-isip")
state = MCPServerState()


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools for making calls."""
    return [
        Tool(
            name="make_call",
            description=(
                "Make a SIP phone call with TTS prompt and transcription. "
                "Returns call duration, transcript, and recording info. "
                "Use this for full-featured calls with custom configuration."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "phone": {
                        "type": "string",
                        "description": "Phone number to call (E.164 format, e.g., +19999999999)",
                    },
                    "prompt": {
                        "type": "string",
                        "description": "Text to speak during the call (will be converted to audio via TTS)",
                    },
                    "timeout": {
                        "type": "number",
                        "description": "Call timeout in seconds (default: 30)",
                        "default": 30.0,
                    },
                    "voice": {
                        "type": "string",
                        "description": "TTS voice to use (alloy, nova, shimmer, echo, fable, onyx)",
                        "default": "alloy",
                    },
                },
                "required": ["phone", "prompt"],
            },
        ),
        Tool(
            name="quick_call",
            description=(
                "Make a quick SIP call with minimal configuration. "
                "Simpler than make_call, uses defaults for everything. "
                "Perfect for simple test calls or quick messages."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "phone": {
                        "type": "string",
                        "description": "Phone number to call (E.164 format)",
                    },
                    "prompt": {
                        "type": "string",
                        "description": "What to say during the call",
                    },
                },
                "required": ["phone", "prompt"],
            },
        ),
        Tool(
            name="list_recordings",
            description=(
                "List recent call recordings made through this MCP server session. "
                "Returns call ID, timestamp, phone number, duration, and transcript."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "number",
                        "description": "Maximum number of recordings to return (default: 10)",
                        "default": 10,
                    },
                },
            },
        ),
        Tool(
            name="get_transcript",
            description=(
                "Get the full transcript of a specific call by ID. "
                "Use list_recordings first to get call IDs."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "call_id": {
                        "type": "number",
                        "description": "Call ID from list_recordings",
                    },
                },
                "required": ["call_id"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool calls."""
    
    if name == "make_call":
        return await handle_make_call(arguments)
    elif name == "quick_call":
        return await handle_quick_call(arguments)
    elif name == "list_recordings":
        return await handle_list_recordings(arguments)
    elif name == "get_transcript":
        return await handle_get_transcript(arguments)
    else:
        raise ValueError(f"Unknown tool: {name}")


async def handle_make_call(args: dict) -> list[TextContent]:
    """Handle make_call tool."""
    phone = args["phone"]
    prompt = args["prompt"]
    timeout = args.get("timeout", 30.0)
    voice = args.get("voice", "alloy")
    
    try:
        # Configure services
        openai = VoiceService("openai", "tts-1", voice=voice)
        deepgram = VoiceService("deepgram", "nova-2")
        
        sippy = Sippy(
            voice_service=openai,
            transcription_service=deepgram,
            output_dir=state.output_dir,
        )
        
        # Configure target
        gateway = os.getenv("SIP_GATEWAY", "2g0282esbg2.sip.livekit.cloud")
        target = SipHeaders(sip_to=f"sip:{phone}@{gateway}")
        
        # Make the call (run in thread to avoid blocking)
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: sippy.call(target, prompt=prompt, timeout=timeout)
        )
        
        # Record the call
        record = state.add_call(result, phone, prompt)
        
        # Format response
        if result.established:
            response = (
                f"✓ Call completed successfully!\n\n"
                f"Call ID: {record.id}\n"
                f"Phone: {phone}\n"
                f"Duration: {result.duration:.2f} seconds\n"
                f"Recording: {result.recording}\n\n"
                f"Transcript:\n{result.transcript or '[No transcript available]'}"
            )
        else:
            response = (
                f"✗ Call failed\n\n"
                f"Phone: {phone}\n"
                f"Error: {result.error or 'Unknown error'}"
            )
        
        return [TextContent(type="text", text=response)]
        
    except Exception as e:
        return [TextContent(type="text", text=f"Error making call: {str(e)}")]


async def handle_quick_call(args: dict) -> list[TextContent]:
    """Handle quick_call tool."""
    phone = args["phone"]
    prompt = args["prompt"]
    
    try:
        # Make the call
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: quick_call(phone=phone, prompt=prompt)
        )
        
        # Record the call
        record = state.add_call(result, phone, prompt)
        
        # Format response
        response = (
            f"✓ Quick call completed!\n\n"
            f"Call ID: {record.id}\n"
            f"Established: {result.established}\n"
            f"Duration: {result.duration:.2f}s\n"
            f"Response: {result.transcript or '[No response]'}"
        )
        
        return [TextContent(type="text", text=response)]
        
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def handle_list_recordings(args: dict) -> list[TextContent]:
    """Handle list_recordings tool."""
    limit = args.get("limit", 10)
    
    recent_calls = state.calls[-limit:]
    
    if not recent_calls:
        return [TextContent(type="text", text="No recordings yet. Make a call first!")]
    
    lines = ["Recent Calls:\n"]
    for call in reversed(recent_calls):  # Most recent first
        status = "✓" if call.established else "✗"
        lines.append(
            f"{status} Call #{call.id} - {call.phone}\n"
            f"   Time: {call.timestamp}\n"
            f"   Duration: {call.duration:.2f}s\n"
            f"   Transcript: {(call.transcript or '[None]')[:80]}...\n"
        )
    
    return [TextContent(type="text", text="\n".join(lines))]


async def handle_get_transcript(args: dict) -> list[TextContent]:
    """Handle get_transcript tool."""
    call_id = int(args["call_id"])
    call = state.get_call(call_id)
    
    if not call:
        return [TextContent(type="text", text=f"Call #{call_id} not found")]
    
    response = (
        f"Call #{call.id} Transcript\n"
        f"{'=' * 60}\n\n"
        f"Phone: {call.phone}\n"
        f"Time: {call.timestamp}\n"
        f"Duration: {call.duration:.2f} seconds\n"
        f"Status: {'✓ Connected' if call.established else '✗ Failed'}\n\n"
        f"You said:\n{call.prompt}\n\n"
        f"They said:\n{call.transcript or '[No transcript available]'}\n"
    )
    
    return [TextContent(type="text", text=response)]


@app.list_resources()
async def list_resources() -> list[Resource]:
    """List available resources (recordings, transcripts)."""
    resources = []
    
    for call in state.calls:
        # Add transcript resource
        resources.append(
            Resource(
                uri=f"transcript://call_{call.id}",
                name=f"Call {call.id} Transcript",
                mimeType="text/plain",
                description=f"Transcript of call to {call.phone} at {call.timestamp}",
            )
        )
        
        # Add recording resource if available
        if call.recording_path and call.recording_path.exists():
            resources.append(
                Resource(
                    uri=f"recording://call_{call.id}",
                    name=f"Call {call.id} Recording",
                    mimeType="audio/wav",
                    description=f"Audio recording of call to {call.phone}",
                )
            )
    
    return resources


@app.read_resource()
async def read_resource(uri: str) -> str:
    """Read a resource by URI."""
    if uri.startswith("transcript://call_"):
        call_id = int(uri.split("_")[1])
        call = state.get_call(call_id)
        if call:
            return call.transcript or "[No transcript available]"
    
    elif uri.startswith("recording://call_"):
        call_id = int(uri.split("_")[1])
        call = state.get_call(call_id)
        if call and call.recording_path:
            # For now, return path. In future, could return base64 audio
            return f"Recording path: {call.recording_path}"
    
    raise ValueError(f"Resource not found: {uri}")


@app.list_prompts()
async def list_prompts() -> list[Prompt]:
    """List available prompt templates."""
    return [
        Prompt(
            name="test_call",
            description="Template for making a test SIP call to verify connectivity",
            arguments=[
                {"name": "phone", "description": "Phone number to call", "required": True},
            ],
        ),
        Prompt(
            name="agent_handoff",
            description="Template for agent-to-agent communication handoff",
            arguments=[
                {"name": "phone", "description": "Agent phone number", "required": True},
                {"name": "task", "description": "Task to hand off", "required": True},
                {"name": "context", "description": "Context about the task", "required": False},
            ],
        ),
    ]


@app.get_prompt()
async def get_prompt(name: str, arguments: dict) -> GetPromptResult:
    """Get a prompt template."""
    
    if name == "test_call":
        phone = arguments["phone"]
        return GetPromptResult(
            description="Test call template",
            messages=[
                PromptMessage(
                    role="user",
                    content=TextContent(
                        type="text",
                        text=f"Make a test call to {phone} with the message: 'Hello, this is a test call from iSIP MCP server. Please acknowledge if you can hear this message.'"
                    ),
                ),
            ],
        )
    
    elif name == "agent_handoff":
        phone = arguments["phone"]
        task = arguments["task"]
        context = arguments.get("context", "")
        
        message = (
            f"Hello, this is an automated agent handoff. "
            f"I'm passing you the following task: {task}. "
        )
        if context:
            message += f"Context: {context}. "
        message += "Please acknowledge and proceed with the task."
        
        return GetPromptResult(
            description="Agent handoff template",
            messages=[
                PromptMessage(
                    role="user",
                    content=TextContent(
                        type="text",
                        text=f"Call {phone} and perform this agent handoff: {message}"
                    ),
                ),
            ],
        )
    
    raise ValueError(f"Unknown prompt: {name}")


def main():
    """Run the MCP server."""
    asyncio.run(stdio_server(app))


if __name__ == "__main__":
    main()

