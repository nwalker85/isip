# iSIP Deployment Guide

## Architecture Overview

iSIP is designed as a **developer-first local testing tool** with cloud deployment capabilities.

```
┌─────────────────────────────────────────────────────────────┐
│                    iSIP Architecture                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐         ┌──────────────┐                 │
│  │   Mac Local  │         │  Linux/Docker│                 │
│  │  Developer   │  ◄────► │   ResoN8     │                 │
│  │   Testing    │ Shared  │   Cloud      │                 │
│  │              │ Scenarios│   Testing    │                 │
│  └──────────────┘         └──────────────┘                 │
│         │                         │                          │
│         └─────────┬───────────────┘                         │
│                   ▼                                          │
│          ┌─────────────────┐                                │
│          │  SIP Gateway    │                                │
│          │  (LiveKit, etc) │                                │
│          └─────────────────┘                                │
│                   │                                          │
│                   ▼                                          │
│          ┌─────────────────┐                                │
│          │  AI Services    │                                │
│          │ OpenAI/Deepgram │                                │
│          └─────────────────┘                                │
└─────────────────────────────────────────────────────────────┘
```

## Deployment Options

### 1. **Mac Native** (Current Implementation)

**Best for:** Individual developers, rapid iteration, local debugging

**Pros:**
- ✅ No containers needed
- ✅ Fast iteration cycle
- ✅ Direct access to system audio
- ✅ Native tooling (Homebrew, Xcode)

**Cons:**
- ❌ Mac-only (requires macOS + Homebrew)
- ❌ Manual setup (pjproject compilation)
- ❌ Doesn't scale for CI/CD
- ❌ Can't run headless

**Setup:**
```bash
brew install pjproject ffmpeg
cd sdk/python
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e .
```

**When to use:** Daily development, testing on your laptop

---

### 2. **Docker/Linux** (Cross-Platform)

**Best for:** CI/CD, automated testing, Linux servers, Windows via WSL

**Pros:**
- ✅ Works on Linux/Mac/Windows (via Docker)
- ✅ Reproducible builds
- ✅ Can run headless/scheduled
- ✅ Easy CI/CD integration
- ✅ Scales horizontally

**Cons:**
- ❌ Slower iteration (rebuild on code changes)
- ❌ No native audio device (headless only)
- ❌ Larger resource footprint

**Setup:**
```bash
# Build image
docker build -t isip:latest .

# Run single test
docker run --rm --env-file .env isip:latest call \
  --gateway 2g0282esbg2.sip.livekit.cloud \
  --user "$SIP_USERNAME" \
  --password "$SIP_PASSWORD" \
  --phone +19999999999 \
  --prompt-text "Hello from Docker"

# Run test suite
docker-compose up isip-worker
```

**When to use:** CI/CD pipelines, scheduled tests, Linux deployment

---

### 3. **ResoN8 Cloud** (Mentioned in Docs)

**Best for:** Large-scale testing, parallel execution, cloud bursts

**Pros:**
- ✅ Massively parallel testing
- ✅ Shared infrastructure
- ✅ Centralized reporting
- ✅ No local setup needed

**Cons:**
- ❌ Requires cloud infrastructure
- ❌ Network latency to test
- ❌ Cost at scale

**Integration:**
```bash
# Push scenarios to cloud
siptester fetch --upload tests/my_suite.json

# Trigger cloud burst from local
siptester suite --cloud --parallel 100 tests/my_suite.json
```

**When to use:** Load testing, regression suites, production monitoring

---

## Platform Compatibility

### Does It Actually Work?

| Platform | Status | Notes |
|----------|--------|-------|
| **macOS** | ✅ Tested | Current implementation, uses Homebrew pjproject |
| **Linux** | ⚠️ Untested | Should work via Docker, needs validation |
| **Windows** | ⚠️ Untested | Possible via WSL2 + Docker, or native pjproject build |
| **Docker** | ⚠️ Prototype | Dockerfile provided, needs testing |

### PJSIP Cross-Platform Reality

PJSIP itself is **fully cross-platform**:
- ✅ Linux (ALSA/PulseAudio)
- ✅ macOS (CoreAudio)
- ✅ Windows (DirectSound/WASAPI)
- ✅ Headless (no audio device needed for call signaling)

The Mac limitation is **only due to the Homebrew setup**. The underlying tech works everywhere.

---

## Production Deployment Patterns

### Pattern 1: CI/CD Integration (GitHub Actions)

