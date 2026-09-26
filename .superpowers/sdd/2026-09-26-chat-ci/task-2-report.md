# Task 2 delivery — shared scenario result and offline HTML

- `bridge.result.calculate_snapshot(csv_path, parameters, provenance) -> (calculation, markdown)`; provenance requires `benchmark`, `benchmark_version`, `version_status`, `cost_basis`, `source_dates`, `source_locator={commit,path}`, `caveats`. It validates group/version/basis, paid data, cost grades, source dates and URLs, and performs one `compute_groups` call. `ladder_extra.select_picks(final)` is the sole pick implementation for Markdown and JSON. Renderer title is optional; CLI default is unchanged.
- `bridge.html_report.render_html(calculation) -> str` consumes that exact payload. Fixed inline CSS, no remote assets or JS, narrow-layout cards/statuses, horizontally scrollable table, escaped text, full Grok/Contributor status sections and source caveats. The caller writes the returned string to `report.html` in later tasks.
- `make_envelope(request, execution, *, calculation, errors)` flattens success fields and correlates request/run/attempt; `validate_envelope(envelope)` rejects failure with stale picks/ladder and incomplete success. Execution fields: `request_commit_sha`, `run_id`, `run_attempt`, `run_url`; `created_at` comes from request.

## Red / green evidence

- Red: `python3 -m unittest discover -s tests -p 'test_bridge_result.py' -v` → `ModuleNotFoundError: No module named 'bridge.result'`, 1 import error.
- Initial green bridge tests: `python3 -m unittest discover -s tests -p 'test_bridge_*.py' -v` → 21 tests, OK (after correcting HTML template syntax).
- Full suite initially caught wrong new test expectation for midpoint selection (`Grok Middle`, not `Other Cheap`); corrected test to reflect original `len(by_score)//2` behavior.
- Final: `python3 -m unittest discover -s tests -v` → 70 tests, OK. Snapshot parity: 155 statuses (16 final / 4 cut / 135 excluded), 16 final rungs; 9 Grok and 2 Contributor; exact three pick identities and scores asserted.

## Caveats / integration

- `source_locator` is supplied by runner as a pinned Git `{commit,path}`; it is intentionally not inferred from CSV. The test's placeholder commit is only a fixture.
- HTML is self-contained output, not automatically published or deployed here; future runner/publisher must save it alongside JSON/Markdown. No claim of Chat attachment or visual browser inspection in this task.
- Failure envelopes intentionally omit picks, ladder, and candidate statuses; refreshing with no pinned source may have `source_snapshot: null` and `source_dates: []`.
