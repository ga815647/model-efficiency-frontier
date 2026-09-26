# Task 2 delivery — shared scenario result and offline HTML

- `bridge.result.calculate_snapshot(csv_path, parameters, provenance) -> (calculation, markdown)`; provenance requires `benchmark`, `benchmark_version`, `version_status`, `cost_basis`, `source_dates`, `source_locator`, `caveats` (two locator forms below). It validates group/version/basis, paid data, cost grades, source dates and URLs, and performs one `compute_groups` call. `ladder_extra.select_picks(final)` is the sole pick implementation for Markdown and JSON. Renderer title is optional; CLI default is unchanged.
- `bridge.html_report.render_html(calculation) -> str` consumes that exact payload. Fixed inline CSS, no remote assets or JS, narrow-layout cards/statuses, horizontally scrollable table, escaped text, full Grok/Contributor status sections and source caveats. The caller writes the returned string to `report.html` in later tasks.
- `make_envelope(request, execution, *, calculation, errors)` flattens success fields and correlates request/run/attempt; `validate_envelope(envelope)` rejects failure with stale picks/ladder and incomplete success. Execution fields: `request_commit_sha`, `run_id`, `run_attempt`, `run_url`; `created_at` comes from request.

## Red / green evidence

- Red: `python3 -m unittest discover -s tests -p 'test_bridge_result.py' -v` → `ModuleNotFoundError: No module named 'bridge.result'`, 1 import error.
- Initial green bridge tests: `python3 -m unittest discover -s tests -p 'test_bridge_*.py' -v` → 21 tests, OK (after correcting HTML template syntax).
- Full suite initially caught wrong new test expectation for midpoint selection (`Grok Middle`, not `Other Cheap`); corrected test to reflect original `len(by_score)//2` behavior.
- Final: `python3 -m unittest discover -s tests -v` → 70 tests, OK. Snapshot parity: 155 statuses (16 final / 4 cut / 135 excluded), 16 final rungs; 9 Grok and 2 Contributor; exact three pick identities and scores asserted.

## Caveats / integration

- `source_locator` is supplied by runner as a pinned Git `{commit,path}` for recompute or a checked `{kind,path,sha256}` for a newly acquired refresh snapshot; it is intentionally not inferred from the CSV version. The test's placeholder commit is only a fixture.
- HTML is self-contained output, not automatically published or deployed here; future runner/publisher must save it alongside JSON/Markdown. No claim of Chat attachment or visual browser inspection in this task.
- Failure envelopes intentionally omit picks, ladder, and candidate statuses; refreshing with no pinned source may have `source_snapshot: null` and `source_dates: []`.

## Review fix round 1 (controller ruling)

- Two explicit source locators: recompute `{commit:40-hex,path:runs/.../candidates.csv|results/<uuid>/<run>-<attempt>/snapshot/candidates.csv}`; refresh before publication `{kind:"acquired",path:"snapshot/candidates.csv",sha256:64-hex}`. `calculate_snapshot` verifies acquired bytes against the digest, checks source dates, version status (`explicit` / `inferred`) and caveats (required for inferred version or B cost). The runner must verify pinned Git bytes at the exact commit; this module checks their locator syntax, not Git ancestry, remote authenticity or response metadata.
- Success envelope requires typed correlation, dated provenance, positive candidate_count and exactly that many typed statuses with unique identities, complete final ladder in Score-desc order, and picks equal to the existing shared selector over projected final rows. An empty *final ladder* with nonempty all-excluded candidates and null picks is valid; all-Claude final likewise. Failure envelopes require structured nonempty errors and omit every success-derived field; they do not revalidate malformed request parameters and may have null request identity for parse failures. Task 6 still owns best-available correlation when request parsing fails.
- Family flags `is_grok` / `is_contributor` are projected from the same `ladder_extra` predicates used by adjustment/Markdown, not derived anew from HTML strings. HTML uses the payload's actual factor parameters, renders acquired SHA-256 appropriately, and marks status sections by family for parity checks. Archived provenance caveat wording is source context, not rewritten as a fresh measurement claim.
- Fix-round red: `python3 -m unittest discover -s tests -p 'test_bridge_*.py' -q` → 26 tests, 12 failures / 2 errors (missing locator/hash/flags/structural validation and fixed-factor HTML). After fixes scoped → 26 tests, OK. New tests cover malicious/hollow envelopes, malformed error objects, varied factors and exact 3-card/ladder/family contents, acquired hash, dates/locator/version semantics, all-filtered and all-Claude successes.
- Final verification: `python3 -m unittest discover -s tests -p 'test_bridge_*.py' -q` → 26 tests, OK; `python3 -m unittest discover -s tests -v` → 75 tests, OK.

## Review fix round 2

- Successful envelope operation and locator now agree: `refresh` requires acquired `{kind,path,sha256}`; `recompute` requires pinned `{commit,path}`. This check belongs to the success envelope boundary because `calculate_snapshot` has no operation argument. Failure envelopes remain able to report malformed requests.
- Pinned locator path type is checked before either regex is called, raising `ResultError(ValueError)` for null/numeric paths. Added tests for both operation/locator mismatches, malformed path types, and all three Markdown pick lines (labels and identities).
- Red: `python3 -m unittest discover -s tests -p test_bridge_result.py -v` → 9 tests, 2 failures / 2 errors. Green: same command → 9 tests, OK. No full-suite repeat requested for this scoped validation correction.
