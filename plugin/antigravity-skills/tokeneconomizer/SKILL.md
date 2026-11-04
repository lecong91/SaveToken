---
name: tokeneconomizer
description: >-
  Inspect, configure, and control TokenEconomizer (Microsoft Research & UC Berkeley) on Google Antigravity:
  check session token cost and savings (`status`), view or manage learned repository micro-skills (`microskills`),
  inspect, apply, or restore unused tool pruning (`toolprune`), tune failure-loop intervention (`loopguard`),
  manage repository maps (`repomap`), fold finished sessions (`fold`), and run health checks (`doctor`).
  Use whenever the user mentions TokenEconomizer, `te`, `/tokeneconomizer`, micro-skills, tool pruning,
  loop guard, or asks about repository token economics.
---

# TokenEconomizer for Google Antigravity

TokenEconomizer is installed as a native Antigravity plugin (`~/.gemini/config/plugins/tokeneconomizer/`) with automatic lifecycle hooks (`SessionStart`, `PreInvocation`, `PreToolUse`, `PostToolUse`, `Stop`) and a zero-dependency Python engine (`~/.tokeneconomizer/bin/te`).

## Quick Command Reference

Always run the CLI with `--host antigravity` (or rely on automatic detection inside Antigravity) using `run_command`:

```bash
TE_BIN="${HOME}/.tokeneconomizer/bin/te"
[ -x "$TE_BIN" ] || TE_BIN="${HOME}/.gemini/config/plugins/tokeneconomizer/scripts/te"
```

| User Intent | Command to Run |
| :--- | :--- |
| **Overall status & session cost ledger** | `"$TE_BIN" --host antigravity status` |
| **Detailed explanation of current state** | `"$TE_BIN" --host antigravity status --explain` |
| **JSON status snapshot** | `"$TE_BIN" --host antigravity status --json` |
| **View learned & candidate micro-skills** | `"$TE_BIN" --host antigravity microskills` |
| **View tool pruning evidence & proposals** | `"$TE_BIN" --host antigravity toolprune show` |
| **Apply proposed tool deny-list** | `"$TE_BIN" --host antigravity toolprune apply` |
| **Restore pruned tools** | `"$TE_BIN" --host antigravity toolprune restore` |
| **Show active configuration & thresholds** | `"$TE_BIN" --host antigravity config show` |
| **Change a setting (repo-scoped or `--global`)** | `"$TE_BIN" --host antigravity config set <KEY>=<VALUE> [--global]` |
| **Reset a setting to default** | `"$TE_BIN" --host antigravity config unset <KEY> [--global]` |
| **List all tracked repositories** | `"$TE_BIN" --host antigravity repos` |
| **Fold pending/completed sessions** | `"$TE_BIN" --host antigravity fold --verbose` |
| **View or refresh repository map** | `"$TE_BIN" --host antigravity repomap [show\|refresh]` |
| **Run installation & state diagnostics** | `"$TE_BIN" --host antigravity doctor` |

---

## Core Mechanisms & Configuration Keys

1. **Micro-skills (`microskills`)**:
   - Modes: `off`, `envfacts` (learns from recurring command/environment failures with zero model calls), `on` / `envfacts+distiller` (free layer + periodic proposer).
   - Settings:
     - `microskills_propose_every=3` (sessions between proposer runs)
     - `microskills_max_facts=4`
     - `microskills_max_tokens=150`
     - `vocabulary=auto|python-git|node-web`

2. **Tool Pruning (`toolprune`)**:
   - Modes: `auto` (applies after idle window), `propose` (waits for `te toolprune apply`), `off`.
   - Settings:
     - `toolprune_evidence=10` (prompts a tool must go unused)
     - `toolprune_min_sessions=2` (minimum sessions those prompts must span)
     - `toolprune_sessions=5` (or this many sessions of any length)
     - `toolprune_quiet_minutes=60` (idle minutes before writing `.agents/tokeneconomizer.local.json`)
     - `toolprune_protect=<pattern1>,<pattern2>` (glob patterns of tools to never prune)

3. **Failure-Loop Intervention / Loop Guard (`loopguard`)**:
   - Modes: `on` (or `nudge`), `off`.
   - Settings:
     - `loopguard_aggr=default|conservative|aggressive`
     - `loopguard_nudges=1` (redirects per turn before issuing user stop notice)
     - `loopguard.envelope_min_samples=5` (green turns before envelope activates)
     - `loopguard.judge_confidence=0.7`
     - `loopguard.backstop_mult=2.5`

4. **General & Diagnostic Settings**:
   - `enabled=true|false`
   - `shadow=true|false` (compute and log all decisions without acting on them)
   - `repomap=off|on|start`

---

## Folding the Current or Finished Antigravity Session On-Demand

Antigravity conversations persist their transcript at:
`<appDataDir>/brain/<conversation-id>/.system_generated/logs/transcript.jsonl`

While finished sessions are folded automatically at the next `SessionStart` once idle, if the user asks to fold a specific session immediately so its facts and token usage appear right away in `status` and `microskills`:

```bash
"$TE_BIN" --host antigravity fold --session "<conversation-id>" --verbose
```
