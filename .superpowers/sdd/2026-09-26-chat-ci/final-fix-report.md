# Whole-branch final fixwave (local only)

Base: `c0b5990`. Code/test commit: `f1fa1c8` (`Fix publication fetch races and contributor loss diagnostics`). No cloud/production remote was contacted or changed; publisher tests use a local bare Git remote.

## Findings and disposition

- **Important — publisher race:** `_tip` could observe an old `ls-remote` tip but fetch a newer one. Its `remote_tip_changed_during_fetch` exception bypassed the outer retry loop. Now only that specific race spends one of the existing three attempts; unrelated Git errors still fail, and pushes remain fast-forward/non-force. Local-bare test races a second publisher specifically before fetch and verifies both immutable results survive; perpetual mismatch exhausts exactly three attempts.
- **Important — Contributor regression:** losing a previous Contributor effort failed generically without saved evidence. Now `missing_candidates.json` records each missing Contributor identity/effort, previous-inventory presence, observed same-family current leaderboard entries, release-page slugs and current Contributor efforts. Model/index lookup and exact ID/effort disambiguation are explicitly **pending manual review**, not asserted absent. Refresh fails before writing candidates; the existing publisher evidence allowlist already permits this JSON, so no publisher schema change was needed.
- **Minor — boolean floor:** regression proves `min_score=True` is rejected by existing request numeric validation; implementation unchanged.
- **Minor — mobile raw notes:** Grok/Contributor cards keep identity, grade, score, original cost, factor, adjusted CP, status, reason, source URL/date visible. Only verbose original notes move into native `<details>/<summary>`; all text stays escaped, local and JS-free, and is read from the same payload.

## Red / green evidence

- Red: `PYTHONPATH=tests:. python3 -m unittest tests.test_bridge_publish.PublishTests.test_retries_remote_advance_between_ls_remote_and_fetch tests.test_bridge_publish.PublishTests.test_fetch_race_uses_same_three_attempt_budget tests.test_refresh_sources.RefreshSourcesTest.test_previous_contributor_effort_loss_records_three_pass_pending_evidence tests.test_bridge_request.RequestTests.test_boolean_min_score_is_not_a_number tests.test_bridge_html.HTMLTests.test_verbose_status_notes_are_collapsed_but_essential_status_visible` → 5 run, 3 failures + 1 error (race test initially needed seeded remote; then verified against old implementation); min-score regression passed before code change.
- Green: same targeted command → **5 passed**. Stronger per-card HTML visibility assertion → **1 passed**.
- Full suite once after fixes: `python3 -m unittest discover -s tests -v` → **133 passed**, with existing missing-config warning in ladder test. `git diff --check` clean.

Changed implementation: `bridge/publish.py`, `scripts/refresh_snapshot.py`, `bridge/html_report.py`. Changed regressions: `tests/test_bridge_publish.py`, `tests/test_refresh_sources.py`, `tests/test_bridge_request.py`, `tests/test_bridge_html.py`. This report is the only additional committed file; frozen math, historical runs, and Notion were not touched.

Offline preview regenerated at `/tmp/opencode/chat-ci-preview/report.html` using `runs/2026-09-26-general-grok16/candidates.csv` and the approved snapshot provenance/parameters from `tests/test_bridge_result.py` (16 ladder rungs, 9 Grok statuses, 2 Contributor statuses). Ready for controller visual inspection; this fixwave does not claim a browser/device check or remote CI/Chat acceptance.
