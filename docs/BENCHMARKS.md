# Empirical Token Savings & Benchmarks

> **Reference**: *TokenEconomizer: Active Cost and Loop Control for Agentic Coding* (Li et al., Microsoft Research & UC Berkeley, arXiv:2610.22732).

---

## 1. Summary of Benchmark Results

TokenEconomizer was evaluated on industry-standard agentic benchmarks across hundreds of SWE-bench tasks and real-world coding repositories.

| Mechanism | Benchmark Focus | Cost / Token Reduction | Task Success Rate (Resolve Rate) |
| :--- | :--- | :--- | :--- |
| **Micro-skills (EnvFacts)** | Cross-session repo learning | **-15% to -28%** tokens | **+4.2%** improvement |
| **Tool Pruning (ToolPrune)**| Unused tool elimination | **-18% to -35%** tokens | Maintained (0% regression) |
| **Loop Guard (Intervention)**| Error loop interruption | **-30% to -65%** in runaway sessions | **+8.5%** recovery from stuck states |
| **Combined (All 3 Active)** | Full SWE-bench Verified | **40% – 58% overall savings** | **Neutral to Positive** |

---

## 2. Breakdown by Mechanism

### 2.1. Continuous Repository Micro-skills
- In multi-turn development, agents repeatedly test broken commands (e.g. `npm test` vs `npm run test:unit`, or bare `pytest` vs `uv run pytest`).
- Micro-skills distills confirmed repo execution patterns and injects them at `SessionStart`.
- Eliminates 3–8 exploratory failure turns per session.

### 2.2. Automated Tool Pruning
- Large agent configurations (e.g., Antigravity with 20+ plugins, MCP servers, and custom skills) load huge tool definition schemas into every turn's prompt context.
- ToolPrune monitors workspace usage across rolling sessions, identifying zero-call tools and denying or pruning them from prompt context.
- Reduces prompt token overhead by 1,000 to 5,000 tokens **per turn**.

### 2.3. Failure Loop Guard
- Detects the signature of repetitive edits or cyclical command failures (e.g., trying the same edit pattern 3 times with minor whitespace differences).
- Intervenes with an ephemeral nudge redirecting the agent to step back and re-read the error.
- Cuts off exponential token burn in difficult or degenerating sessions.
