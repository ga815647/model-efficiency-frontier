#!/usr/bin/env python3
"""AA Data API v2 fetcher -> candidates.csv draft rows + version snapshot.

Endpoint: GET https://artificialanalysis.ai/api/v2/language/models/free
Auth: x-api-key header from env AA_API_KEY (never a CLI arg, never logged).
Pagination: page/page_size=200 until exhausted.
Stdlib only (urllib, json, csv, argparse).

Field map (per librarian brief, do not invent names):
  score = entry.evaluations.artificial_analysis_intelligence_index
  cost  = entry.artificial_analysis_intelligence_index_cost.cost_per_task.total_cost
  version = response envelope intelligence_index_version (recorded once)

Free tier is a cross-provider median: provider is always 'AA-median' and
notes state this; never claim a specific provider/plan split.
benchmark_version comes from the envelope ('v'+version); never merge
versions downstream (ban 10).
"""

import argparse
import csv
import datetime
import io
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

BASE_URL = "https://artificialanalysis.ai/api/v2/language/models/free"
PAGE_SIZE = 200

COLUMNS = [
    "identity", "model", "effort", "provider", "pricing_plan",
    "model_version", "benchmark", "benchmark_version", "score",
    "cost_per_task", "cost_basis", "privacy", "is_free", "evidence_url",
    "checked_date", "quota", "notes", "ttft_s", "time_per_task_s",
]

# --dry-run sample: same envelope shape, 2 models, one null-cost (skipped).
SAMPLE_ENVELOPE = {
    "intelligence_index_version": "4.3",
    "data": [
        {
            "name": "Sample Model Alpha (high)",
            "slug": "sample-model-alpha-high",
            "evaluations": {"artificial_analysis_intelligence_index": 45.0},
            "artificial_analysis_intelligence_index_cost": {
                "cost_per_task": {"total_cost": 0.55}
            },
            "pricing": {"price_1m_input_tokens": 1.0,
                        "price_1m_output_tokens": 3.0},
        },
        {
            "name": "Sample Model Beta (low)",
            "slug": "sample-model-beta-low",
            "evaluations": {"artificial_analysis_intelligence_index": 38.0},
            "artificial_analysis_intelligence_index_cost": {
                "cost_per_task": {"total_cost": None}
            },
            "pricing": {"price_1m_input_tokens": 0.5,
                        "price_1m_output_tokens": 1.5},
        },
    ],
}

EFFORT_RE = re.compile(r"^(?P<model>.*?)\s*\((?P<effort>[^()]*)\)\s*$")


def split_name_effort(name):
    """Split trailing parenthetical as effort; warn if absent."""
    m = EFFORT_RE.match(name or "")
    if m:
        return m.group("model").strip(), m.group("effort").strip()
    print(f"warn: no effort parenthetical in name {name!r}; "
          f"using name as-is", file=sys.stderr)
    return (name or "").strip(), (name or "").strip()


def parse_envelope(envelope, today):
    """Parse one envelope -> (rows, version, skipped_null_count)."""
    raw_version = envelope.get("intelligence_index_version", "")
    version = f"v{raw_version}" if raw_version else ""
    entries = envelope.get("data") or []
    rows = []
    skipped = 0
    for e in entries:
        ev = e.get("evaluations") or {}
        score = ev.get("artificial_analysis_intelligence_index")
        cost_block = e.get("artificial_analysis_intelligence_index_cost") or {}
        cpt = cost_block.get("cost_per_task") or {}
        cost = cpt.get("total_cost")
        if score is None or cost is None:
            skipped += 1
            continue
        name = e.get("name", "")
        model, effort = split_name_effort(name)
        pricing = e.get("pricing") or {}
        pin = pricing.get("price_1m_input_tokens")
        pout = pricing.get("price_1m_output_tokens")
        notes = (
            f"GRADE-A AA API實測 {score} / ${cost}; "
            f"envelope intelligence_index_version={version}; "
            f"fetched {today}; provider AA-median (Free tier cross-provider "
            f"median, no provider/plan split); slug={e.get('slug', '')}; "
            f"price_1m_in={pin} price_1m_out={pout}"
        )
        rows.append({
            "identity": f"{model} {effort} AA-median Free",
            "model": model,
            "effort": effort,
            "provider": "AA-median",
            "pricing_plan": "Free",
            "model_version": "",
            "benchmark": "AA-Intelligence-Index",
            "benchmark_version": f"AA-Intelligence-Index-{version}",
            "score": score,
            "cost_per_task": cost,
            "cost_basis": "api",
            "privacy": "",
            "is_free": "false",
            "evidence_url": "https://artificialanalysis.ai/api/v2/language/models/free",
            "checked_date": today,
            "quota": "",
            "notes": notes,
            "ttft_s": "",
            "time_per_task_s": "",
        })
    return rows, version, skipped


