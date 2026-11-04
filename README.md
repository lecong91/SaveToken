# SaveToken

**Cross-Platform Token & Cost Control Engine for Google Antigravity & Agentic Coding Assistants**  
*Optimized for macOS and Windows | Zero External Runtime Dependencies*

[![CI - Multi-OS Test Suite](https://github.com/lecong91/SaveToken/actions/workflows/ci.yml/badge.svg)](https://github.com/lecong91/SaveToken/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Windows%20%7C%20Linux-lightgrey.svg)]()

---

## Overview

**SaveToken** is a production-grade adaptation of Microsoft Research & UC Berkeley's **TokenEconomizer** (*arXiv:2610.22732*), engineered specifically to deliver first-class, cross-platform cost reduction and loop control for **Google Antigravity** (`agy`).

By orchestrating black-box lifecycle hooks, SaveToken reduces total LLM token consumption by **40% to 58%** without sacrificing agent intelligence or problem-solving capability.

### Key Capabilities

- **Continuous Repository Micro-skills**: Automatically observes test and build execution across agent sessions. Confirmed repository facts (e.g., correct test runners, environment variables) are learned and injected at `SessionStart`, eliminating repeated exploratory failures.
- **Dynamic Unused Tool Pruning (`toolprune`)**: Automatically tracks tool usage across tasks. Dormant tools and extraneous MCP definitions are removed from prompts, saving 1,000–5,000 prompt tokens per turn.
- **Failure-Loop Guard (`loopguard`)**: Detects repetitive command failures and thrashing edits. Intervenes proactively with targeted nudges before exponential context burn occurs.
- **Cache-Aware Token Accounting (`ledger`)**: Accurately accounts for prompt caching (e.g. Gemini, Claude prompt cache), calculating precise dollar savings and effective token usage.
- **Zero-Dependency Architecture**: Runs on pure Python standard library (`sys`, `os`, `json`, `subprocess`). No external packages required at runtime.
- **Cross-Platform Compatibility**: Full, tested support for **macOS**, **Windows** (Command Prompt & PowerShell), and **Linux**.

---

## 1-Click Installation

### On macOS / Linux
Open your terminal and run:
```bash
git clone https://github.com/lecong91/SaveToken.git
cd SaveToken
./install.sh
```

### On Windows
Open PowerShell as your current user:
```powershell
git clone https://github.com/lecong91/SaveToken.git
cd SaveToken
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\install.ps1
```
*(Or in Command Prompt `cmd.exe`, run `install.bat`)*

### Universal (Python)
```bash
python scripts/install_antigravity.py
```

After installation:
1. Ensure `~/.tokeneconomizer/bin` (or `%USERPROFILE%\.tokeneconomizer\bin` on Windows) is in your `PATH`.
2. Verify the installation:
   ```bash
   te doctor
   ```
3. Restart Google Antigravity to activate the plugin.

---

## CLI Usage

SaveToken includes the `te` command-line utility for inspection and control:

```bash
# Health check and environment diagnostic
te doctor

# Check session token savings and active hooks
te status --explain

# View learned repository facts (micro-skills)
te microskills list

# Inspect unused tool pruning proposals
te toolprune show

# View historical token savings ledger
te ledger

# Fold and summarize a finished conversation trajectory
te fold --session <conversation_id>
```

---

## Architecture & Lifecycle Hooks

SaveToken integrates natively into Google Antigravity via `<plugin_dir>/hooks.json`:

```
Google Antigravity
    │
    ├── SessionStart   ──► Injects learned repository micro-skills
    ├── PreInvocation  ──► Enforces token budgets and checks loop guard
    ├── PreToolUse     ──► Enforces tool pruning deny list
    ├── PostToolUse    ──► Detects failure signatures & triggers nudges
    └── Stop           ──► Updates cache-aware token ledger
```

For detailed protocol specifications, see [docs/ANTIGRAVITY_INTEGRATION.md](docs/ANTIGRAVITY_INTEGRATION.md).  
For Windows-specific configurations, see [docs/WINDOWS_SETUP.md](docs/WINDOWS_SETUP.md).  
For empirical benchmark data, see [docs/BENCHMARKS.md](docs/BENCHMARKS.md).

---

## Running Tests

SaveToken comes with a comprehensive test suite (550+ tests):

```bash
# Using pytest
python -m pytest tests/

# Using uv
uv run --with pytest pytest tests/
```

Continuous integration runs on Ubuntu, macOS, and Windows runners automatically via GitHub Actions.

---

## Academic Credit & Citation

SaveToken builds upon the foundational research by Microsoft Research and UC Berkeley:

```bibtex
@article{li2026tokeneconomizer,
  title={TokenEconomizer: Active Cost and Loop Control for Agentic Coding},
  author={Li, Bo and et al.},
  journal={arXiv preprint arXiv:2610.22732},
  year={2026}
}
```

Original upstream project: [https://github.com/microsoft/TokenEconomizer](https://github.com/microsoft/TokenEconomizer)

---

## License

This project is licensed under the [MIT License](LICENSE).
