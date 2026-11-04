"""Google Antigravity session transcript (`transcript.jsonl`) and hook event reader.

Antigravity writes each conversation's log as JSON Lines (`transcript.jsonl`) under
`<appDataDir>/brain/<conversation-id>/.system_generated/logs/transcript.jsonl`. Each line is a
step object carrying:

  * `type == "USER_INPUT"` (`source == "USER_EXPLICIT"`): a user prompt;
  * `type == "PLANNER_RESPONSE"`: a model response with `input_tokens`, `cache_read_tokens`,
    `output_tokens`, and `tool_calls: [{"name": ..., "args": {...}}]`;
  * `type == "GENERIC"`: the tool output step(s) immediately following a `PLANNER_RESPONSE`'s
    `tool_calls`, with `status` ("DONE", "ERROR", "RUNNING") and `content`.

This module converts Antigravity transcripts (or hook-recorded event spools) into the
Claude-shaped trajectory that `PrefixStage`, `ToolingStage` and `SpiralState` consume, and reads
token usage, prompt counts, and tool usage directly.
"""
import json
import os
import re

from .jsonl import lines as _lines

_EXIT_CODE_RE = re.compile(
    r"(?im)(?:Command exited with code|exit status|Process exited with code)[:\s]+(-?\d+)"
)
_HEADER_RE = re.compile(
    r"\ACreated At:\s*[^\n]+\n(?:Completed At:\s*[^\n]+\n)?"
    r"(?:The tool's output was truncated[^\n]*\n\nHere is a preview[^\n]*\n)?"
    r"(?:Command exited with code -?\d+\.\n\n(?:Command output:\n|No output from the command\.)?)?"
)


def _unquote_val(v):
    """Antigravity's transcript.jsonl encodes string arguments as JSON-quoted strings
    (e.g. `'"ls -la"'`). Unwrap one layer of JSON string encoding when present."""
    if isinstance(v, str) and len(v) >= 2 and v.startswith('"') and v.endswith('"'):
        try:
            parsed = json.loads(v)
            if isinstance(parsed, str):
                return parsed
        except ValueError:
            pass
    return v


def _clean_args(args):
    if not isinstance(args, dict):
        return {}
    return {k: _unquote_val(v) for k, v in args.items()}


def _clean_output(text):
    if not isinstance(text, str):
        return ""
    cleaned = _HEADER_RE.sub("", text, count=1)
    return cleaned.strip()


def _extract_exit_code(text):
    if not isinstance(text, str):
        return None
    m = _EXIT_CODE_RE.search(text[:600])
    return int(m.group(1)) if m else None


def normalize_antigravity_tool(name, args):
    """Map an Antigravity tool call to the canonical Claude-shaped (tool_name, tool_input)
    expected by `PrefixStage` (microskills) and `SpiralState` (loopguard)."""
    args = _clean_args(args)
    low = (name or "").lower()
    if low in ("run_command", "bash", "shell"):
        cmd = args.get("CommandLine") or args.get("command") or args.get("cmd") or ""
        return "Bash", {"command": str(cmd)}
    if low in ("edit_file", "edit", "multiedit", "multi_edit"):
        path = args.get("Path") or args.get("file_path") or args.get("path") or ""
        return "Edit", {"file_path": str(path)}
    if low in ("write_file", "write", "create"):
        path = args.get("Path") or args.get("file_path") or args.get("path") or ""
        return "Write", {"file_path": str(path)}
    if low in ("read_file", "read", "view", "view_file"):
        path = args.get("Path") or args.get("file_path") or args.get("path") or ""
        return "Read", {"file_path": str(path)}
    if low == "call_mcp_tool":
        srv = args.get("ServerName") or "mcp"
        tname = args.get("ToolName") or "tool"
        sub_args = args.get("Arguments")
        return f"mcp__{srv}__{tname}", (sub_args if isinstance(sub_args, dict) else {})
    return str(name or "unknown"), args


def raw_antigravity_tool_name(name, args):
    """The tool name as counted for tool pruning on Antigravity."""
    args = _clean_args(args)
    if (name or "").lower() == "call_mcp_tool":
        srv = args.get("ServerName") or "mcp"
        tname = args.get("ToolName") or "tool"
        return f"mcp__{srv}__{tname}"
    return str(name or "")


