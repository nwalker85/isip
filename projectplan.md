# iSIP Project Plan

## Objective
Deliver a polished mac-native SIP automation toolkit so individual engineers can script calls, replay prompts, and inspect responses without spinning up cloud infrastructure.

## Milestones

1. **SDK Stabilization**
   - [ ] Publish to internal PyPI / artifact registry.
   - [ ] Add unit tests (mocking `pjsua`) plus integration harness that can run against a lab SIP server.
   - [ ] Provide typed stubs + mypy coverage for `siptester`.

2. **CLI Enhancements**
   - [ ] Config file support (`~/.isip/config.yaml`) for storing SIP credentials + trunk defaults.
   - [ ] Richer output (JSON summaries, waveform previews, optional desktop notifications).
   - [ ] Parallel execution of suite scenarios with per-test retries.

3. **Scenario Catalog**
   - [ ] Reuse the shared `tests/*.json` definitions (symlink or shared repo) so mac + cloud paths stay aligned.
   - [ ] Add a `siptester fetch` command that downloads curated scenarios from S3/Git.

4. **Developer Experience**
   - [ ] Provide `make dev` shortcut to set up virtualenvs, install pjproject, and run lint/test.
   - [ ] Offer VS Code tasks / launch configs for rapid iteration.
   - [ ] Document troubleshooting (microphone permissions, SIP firewall rules, NAT tips).

5. **Future Ideas**
   - Cross-platform support (Linux/Windows) using the same SDK.
   - Optional WebRTC transport (via PJSIP add-ons) to test WebRTC gateways.
   - Integration with ResoN8 so local runs can enqueue cloud bursts when needed.

Owners: Developer Productivity & SIP Platform Engineering.