```yaml
# .github/workflows/sip-tests.yml
name: SIP Integration Tests

on:
  push:
    branches: [main]
  schedule:
    - cron: '0 */4 * * *'  # Every 4 hours

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Build iSIP Docker image
        run: docker build -t isip:test .
      
      - name: Run test suite
        env:
          SIP_USERNAME: ${{ secrets.SIP_USERNAME }}
          SIP_PASSWORD: ${{ secrets.SIP_PASSWORD }}
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          DEEPGRAM_API_KEY: ${{ secrets.DEEPGRAM_API_KEY }}
        run: |
          docker run --rm --env-file <(env | grep -E 'SIP_|OPENAI|DEEPGRAM') \
            isip:test suite --suite /app/tests/regression.json
      
      - name: Upload recordings
        uses: actions/upload-artifact@v3
        with:
          name: test-recordings
          path: sippy_output/
```

### Pattern 2: Kubernetes CronJob

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: isip-health-checks
spec:
  schedule: "*/15 * * * *"  # Every 15 minutes
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: isip
            image: your-registry/isip:latest
            envFrom:
            - secretRef:
                name: isip-credentials
            command:
            - siptester
            - suite
            - --suite
            - /app/tests/health_check.json
          restartPolicy: Never
```

### Pattern 3: AWS Lambda (for light testing)

```python
# Lambda function for scheduled SIP testing
import boto3
from siptester import quick_call

def lambda_handler(event, context):
    """Run SIP health check on schedule"""
    result = quick_call(
        phone="+19999999999",
        prompt="Health check call",
        username=os.environ['SIP_USERNAME'],
        password=os.environ['SIP_PASSWORD'],
    )
    
    if not result.established:
        # Alert SNS topic
        sns = boto3.client('sns')
        sns.publish(
            TopicArn=os.environ['ALERT_TOPIC_ARN'],
            Subject='SIP Health Check Failed',
            Message=f'Call failed: {result.error}'
        )
    
    return {'statusCode': 200, 'body': result.transcript}
```

---

## Recommended Deployment Strategy

### Phase 1: Current State (Mac-Native)
- ✅ **Local development**: Mac with Homebrew
- ✅ **Quick iteration**: Individual engineers testing locally
- ✅ **Shared scenarios**: JSON files in Git

### Phase 2: Docker (Coming Soon)
- 🔄 **CI/CD**: Docker containers for automated tests
- 🔄 **Linux servers**: Headless testing on Ubuntu
- 🔄 **Scheduled monitoring**: Cron jobs in Docker

### Phase 3: ResoN8 Integration (Future)
- 📅 **Cloud bursts**: Trigger parallel testing from local
- 📅 **Load testing**: 100s of concurrent calls
- 📅 **Centralized reporting**: Dashboard + analytics

---

## FAQ

### Q: Why not just use Docker everywhere?

**A:** Developer experience. Rebuilding containers for every code change is slow. Mac-native is faster for active development. Docker is better for CI/CD and deployment.

### Q: Does the Docker version actually work?

**A:** The Dockerfile is provided but **untested**. PJSIP compiles on Linux, so it *should* work, but needs validation. This is prototype stage.

### Q: Can I run this on Windows?

**A:** Not natively yet. Options:
1. WSL2 + Docker (recommended)
2. Build pjproject with MinGW/MSVC (complex)
3. Wait for cross-platform support in project plan

### Q: Is this production-ready?

**A:** No. From the project plan:
- No unit tests yet
- No CI/CD pipeline
- No published packages
- Manual setup required

This is a **developer productivity tool** in early stages.

### Q: How does this compare to cloud SIP testing services?

**A:** 
- **iSIP**: Local-first, fast iteration, full control
- **Cloud SaaS**: Managed infrastructure, scales better, costs money
- **Hybrid**: Use iSIP locally, ResoN8 in cloud (planned)

### Q: Why PJSIP instead of Twilio/LiveKit SDKs?

**A:** PJSIP gives you **full SIP protocol control**. Twilio/LiveKit are higher-level and don't expose raw SIP signaling, which is needed for testing SIP infrastructure (not just making calls).

---

## Next Steps for Production

To make this truly production-ready:

1. ✅ **Test Docker build** on Linux
2. ✅ **Add CI/CD pipeline** (GitHub Actions)
3. ✅ **Write unit tests** (mock pjsua)
4. ✅ **Publish to PyPI** for easy `pip install`
5. ✅ **Document cross-platform builds** (Windows, ARM)
6. ✅ **Add monitoring/observability** (Prometheus metrics)
7. ✅ **Implement ResoN8 integration** (cloud burst API)

---

## Conclusion

**Does the stack make sense?** Yes, for local developer testing.  
**Does it work?** Yes on Mac, Docker untested but should work.  
**Mac-only?** Currently, but PJSIP is cross-platform.  
**Docker deployment?** Provided, needs validation.  

The architecture is sound. The current limitation is **maturity**, not design.