def fetch_all(api_key):
    """Paginate until exhausted. Returns list of envelopes."""
    envelopes = []
    page = 1
    while True:
        qs = urllib.parse.urlencode({"page": page, "page_size": PAGE_SIZE})
        req = urllib.request.Request(
            f"{BASE_URL}?{qs}", headers={"x-api-key": api_key})
        try:
            with urllib.request.urlopen(req) as resp:
                remaining = resp.headers.get("X-RateLimit-Remaining")
                print(f"page {page}: X-RateLimit-Remaining={remaining}",
                      file=sys.stderr)
                envelope = json.load(resp)
        except urllib.error.HTTPError as exc:
            if exc.code == 429:
                retry = exc.headers.get("Retry-After")
                wait = int(retry) if retry and retry.isdigit() else 60
                print(f"429 on page {page}; sleeping {wait}s then resuming",
                      file=sys.stderr)
                time.sleep(wait)
                continue
            raise
        envelopes.append(envelope)
        entries = envelope.get("data") or []
        if len(entries) < PAGE_SIZE:
            break
        page += 1
    return envelopes


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Fetch AA Data API v2 free-tier models -> "
                    "candidates.csv draft rows + version snapshot.")
    ap.add_argument("--out", default=None,
                    help="CSV output path (default: stdout)")
    ap.add_argument("--snapshot", default=None,
                    help="JSON snapshot output path")
    ap.add_argument("--dry-run", action="store_true",
                    help="parse embedded sample envelope, no network")
    args = ap.parse_args(argv)

    today = datetime.date.today().isoformat()

    if args.dry_run:
        rows, version, skipped = parse_envelope(SAMPLE_ENVELOPE, today)
        entry_count = len(SAMPLE_ENVELOPE["data"])
    else:
        api_key = os.environ.get("AA_API_KEY", "")
        if not api_key:
            print("error: AA_API_KEY env var is required",
                  file=sys.stderr)
            return 2
        envelopes = fetch_all(api_key)
        rows, version, skipped = [], "", 0
        entry_count = 0
        for env in envelopes:
            r, v, s = parse_envelope(env, today)
            rows.extend(r)
            skipped += s
            entry_count += len(env.get("data") or [])
            if v and not version:
                version = v

    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=COLUMNS)
    w.writeheader()
    w.writerows(rows)
    csv_text = buf.getvalue()
    if args.out:
        with open(args.out, "w", newline="") as f:
            f.write(csv_text)
    else:
        sys.stdout.write(csv_text)
    print(f"parsed {len(rows)} rows, skipped {skipped} null "
          f"score/cost entries", file=sys.stderr)

    if args.snapshot:
        snap = {
            "fetched_at": today,
            "intelligence_index_version": version,
            "entry_count": entry_count,
            "skipped_null_count": skipped,
        }
        with open(args.snapshot, "w") as f:
            json.dump(snap, f, indent=2)
    return 0


if __name__ == "__main__":
    sys.exit(main())