def antigravity_session_to_claude(path, out_path):
    """Convert an Antigravity `transcript.jsonl` (or hook event spool) to a Claude-shaped
    JSONL file at `out_path`. Returns the number of records written, or None if unreadable."""
    try:
        raw_lines = _lines(path)
    except OSError:
        return None
    if not raw_lines:
        return None

    events = []
    for line in raw_lines:
        try:
            ev = json.loads(line)
        except ValueError:
            continue
        if isinstance(ev, dict):
            events.append(ev)
    if not events:
        return None

    # Check if this is a hook-event spool (fallback when transcriptPath was not provided)
    if any("hook_event_name" in ev for ev in events):
        from .cursor import cursor_events_to_claude
        return cursor_events_to_claude(path, out_path)

    out = []
    pending_calls = []  # queue of (tid, norm_name, norm_args) awaiting GENERIC result steps
    call_seq = 0

    def flush_unpaired():
        while pending_calls:
            tid, n_name, n_args = pending_calls.pop(0)
            out.append({"type": "assistant", "message": {
                "content": [{"type": "tool_use", "id": tid, "name": n_name, "input": n_args}]}})
            out.append({"type": "user", "message": {
                "content": [{"type": "tool_result", "tool_use_id": tid,
                             "content": "", "is_error": False}]}})

    for ev in events:
        step_type = ev.get("type")
        if step_type == "USER_INPUT" and ev.get("source") == "USER_EXPLICIT":
            flush_unpaired()
            text = ev.get("content") or ""
            if isinstance(text, str) and text.strip():
                out.append({"type": "user", "message": {
                    "content": [{"type": "text", "text": text}]}})
        elif step_type == "PLANNER_RESPONSE":
            flush_unpaired()
            tcs = ev.get("tool_calls") or []
            if isinstance(tcs, list):
                for tc in tcs:
                    if not isinstance(tc, dict) or not tc.get("name"):
                        continue
                    call_seq += 1
                    tid = f"agy-{ev.get('step_index', call_seq)}-{call_seq}"
                    n_name, n_args = normalize_antigravity_tool(tc.get("name"), tc.get("args"))
                    pending_calls.append((tid, n_name, n_args))
        elif step_type == "GENERIC" and pending_calls:
            tid, n_name, n_args = pending_calls.pop(0)
            raw_content = ev.get("content") or ""
            code = _extract_exit_code(raw_content)
            failed = (ev.get("status") == "ERROR") or (code is not None and code != 0)
            cleaned = _clean_output(raw_content)
            out.append({"type": "assistant", "message": {
                "content": [{"type": "tool_use", "id": tid, "name": n_name, "input": n_args}]}})
            out.append({"type": "user", "message": {
                "content": [{"type": "tool_result", "tool_use_id": tid,
                             "content": cleaned, "is_error": failed}]}})

    flush_unpaired()

    try:
        with open(out_path, "w", encoding="utf-8") as fh:
            for item in out:
                fh.write(json.dumps(item, ensure_ascii=False) + "\n")
    except OSError:
        return None
    return len(out)


def antigravity_prompt_count(transcript_path):
    """How many user prompts were submitted in an Antigravity transcript."""
    if not transcript_path or not os.path.exists(transcript_path):
        return 0
    n = 0
    for line in _lines(transcript_path):
        try:
            ev = json.loads(line)
        except ValueError:
            continue
        if not isinstance(ev, dict):
            continue
        if ev.get("type") == "USER_INPUT" and ev.get("source") == "USER_EXPLICIT":
            n += 1
        elif ev.get("hook_event_name") == "UserPromptSubmit":
            n += 1
    return n


def antigravity_session_usage(transcript_path):
    """Token usage breakdown across all `PLANNER_RESPONSE` steps in an Antigravity transcript."""
    if not transcript_path or not os.path.exists(transcript_path):
        return {}
    inp = cache_read = cache_write = out_tok = requests = 0
    models = {}
    by_step = {}
    for idx, line in enumerate(_lines(transcript_path)):
        if "input_tokens" not in line and "output_tokens" not in line:
            continue
        try:
            ev = json.loads(line)
        except ValueError:
            continue
        if not isinstance(ev, dict) or ev.get("type") != "PLANNER_RESPONSE":
            continue
        step_key = ev.get("step_index", f"line-{idx}")
        by_step[step_key] = {
            "input_tokens": int(ev.get("input_tokens") or 0),
            "cache_read_input_tokens": int(
                ev.get("cache_read_tokens") or ev.get("cache_read_input_tokens") or 0
            ),
            "cache_creation_input_tokens": int(
                ev.get("cache_creation_tokens") or ev.get("cache_creation_input_tokens") or 0
            ),
            "output_tokens": int(ev.get("output_tokens") or 0),
        }
        model = ev.get("model") or ev.get("modelName")
        if model and str(model).lower() != "auto":
            models[model] = models.get(model, 0) + 1

    if not by_step:
        return {}

    for u in by_step.values():
        inp += u["input_tokens"]
        cache_read += u["cache_read_input_tokens"]
        cache_write += u["cache_creation_input_tokens"]
        out_tok += u["output_tokens"]
    requests = len(by_step)
    return {
        "input_tokens": inp,
        "cache_read_input_tokens": cache_read,
        "cache_creation_input_tokens": cache_write,
        "output_tokens": out_tok,
        "requests": requests,
        "model": max(models, key=models.get) if models else None,
        "files": 1,
    }


def antigravity_tool_usage(transcript_path):
    """{tool_name: calls} over an Antigravity transcript."""
    if not transcript_path or not os.path.exists(transcript_path):
        return {}
    counts = {}
    for line in _lines(transcript_path):
        try:
            ev = json.loads(line)
        except ValueError:
            continue
        if not isinstance(ev, dict):
            continue
        if ev.get("type") == "PLANNER_RESPONSE":
            for tc in ev.get("tool_calls") or []:
                if isinstance(tc, dict) and tc.get("name"):
                    tname = raw_antigravity_tool_name(tc.get("name"), tc.get("args"))
                    if tname:
                        counts[tname] = counts.get(tname, 0) + 1
        elif ev.get("hook_event_name") in ("PostToolUse", "PostToolUseFailure"):
            tname = ev.get("raw_tool_name") or ev.get("tool_name")
            if tname:
                counts[tname] = counts.get(tname, 0) + 1
    if not counts:
        from .calls import tool_usage
        return tool_usage(transcript_path)
    return counts
