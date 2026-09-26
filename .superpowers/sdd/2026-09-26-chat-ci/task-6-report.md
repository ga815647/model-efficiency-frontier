# Task 6 — audited push workflow

## Delivered

- `.github/workflows/chat-execution.yml` triggers only on `efficiency-run/**` pushes changing `bridge/requests/*.json`; ubuntu-24.04, Python 3.11, 20-minute timeout, `contents: write`, per-run non-cancelling concurrency. No results-push trigger, Pages deployment, or branch deletion.
- Official action commit pins, resolved via GitHub's `repos/actions/{repo}/git/ref/tags/{tag}` API: checkout v4.2.2 `11bd71901bbe5b1630ceea73d27597364c9af683`, setup-python v5.6.0 `a26af69be951a213d495a4c3e4e4022e16d87065`, upload-artifact v4.6.2 `ea165f8d65b6e75b540449e92b4886f43607fa02`. Checkout fetches full history with persisted credentials disabled.
- Current `main` bootstrap validates the immutable authenticated `github.event.after`, not the moving request branch tip. It checks exactly one parent, parent ancestry on current main, canonical event ref UUID, sole added matching JSON Git-tree blob, strict decoded request and its `product_sha == parent`. It hands the verified parent SHA and Git blob bytes to a separate product checkout. JSON never chooses a checkout ref or script path. Product checkout sees full history and materializes `refs/heads/results` from fetched `origin/results` when present for recompute and previous-refresh inventory.
- Invalid transport writes a failed envelope from the bootstrap, using only event SHA/ref identity; no product execution. Runner failure emits its own envelope; if it crashes before doing so, bootstrap emits `runner_interrupted`. Publisher (with the only explicit `GITHUB_TOKEN`) appends the result, including failure, and writes the publication commit SHA plus request/run/attempt to the job summary. The final assertion keeps execution failures red even if publication succeeds; publication failures themselves remain red. The AA secret is scoped to the refresh step; public refresh remains available when unset. Successful HTML is downloadable as `report-<request UUID>-<run ID>-<attempt>` via pinned upload-artifact, not hosted as a website.

## CLI contracts

From trusted bootstrap checkout:

```
python3 -m bridge.runner verify-transport --repository . --event-sha <event.after> --ref-name <github.ref_name> --run-id <id> --run-attempt <positive-int> --output ../output --product-sha-file ../handoff/product.sha --github-output "$GITHUB_OUTPUT"
python3 -m bridge.runner diagnostic-failure --event-sha <event.after> --ref-name <github.ref_name> --product-sha-file ../handoff/product.sha --run-id <id> --run-attempt <positive-int> --output ../output
python3 -m bridge.publish --output ../output --remote https://github.com/<owner>/<repo>.git
python3 -m bridge.runner assert-success --output ../output
```

`verify-transport` returns 0 and writes the pinned SHA/request JSON to `handoff/` plus validated GitHub step outputs (`product_sha`, `operation`, `request_id`), or returns 1 and writes `output/result.json` with status `failed`. `diagnostic-failure` is for the previously verified transport whose runner produced no result; it writes a correlated failed result. `assert-success` returns 0 only for a valid success envelope, otherwise 1. Product runner's existing CLI is unchanged: `python3 -m bridge.runner --request ../handoff/request.json --event-sha ... --ref-name ... --run-id ... --run-attempt ... --output ../output`.

## Tested error cases

- Real temporary Git history: single-file request passes; code change rejected before product checkout; malformed request JSON publishes a failure correlated to event/ref, never the JSON's claimed ID; parent outside current main rejected; a later branch-tip commit cannot replace event SHA.
- Interrupted runner diagnostic uses the verified handoff identity. A failed result remains nonzero with `assert-success` after successful local bare-Git publication. Full suite: `python3 -m unittest discover -s tests -v` (126 tests passed). No network Git writes or live Actions run in Task 6; remote acceptance belongs to Task 8.
