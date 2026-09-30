# Bounded Chat routing conversations

`shorthand-freshness.json` contains ten independent offline cases for Issue #2's approved instruction bugfix, not executable requests or a new router subsystem. The fixtures store conversation turns, verified context, per-case authorization and observable acceptance criteria. A numeric default in the shared context is not fresh-floor authorization; check each case's context. Historical identifiers in case g are replay-only evidence: never submit, retry or operate on them from a fixture.

## Blind instruction-consumer test

The controller owns consumer dispatch and independent review; the implementation worker must not run agents or claim GREEN from reading its own prose.

1. Pin the instruction candidate commit and read that commit's full `chatgpt-instructions.md` and `docs/contracts/chat-ci.md` together. No remote writes, network requests or actual tool execution in the offline probe.
2. Run a fresh blind consumer with **identical inputs to the baseline**: `.superpowers/sdd/2026-09-30-refresh-reconciliation/routing-probe-inputs.json` (`today`, `verified_source`, `default_parameters`, each `context` and `last_user_message`). `probe_id` maps a–j to this fixture. Do not send this README, `expected`, descriptive case IDs, assessment, worker report, authorization annotations or baseline observations to the consumer. They are evaluator-only; the unchanged input context already supplies the relevant authorization. The stored `turns` are bounded conversational renderings of those inputs, not extra evidence to add to the paired baseline/after probe.
3. Ask for the first user-visible response, chosen operation/read-only action and ordered proposed tool calls, without performing any calls. Keep cases independent so prior answers cannot supply missing authorization. Record verbatim output and the consumer/candidate identifiers.
4. After answers are sealed, read every observation against `expected.observable` and `expected.prohibited`; do not score by keyword presence alone. A correct recompute route still fails if the actual path, source date or no-new-model consequence is absent from the visible message **before both** proposed `create_branch` and `create_file`. An execution update is not another confirmation gate. For refresh, ensure acquisition disclosure and no `source_snapshot`; for missing-floor/conflict/pending/lookup/conclusion cases, check zero writes and the actual action, not just prose labels.
5. Preserve controls that already passed baseline. Any failures require a bounded revision and fresh identical-input probe; a fixture file, self-review or pipeline unittest cannot prove Chat follows the guidance.

## Evidence boundaries

- Historical actual RED: target Chat on 2026-09-30, short「開始」submitted recompute of9/26 without pre-write freshness disclosure; request `7f3d85a2-6e34-4bd4-9d91-4d6d11c7a4b8`, run `36665990363-1`, publication `171c1b797c8db6a9606ed3a9f42acce8df3c9cbc`.
- Recorded offline baseline: consumer `ses_f0f032daaffeLAE1Jva8CBJ2iA`; a/d/i chose recompute correctly but omitted visible actual source path and explicit snapshot-after-new-model consequence. b/e, c/f, g/h and j already passed their observed routing/date controls. Original observations and assessment live in the same scratch directory as the probe inputs.
- After-edit offline GREEN is **pending controller consumer probe**, not established by these fixtures or the full suite. Consumer observations are local instruction-use evidence, not target Chat end-to-end acceptance.
- Local commit, posted main, cloud refresh/recompute and artifact verification, target Chat routing/readback, and Project settings installation are distinct evidence. Bootstrap is unchanged; no settings re-paste is needed for this local instruction change, and installation remains independently unconfirmed. Final-review-conditioned delivery authorization is not evidence that publication has occurred.

Run `python3 -m unittest discover -s tests` once for unchanged schema/pipeline regression evidence. No keyword unittest is added: the behavioral gate above tests use of the instructions. Request v1, result v2/historical v1, three fixed commits, floor/reason, provenance, no-Claude and failure/no-stale-fallback rules remain authoritative in the contract.
