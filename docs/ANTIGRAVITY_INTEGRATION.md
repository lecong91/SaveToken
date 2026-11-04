# Google Antigravity Integration Guide

## 1. Overview

**SaveToken** extends Microsoft Research & UC Berkeley's **TokenEconomizer** architecture to provide first-class support for **Google Antigravity** (`agy`).

Google Antigravity coordinates AI agents through conversational contexts, tools, MCP servers, and background execution tasks. Without active token control, sessions accumulate repetitive context, redundant tool definitions, and failure loops that consume millions of unnecessary tokens.

SaveToken hooks into Antigravity's lifecycle events to apply three complementary mechanisms in real time:
1. **Continuous Repository Micro-skills** (`SessionStart`): Learns repository facts across sessions and injects only high-confidence rules at startup.
2. **Dynamic Tool Pruning** (`PreInvocation`): Denies unused or irrelevant tools to dramatically reduce per-turn prompt overhead.
3. **Loop Guard Interventions** (`PostToolUse` / `PreInvocation`): Detects repetitive error patterns and redirects the agent before it burns context tokens.

---

## 2. Antigravity Hook Architecture

Antigravity executes external lifecycle hooks configured in `<plugin_dir>/hooks.json`:

```
┌────────────────────────────────────────────────────────┐
│                   Google Antigravity                   │
└───────┬───────────────────┬───────────────────┬────────┘
        │ (SessionStart)    │ (PreInvocation)   │ (PostToolUse)
        ▼                   ▼                   ▼
┌────────────────────────────────────────────────────────┐
│          scripts/antigravity_hook.py                   │
│   (Receives camelCase JSON via stdin, outputs stdout)  │
└───────────────────────┬────────────────────────────────┘
                        │
                        ▼
┌────────────────────────────────────────────────────────┐
│          SaveToken Controller (Core Python)            │
│  - Environment Facts Distiller                         │
│  - Tool Pruning Engine                                 │
│  - Loop Guard Intervention Judge                       │
└────────────────────────────────────────────────────────┘
```

### 2.1. The 5 Integrated Lifecycle Hooks

| Hook Event | Trigger Point | SaveToken Action | Antigravity Output |
| :--- | :--- | :--- | :--- |
| **`SessionStart`** | When conversation session begins or restarts | Distills verified facts from prior sessions in the current repository | Injects `systemMessage` with repo micro-skills |
| **`PreInvocation`** | Before the LLM planner is called | Evaluates token budget and checks loop guard state | Injects `ephemeralMessage` if a redirect was triggered |
| **`PreToolUse`** | Before executing a tool call | Enforces deny list for pruned tools (`toolprune`) | Returns `{"decision": "allow"}` or `{"decision": "deny"}` |
| **`PostToolUse`** | After a tool call completes | Inspects tool result and exit codes for failure loops | Injects nudge or warning if consecutive failures detected |
| **`Stop`** | When conversation session completes or stops | Records session token metrics to local ledger (`te fold`) | Updates cache-aware token accounting ledger |

### 2.2. Protocol & Encoding
- **Input (`stdin`)**: Antigravity encodes hook payloads in protojson **camelCase** (e.g. `conversationId`, `stepIdx`, `toolCall`, `toolResult`, `workspacePaths`).
- **Output (`stdout`)**: SaveToken returns JSON objects matching Antigravity specifications:
  ```json
  {
    "injectSteps": [
      {
        "systemMessage": "# environment facts learned from earlier sessions in this repository\n..."
      }
    ],
    "decision": "allow"
  }
  ```
- **Error Handling**: Non-zero exit codes or unhandled exceptions fail safely without disrupting the agent session.

---

## 3. Transcript Parsing (`tokeneconomizer.trace.antigravity`)

Antigravity logs trajectories in `<conversation_dir>/.system_generated/logs/transcript.jsonl`.
SaveToken's `antigravity.py` trace parser:
1. Pairs `PLANNER_RESPONSE` (assistant tool calls) with `GENERIC` (tool executions and outputs).
2. Unquotes and normalizes JSON-quoted tool arguments (e.g., `tool_calls.args`).
3. Extracts tool execution exit codes and error signatures.
4. Reads precise token breakdowns (`input_tokens`, `output_tokens`, `cached_tokens`) for exact accounting.

---

## 4. Verification

To verify that the integration is active in your Antigravity environment:

```bash
# Check health status
te doctor

# Inspect active hooks and learned micro-skills
te status --explain

# View token ledger
te ledger
```
