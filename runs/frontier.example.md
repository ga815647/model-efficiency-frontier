# Frontier result (as-of run: `runs/candidates.example.csv`)
- min-score=30, max-cost=none, eps_score=2, eps_cp=5.0%, privacy-mode=all
- Rule: buckets never merged; FREE rows never in numeric frontier.

## General @ AA-2026-09 | basis=api | bucket=other (n=1)
| Score | Identity | Cost/task | CP | Provider | Training bucket | 為什麼留下 |
|---|---|---|---|---|---|---|
| 40 | CheapOther medium | $0.40 | 100.0 | Provider W | other | highest-capability start of this bucket |

## General @ AA-2026-09 | basis=api | bucket=private-safe (n=9)
| Score | Identity | Cost/task | CP | Provider | Training bucket | 為什麼留下 |
|---|---|---|---|---|---|---|
| 53 | Astra xhigh | $2.31 | 22.9 | Provider X | private-safe | highest-capability start of this bucket |
| 51 | Astra high | $1.72 | 29.7 | Provider X | private-safe | CP new high +29.2%% at score step -2.00 |
| 50 | Astra medium | $1.54 | 32.5 | Provider X | private-safe | same-tier (gap 1.00 < 2.0) CP takeover +9.5%% |
| 46 | Astra low | $0.82 | 56.1 | Provider X | private-safe | CP new high +72.8%% at score step -5.00 |
| 39 | Sol medium | $0.50 | 78.0 | Provider Y | private-safe | CP new high +39.0%% at score step -7.00 |
| 38 | Luna max | $0.18 | 211.1 | Provider Z | private-safe | same-tier (gap 1.00 < 2.0) CP takeover +170.7%% |
| 35 | Luna xhigh | $0.09 | 388.9 | Provider Z | private-safe | CP new high +84.2%% at score step -4.00 |

<details><summary>Dominated / excluded sample (2, top 5)</summary>

- Sol max (S=47, $1.99): CP no new high (23.62 <= best 32.47 x 1.05)
- Sol xhigh (S=44, $1.18): CP no new high (37.29 <= best 56.10 x 1.05)
</details>

## FREE sidecar (1, excluded from frontier math)
- FreeBot free | provider=Provider Z | quota=50 req/day | privacy=other | evidence=https://example.com/z
