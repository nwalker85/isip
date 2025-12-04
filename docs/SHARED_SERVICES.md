# Shared Services Integration

## Overview

iSIP integrates with Ravenhelm's shared services infrastructure managed by Hliðskjálf. This document tracks API keys, credentials, and service dependencies.

## API Key Sources

All API keys are sourced from the Hliðskjálf control plane:

**Primary Source:** `/Users/nwalker/Development/hlidskjalf/.env`

| Service | Key Variable | Rotation Schedule | Runbook |
|---------|--------------|-------------------|---------|
| OpenAI | `OPENAI_API_KEY` | 90 days | [RUNBOOK-010](https://gitlab.ravenhelm.test/hlidskjalf/-/blob/main/docs/runbooks/RUNBOOK-010-secret-rotation.md) |
| Deepgram | `DEEPGRAM_API_KEY` | 90 days | [RUNBOOK-010](https://gitlab.ravenhelm.test/hlidskjalf/-/blob/main/docs/runbooks/RUNBOOK-010-secret-rotation.md) |
| ElevenLabs | `ELEVENLABS_API_KEY` | 90 days | [RUNBOOK-010](https://gitlab.ravenhelm.test/hlidskjalf/-/blob/main/docs/runbooks/RUNBOOK-010-secret-rotation.md) |
| Anthropic | `ANTHROPIC_API_KEY` | 90 days | [RUNBOOK-010](https://gitlab.ravenhelm.test/hlidskjalf/-/blob/main/docs/runbooks/RUNBOOK-010-secret-rotation.md) |

## LiveKit SIP Gateway

**Source:** [RUNBOOK-027-sip-voice-platform.md](https://gitlab.ravenhelm.test/hlidskjalf/-/blob/main/docs/runbooks/RUNBOOK-027-sip-voice-platform.md)

| Credential | Value | Notes |
|------------|-------|-------|
| SIP Gateway | `2g0282esbg2.sip.livekit.cloud` | LiveKit Cloud deployment |
| SIP Username | `nate@ravenhelm.co` | Email-based auth |
| SIP Password | `F0rTh3M0$tP@rt` | Rotate per RUNBOOK-010 |
| LiveKit URL | `wss://ravenhelm-gt6v1eh8.livekit.cloud` | WebSocket endpoint |
| LiveKit Project | `p_2g0282esbg2` | Project ID |

## Synchronization Procedure

When API keys are rotated in Hliðskjálf, update iSIP:

```bash
# 1. Navigate to iSIP project
cd /Users/nwalker/Development/Quant/isip

# 2. Extract updated keys from Hliðskjálf
cd /Users/nwalker/Development/hlidskjalf
grep -E "^(OPENAI|DEEPGRAM|ELEVENLABS|ANTHROPIC)_API_KEY=" .env > /tmp/api_keys.txt

# 3. Update iSIP .env (manual merge to preserve SIP credentials)
cd /Users/nwalker/Development/Quant/isip
# Edit .env with new keys from /tmp/api_keys.txt

# 4. Verify
source sdk/python/.venv/bin/activate
python test_e2e.py
```

## Architecture Alignment

Per Enterprise Multi-Platform Architecture Scaffold v1.3.0:

- **Secrets Management:** API keys stored in `.env` files (local dev). Production should use AWS Secrets Manager or HashiCorp Vault.
- **Service Identity:** iSIP operates as a developer tool, not a platform service. No SPIRE identity required.
- **Network Isolation:** iSIP connects to external SaaS APIs (OpenAI, Deepgram, LiveKit). No internal Ravenhelm network access needed.
- **Observability:** Logs to stdout. No Grafana/Alloy integration required for local dev tool.

## Related Documentation

### Hliðskjálf Wiki
- [Overview & Governance](file:///Users/nwalker/Development/hlidskjalf/docs/wiki/Overview.md)
- [Runbook Catalog](file:///Users/nwalker/Development/hlidskjalf/docs/wiki/Runbook_Catalog.md)
- [RUNBOOK-010: Secret Rotation](file:///Users/nwalker/Development/hlidskjalf/docs/runbooks/RUNBOOK-010-secret-rotation.md)
- [RUNBOOK-027: SIP Voice Platform](file:///Users/nwalker/Development/hlidskjalf/docs/runbooks/RUNBOOK-027-sip-voice-platform.md)

### iSIP Documentation
- [README.md](../README.md) - Main documentation
- [DEPLOYMENT.md](../DEPLOYMENT.md) - Deployment guide
- [EXAMPLES.md](../EXAMPLES.md) - Usage examples

## Security Notes

1. **Never commit `.env` to git** - Already in `.gitignore`
2. **Rotate keys every 90 days** - Follow RUNBOOK-010 procedures
3. **Use `.env.example` for templates** - Safe to commit, no real keys
4. **Audit key usage** - Track in Hliðskjálf's audit logs (future)

## Future Enhancements

- [ ] Integrate with Hliðskjálf's AWS Secrets Manager (LocalStack)
- [ ] Add automated key sync script
- [ ] Implement key rotation notifications
- [ ] Add SPIRE identity for production deployment
- [ ] Integrate with Grafana observability stack

## Revision History

| Date | Author | Changes |
|------|--------|---------|
| 2024-12-04 | Nathan Walker | Initial documentation, aligned with Hliðskjálf shared services |

