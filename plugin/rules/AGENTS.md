# TokenEconomizer Active Cost & Loop Control Rules

TokenEconomizer is active in this environment, monitoring session trajectories, injecting learned repository facts at `SessionStart`, tracking unused tools, and guarding against repetitive failure loops via `PostToolUse` and `PreInvocation` hooks.

## Core Agent Behavioral Guidelines

1. **Respect Injected Repository Micro-skills**:
   - When `SessionStart` injects `# environment facts learned from earlier sessions in this repository` (or repository manual facts), treat those facts as verified ground truth for this checkout (e.g., which test runner command works, required environment variables, build prerequisites).
   - Do not waste turns re-probing commands that the injected facts already state are missing or broken (for example, if a fact states bare `pytest` fails with `command not found` and `uv run pytest` or `python -m pytest` works, run the working form directly).

2. **Follow Loop Guard Redirects (`ephemeralMessage`) Immediately**:
   - If you receive a `TokenEconomizer nudged this turn` or Loop Guard redirect message during a turn, **stop repeating the current edit/command pattern immediately**.
   - Step back, re-read the error signature, question your current hypothesis, and try a genuinely different diagnostic or implementation approach.
   - If a turn receives a `TokenEconomizer: this turn still looks stuck after a redirect` notice, relay that notice verbatim in your reply to the user as instructed.

3. **Targeted Context & Tool Economy**:
   - Prefer targeted line-range reads (`StartLine` / `EndLine`) over reading entire large files repeatedly.
   - When the user asks about TokenEconomizer status, learned facts, tool pruning, settings, or diagnostics, activate the `tokeneconomizer` skill and run `~/.tokeneconomizer/bin/te --host antigravity <subcommand>`.
