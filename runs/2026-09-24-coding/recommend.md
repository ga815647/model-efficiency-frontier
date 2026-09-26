# Recommendation matrix (as-of run: `runs/2026-09-24-coding/candidates.csv`)
- min-score=39, max-cost=none, eps_score=2, eps_cp=5.0%, privacy-mode=all
- tier rule: anchor=overall CP peak (Codex DeepSeek V4 Flash 0731 max DeepSeek API Standard S=39 CP=433.3); width=3.5 x eps_score=7; T1=[53,+inf) T2=[46,53) T3=[39,46) T4=[32,39) T5=(-inf,32)
- Rule: frontier math by compute_frontier only; tiers display only; merged single table; FREE rows excluded.

| 級別 | merged |
|---|---|
| T1 | 攻堅 ★ Claude Code Opus 5.5 max Anthropic API Standard（S=66, $13.04）（TTFT ?s／每任務 3960s）；省錢 ★ Codex GPT-6 Sol max OpenAI API Standard（CP=19.1）（TTFT ?s／每任務 1338s）；不推：Claude Code Fable 5.1 max with fallback Anthropic API Standard、Devin Fusion CLI Fable 5.1 XHigh + SWE-2 Medium Cognition API Composite、Claude Code Opus 5 max Anthropic API Standard、Grok Build Grok 4.7 xhigh xAI API Standard、Codex GPT-5.6 Sol max OpenAI API Standard、Muse Code Muse Spark 1.3 max Meta Standard、Opencode GLM-5.3 max Z.ai API Standard |
| T2 | ★ Muse Code Muse Spark 1.3 xhigh Meta Contributor（S=48.3, $0.18, CP=268.3）攻堅＝省錢（TTFT ?s／每任務 1098s；B級推導）；不推：Kimi Code CLI Kimi K3 max Moonshot AI API Standard、Muse Code Muse Spark 1.3 xhigh Meta Standard |
| T3 | ★ Codex DeepSeek V4 Flash 0731 max DeepSeek API Standard（S=39, $0.09, CP=433.3）攻堅＝省錢（TTFT ?s／每任務 1098s）；不推：Codex DeepSeek V4 Pro 0813 max DeepSeek API Standard、Codex GPT-5.6 Luna max OpenAI API Standard、Codex Qwen3.8 Max Alibaba API Standard、Codex GPT-6 Luna max OpenAI API Standard |
| T4 | 從缺 |
| T5 | 從缺 |

FREE sidecar: 0 row(s), excluded from math.
