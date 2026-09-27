# Meta models fixture provenance (2026-09-27)

- First-party URL directly fetched: https://dev.meta.ai/docs/models
- Full response SHA-256: `787898d20a0b66a41a023a7bd26d1b3d7a6db68ef9fac7d54aea14c344ce24ba` (258,948 bytes; full live response not committed).
- `models.html` is the unmodified Muse Spark 1.3 `<li>` from that response, plus a terminal newline; SHA-256 `4406775de488961a95a10abe02d8768e6a4d3cae5659fda9c0ef1d8ef2099a2a`.
- The model item binds `<code>muse-spark-1.3</code>` to the statement that max reasoning is available on Standard tier only. Other model items cannot establish this identity's availability.
- Each actual fresh run independently acquires the complete models page and stores raw bytes, SHA-256, checked date, parsed fact, and retirement/exclusion audit under `snapshot/evidence/`; this test fixture does not replace fresh acquisition.
