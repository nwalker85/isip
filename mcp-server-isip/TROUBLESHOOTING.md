# MCP Server Troubleshooting

## Common Issues

### Error: `spawn mcp-server-isip ENOENT`

**Problem:** Claude Desktop can't find the `mcp-server-isip` command.

**Cause:** The command is installed in a virtual environment and not in Claude's PATH.

**Solution:** Use the full path to the command in your config:

```json
{
  "mcpServers": {
    "isip": {
      "command": "/Users/nwalker/Development/Quant/isip/sdk/python/.venv/bin/mcp-server-isip",
      "cwd": "/Users/nwalker/Development/Quant/isip"
    }
  }
}
```

**Alternative solution** - Use Python directly:

```json
{
  "mcpServers": {
    "isip": {
      "command": "/Users/nwalker/Development/Quant/isip/sdk/python/.venv/bin/python",
      "args": ["-m", "mcp_server_isip.server"],
      "cwd": "/Users/nwalker/Development/Quant/isip"
    }
  }
}
```

---

### Error: `ImportError: No module named 'siptester'`

**Problem:** The iSIP SDK is not accessible to the MCP server.

**Solution:** Make sure the SDK is installed:

```bash
cd /Users/nwalker/Development/Quant/isip/sdk/python
source .venv/bin/activate
pip install -e .
```

---

### Error: Environment variables not found

**Problem:** API keys or SIP credentials not available.

**Solution:** The MCP server automatically loads from `.env` in the project root. Make sure it exists:

```bash
cd /Users/nwalker/Development/Quant/isip
ls -la .env  # Should exist

# If not, copy from template:
cp .env.example .env
# Then edit .env with your actual credentials
```

**Alternative:** Explicitly set environment variables in Claude config:

```json
{
  "mcpServers": {
    "isip": {
      "command": "/Users/nwalker/Development/Quant/isip/sdk/python/.venv/bin/mcp-server-isip",
      "cwd": "/Users/nwalker/Development/Quant/isip",
      "env": {
        "OPENAI_API_KEY": "sk-...",
        "DEEPGRAM_API_KEY": "...",
        "SIP_USERNAME": "...",
        "SIP_PASSWORD": "...",
        "SIP_GATEWAY": "2g0282esbg2.sip.livekit.cloud"
      }
    }
  }
}
```

---

### MCP server starts but tools don't appear

**Problem:** Claude Desktop can't see the tools.

**Debugging:**

1. Check Claude Desktop logs:
   ```bash
   tail -f ~/Library/Logs/Claude/mcp*.log
   ```

2. Test the server manually:
   ```bash
   cd /Users/nwalker/Development/Quant/isip
   python test_mcp_server.py
   ```

3. Verify the server responds to stdio:
   ```bash
   echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' | \
     /Users/nwalker/Development/Quant/isip/sdk/python/.venv/bin/mcp-server-isip
   ```

---

### Calls fail but server is running

**Problem:** SIP connection or authentication issues.

**Check credentials:**

```bash
cd /Users/nwalker/Development/Quant/isip
source sdk/python/.venv/bin/activate
python test_e2e.py
```

If this fails, your SIP credentials or API keys are incorrect.

**Common causes:**
- Wrong SIP username/password
- Invalid API keys (OpenAI, Deepgram)
- Network/firewall blocking SIP traffic
- LiveKit gateway unreachable

---

### Permission denied errors

**Problem:** Can't execute the MCP server command.

**Solution:** Make sure it's executable:

```bash
chmod +x /Users/nwalker/Development/Quant/isip/sdk/python/.venv/bin/mcp-server-isip
```

---

### Claude Desktop doesn't restart properly

**Steps:**

1. **Quit Claude Desktop completely** (Cmd+Q)
2. **Kill any remaining processes:**
   ```bash
   killall Claude
   ```
3. **Wait 5 seconds**
4. **Restart Claude Desktop**
5. **Check for the 🔌 icon** in Claude - should show MCP server connected

---

## Verification Steps

### 1. Verify Installation

```bash
# Check command exists
ls -la /Users/nwalker/Development/Quant/isip/sdk/python/.venv/bin/mcp-server-isip

# Check it's executable
/Users/nwalker/Development/Quant/isip/sdk/python/.venv/bin/mcp-server-isip --help
```

### 2. Verify Configuration

```bash
# Check Claude config
cat ~/Library/Application\ Support/Claude/claude_desktop_config.json

# Verify JSON is valid
cat ~/Library/Application\ Support/Claude/claude_desktop_config.json | python -m json.tool
```

### 3. Test Server Directly

```bash
cd /Users/nwalker/Development/Quant/isip
python test_mcp_server.py
```

Should output:
```
🎉 MCP SERVER IS FULLY OPERATIONAL!
```

### 4. Check Logs

```bash
# Claude Desktop logs
tail -f ~/Library/Logs/Claude/mcp*.log

# Look for:
# - "Connected to MCP server: isip"
# - Tool registrations
# - Any error messages
```

---

## Getting Help

If you're still having issues:

1. **Run the full diagnostic:**
   ```bash
   cd /Users/nwalker/Development/Quant/isip
   python test_mcp_server.py > test_output.txt 2>&1
   ```

2. **Check all configs:**
   ```bash
   echo "=== Claude Config ==="
   cat ~/Library/Application\ Support/Claude/claude_desktop_config.json
   
   echo "=== .env file ==="
   grep -E "^[A-Z_]+=" .env | sed 's/=.*/=***/'
   
   echo "=== MCP Server Path ==="
   ls -la sdk/python/.venv/bin/mcp-server-isip
   ```

3. **Review documentation:**
   - [QUICKSTART.md](QUICKSTART.md)
   - [README.md](README.md)
   - [iSIP README](../README.md)

---

## Configuration Examples

### Minimal (recommended)

```json
{
  "mcpServers": {
    "isip": {
      "command": "/Users/nwalker/Development/Quant/isip/sdk/python/.venv/bin/mcp-server-isip",
      "cwd": "/Users/nwalker/Development/Quant/isip"
    }
  }
}
```

### With explicit environment

```json
{
  "mcpServers": {
    "isip": {
      "command": "/Users/nwalker/Development/Quant/isip/sdk/python/.venv/bin/mcp-server-isip",
      "cwd": "/Users/nwalker/Development/Quant/isip",
      "env": {
        "OPENAI_API_KEY": "sk-...",
        "DEEPGRAM_API_KEY": "...",
        "SIP_USERNAME": "nate@ravenhelm.co",
        "SIP_PASSWORD": "...",
        "SIP_GATEWAY": "2g0282esbg2.sip.livekit.cloud"
      }
    }
  }
}
```

### Using Python directly

```json
{
  "mcpServers": {
    "isip": {
      "command": "/Users/nwalker/Development/Quant/isip/sdk/python/.venv/bin/python",
      "args": ["-m", "mcp_server_isip.server"],
      "cwd": "/Users/nwalker/Development/Quant/isip"
    }
  }
}
```

---

## Status: All Known Issues Resolved

✅ PATH issues → Use full path to command  
✅ Import errors → SDK installed in same venv  
✅ Environment variables → Auto-loaded from .env  
✅ Tested end-to-end → All tests passing  

The MCP server is fully operational! 🚀

