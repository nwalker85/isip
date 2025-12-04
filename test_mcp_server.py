#!/usr/bin/env python3
"""
Test MCP Server End-to-End

This simulates what an MCP client (like Claude Desktop) would do:
1. List available tools
2. Call make_call tool
3. List recordings
4. Get transcript
5. Test resources
"""

import asyncio
import sys
from pathlib import Path

# Add to path
sys.path.insert(0, str(Path(__file__).parent / "mcp-server-isip" / "src"))

from mcp_server_isip.server import app, state, list_tools, call_tool


async def test_mcp_server():
    """Test the MCP server end-to-end."""
    
    print("=" * 70)
    print("  MCP SERVER END-TO-END TEST")
    print("=" * 70)
    print()
    
    # Test 1: List tools
    print("1️⃣  Testing: list_tools()")
    print("-" * 70)
    tools = await list_tools()
    print(f"✓ Found {len(tools)} tools:")
    for tool in tools:
        print(f"  • {tool.name:20} - {tool.description[:50]}...")
    print()
    
    # Test 2: Make a call using quick_call
    print("2️⃣  Testing: quick_call tool")
    print("-" * 70)
    print("Making a test call to +19999999999...")
    print()
    
    try:
        result = await call_tool(
            name="quick_call",
            arguments={
                "phone": "+19999999999",
                "prompt": "Hello! This is an MCP server test call. Testing agent-to-agent communication.",
            }
        )
        
        print("Call Result:")
        for content in result:
            print(content.text)
        print()
        
    except Exception as e:
        print(f"✗ Call failed: {e}")
        import traceback
        traceback.print_exc()
        print()
    
    # Test 3: List recordings
    print("3️⃣  Testing: list_recordings tool")
    print("-" * 70)
    
    try:
        result = await call_tool(
            name="list_recordings",
            arguments={"limit": 10}
        )
        
        print("Recordings:")
        for content in result:
            print(content.text)
        print()
        
    except Exception as e:
        print(f"✗ List recordings failed: {e}")
        print()
    
    # Test 4: Get transcript (if we have calls)
    if state.calls:
        print("4️⃣  Testing: get_transcript tool")
        print("-" * 70)
        
        try:
            call_id = state.calls[0].id
            result = await call_tool(
                name="get_transcript",
                arguments={"call_id": call_id}
            )
            
            print("Transcript:")
            for content in result:
                print(content.text)
            print()
            
        except Exception as e:
            print(f"✗ Get transcript failed: {e}")
            print()
    
    # Test 5: Check state
    print("5️⃣  Testing: Server state")
    print("-" * 70)
    print(f"Total calls made: {len(state.calls)}")
    print(f"Output directory: {state.output_dir}")
    print(f"Output dir exists: {state.output_dir.exists()}")
    
    if state.calls:
        print(f"\nCall History:")
        for call in state.calls:
            status = "✓" if call.established else "✗"
            print(f"  {status} Call #{call.id} to {call.phone}")
            print(f"     Duration: {call.duration:.2f}s")
            print(f"     Transcript: {(call.transcript or '[None]')[:60]}...")
    print()
    
    # Summary
    print("=" * 70)
    print("  TEST SUMMARY")
    print("=" * 70)
    print(f"  ✓ Tools listed: {len(tools)}")
    print(f"  ✓ Calls made: {len(state.calls)}")
    print(f"  ✓ Recordings: {len([c for c in state.calls if c.recording_path])}")
    print(f"  ✓ Transcripts: {len([c for c in state.calls if c.transcript])}")
    print()
    
    if state.calls and state.calls[0].established:
        print("🎉 MCP SERVER IS FULLY OPERATIONAL!")
        print()
        print("Next steps:")
        print("  1. Configure Claude Desktop (see mcp-server-isip/QUICKSTART.md)")
        print("  2. Restart Claude Desktop")
        print("  3. Try: 'Make a call to +19999999999 and say hello'")
    else:
        print("⚠️  MCP server works but call may have failed")
        print("    Check your SIP credentials in .env")
    
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(test_mcp_server())

