"""Tests for the Google Antigravity host adapter, trace parser, and native lifecycle hooks."""
import io
import json
import os
import sys

from tokeneconomizer import loopguard, trace
from tokeneconomizer.plugin import cli, denylist, fold, hosts
from tokeneconomizer.plugin.context import LiveContext

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOOK_SCRIPT_DIR = os.path.join(REPO_ROOT, "plugin", "scripts")
if HOOK_SCRIPT_DIR not in sys.path:
    sys.path.insert(0, HOOK_SCRIPT_DIR)
import antigravity_hook  # noqa: E402


def _write_agy_transcript(path, steps):
    with open(path, "w", encoding="utf-8") as fh:
        for idx, st in enumerate(steps):
            row = dict({"step_index": idx, "status": "DONE"}, **st)
            fh.write(json.dumps(row) + "\n")


def test_antigravity_trace_parses_transcript_and_unquotes_args(tmp_path):
    tp = tmp_path / "transcript.jsonl"
    _write_agy_transcript(str(tp), [
        {"type": "USER_INPUT", "source": "USER_EXPLICIT", "content": "Run the test suite"},
        {
            "type": "PLANNER_RESPONSE",
            "source": "MODEL",
            "input_tokens": 12000,
            "cache_read_tokens": 8000,
            "output_tokens": 450,
            "model": "gemini-3.5-flash",
            "tool_calls": [
                {
                    "name": "run_command",
                    "args": {"CommandLine": '"pytest -q"', "WaitMsBeforeAsync": "5000"},
                }
            ],
        },
        {
            "type": "GENERIC",
            "source": "MODEL",
            "content": (
                "Created At: 2026-11-03T23:05:00+07:00\n"
                "Completed At: 2026-11-03T23:05:01+07:00\n"
                "Command exited with code 127.\n\n"
                "Command output:\n"
                "zsh:1: command not found: pytest\n"
            ),
        },
        {
            "type": "PLANNER_RESPONSE",
            "source": "MODEL",
            "input_tokens": 1500,
            "cache_read_tokens": 19500,
            "output_tokens": 300,
            "model": "gemini-3.5-flash",
            "tool_calls": [
                {
                    "name": "run_command",
                    "args": {"CommandLine": '"python3 -m pytest -q"'},
                },
                {
                    "name": "edit_file",
                    "args": {"Path": '"/repo/src/app.py"', "Target": '"a"', "Replacement": '"b"'},
                },
                {
                    "name": "call_mcp_tool",
                    "args": {
                        "ServerName": '"codegraph"',
                        "ToolName": '"codegraph_explore"',
                        "Arguments": {"query": "app"},
                    },
                },
            ],
        },
        {
            "type": "GENERIC",
            "source": "MODEL",
            "content": (
                "Created At: 2026-11-03T23:05:02+07:00\n"
                "Completed At: 2026-11-03T23:05:03+07:00\n"
                "Command exited with code 0.\n\n"
                "Command output:\n"
                "4 passed in 0.12s\n"
            ),
        },
        {
            "type": "GENERIC",
            "source": "MODEL",
            "content": "Made 1 replacement in /repo/src/app.py",
        },
        {
            "type": "GENERIC",
            "source": "MODEL",
            "content": "Found symbol app",
        },
    ])

    assert trace.antigravity_prompt_count(str(tp)) == 1
    usage = trace.antigravity_session_usage(str(tp))
    assert usage["input_tokens"] == 13500
    assert usage["cache_read_input_tokens"] == 27500
    assert usage["output_tokens"] == 750
    assert usage["requests"] == 2
    assert usage["model"] == "gemini-3.5-flash"

    t_usage = trace.antigravity_tool_usage(str(tp))
    assert t_usage == {
        "run_command": 2,
        "edit_file": 1,
        "mcp__codegraph__codegraph_explore": 1,
    }

    out_claude = tmp_path / "claude_trace.jsonl"
    n = trace.antigravity_session_to_claude(str(tp), str(out_claude))
    assert n == 9  # 1 user prompt + 4*(assistant tool_use + user tool_result)
    traj = trace.load_trajectory(str(out_claude))
    assert len(traj) == 4
    assert traj[0] == ("Bash", {"command": "pytest -q"}, "zsh:1: command not found: pytest", False)
    assert traj[1] == ("Bash", {"command": "python3 -m pytest -q"}, "4 passed in 0.12s", True)
    assert traj[2] == ("Edit", {"file_path": "/repo/src/app.py"}, "Made 1 replacement in /repo/src/app.py", True)
    assert traj[3][0] == "mcp__codegraph__codegraph_explore"


def test_antigravity_host_detection_and_defaults():
    assert hosts.detect({"conversationId": "conv-123", "workspacePaths": ["/w"]}).name == "antigravity"
    assert hosts.detect({}, hint="antigravity").name == "antigravity"
    assert hosts.default_host({"ANTIGRAVITY_AGENT": "1"}) == "antigravity"
    assert hosts.default_host({"TE_HOST": "antigravity", "CLAUDECODE": "1"}) == "antigravity"


def test_antigravity_hooks_end_to_end_lifecycle(tmp_path):
    te_home = tmp_path / "te_home"
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    tp = tmp_path / "transcript.jsonl"
    _write_agy_transcript(str(tp), [
        {"type": "USER_INPUT", "source": "USER_EXPLICIT", "content": "Fix bug"},
    ])

    env = {
        "TOKENECONOMIZER_HOME": str(te_home),
        "TE_CORE_PATH": REPO_ROOT,
        "TE_FOLD_SYNC": "1",
    }
    common = {
        "conversationId": "conv-agy-1",
        "workspacePaths": [str(repo_dir)],
        "transcriptPath": str(tp),
        "artifactDirectoryPath": str(tmp_path),
        "modelName": "gemini-3.5-flash",
        "lastUserInput": "Fix bug",
    }

    # Pre-seed a learned micro-skill fact and an envelope so SessionStart & LoopGuard act
    host = hosts.Antigravity()
    env["TE_MICROSKILLS"] = "envfacts"
    env["TE_LOOPGUARD"] = "on"
    env["TE_TOOLPRUNE"] = "auto"
    ctx = LiveContext.build(host, str(repo_dir), env, session_id="conv-agy-1")
    ctx.store.write("injection.json", {
        "rendered": "## Repository facts\n- Run tests with `python3 -m pytest` (bare `pytest` is missing).",
        "rendered_ids": ["fact-1"],
    })
    # Record 5 green turns to establish an envelope of ~6 calls
    for i in range(5):
        g = loopguard.TurnGuard(turn_key=f"seed-{i}")
        for _ in range(4):
            g.fold("Bash", {"command": "ls"}, "ok", 0)
        loopguard.record_turn(ctx.store, g)

    # 1. SessionStart -> returns injectSteps with systemMessage containing the micro-skill
    start_out = antigravity_hook.handle_antigravity_event("SessionStart", common, env=env)
    assert "injectSteps" in start_out
    sys_msg = start_out["injectSteps"][0]["systemMessage"]["systemMessage"]
    assert "python3 -m pytest" in sys_msg
    assert "added 1 learned fact(s)" in sys_msg

    # 2. PreInvocation -> opens a new prompt turn
    pre_out = antigravity_hook.handle_antigravity_event(
        "PreInvocation", dict(common, invocationNum=1, initialNumSteps=1), env=env
    )
    assert pre_out == {}

    # 3. PostToolUse -> simulate a churning edit+failing test loop past backstop (2.5 * 5 = 13 calls)
    for step_i in range(1, 22):
        if step_i % 2 == 1:
            tc = {"name": "edit_file", "args": {"Path": str(repo_dir / "bug.py")}}
            err = ""
        else:
            tc = {"name": "run_command", "args": {"CommandLine": "python3 -m pytest"}}
            err = "Exit code 1\nAssertionError: expected 42 got 0\n1 failed in 0.10s"
        post_out = antigravity_hook.handle_antigravity_event(
            "PostToolUse",
            dict(common, stepIdx=step_i, toolCall=tc, error=err),
            env=env,
        )
        # PostToolUse contract in Antigravity always returns {}
        assert post_out == {}

    # 4. Next PreInvocation -> flushes the queued Loop Guard redirect nudge as ephemeralMessage!
    nudge_out = antigravity_hook.handle_antigravity_event(
        "PreInvocation", dict(common, invocationNum=12, initialNumSteps=1), env=env
    )
    assert "injectSteps" in nudge_out
    eph = nudge_out["injectSteps"][0]["ephemeralMessage"]
    assert "TokenEconomizer nudged this turn" in eph

    # 5. Stop -> closes the turn
    stop_out = antigravity_hook.handle_antigravity_event(
        "Stop", dict(common, executionNum=1, terminationReason="NO_TOOL_CALL", fullyIdle=True), env=env
    )
    assert stop_out == {}


def test_antigravity_pretooluse_enforces_toolprune_denylist(tmp_path):
    te_home = tmp_path / "te_home"
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    env = {"TOKENECONOMIZER_HOME": str(te_home), "TE_CORE_PATH": REPO_ROOT}

    host = hosts.Antigravity()
    ctx = LiveContext.build(host, str(repo_dir), env, session_id="conv-prune-1")
    denylist.apply(str(repo_dir), ["mcp__canva__create-design"], ctx.store, host="antigravity")

    common = {
        "conversationId": "conv-prune-1",
        "workspacePaths": [str(repo_dir)],
    }

    # Allowed tool -> decision: "allow"
    res_ok = antigravity_hook.handle_antigravity_event(
        "PreToolUse",
        dict(common, toolCall={"name": "run_command", "args": {"CommandLine": "ls"}}),
        env=env,
    )
    assert res_ok == {"decision": "allow"}

    # Pruned MCP tool -> decision: "ask" with explanation
    res_pruned = antigravity_hook.handle_antigravity_event(
        "PreToolUse",
        dict(
            common,
            toolCall={
                "name": "call_mcp_tool",
                "args": {"ServerName": "canva", "ToolName": "create-design", "Arguments": {}},
            },
        ),
        env=env,
    )
    assert res_pruned["decision"] == "ask"
    assert "mcp__canva__create-design" in res_pruned["reason"]

    # Restore -> allowed again
    denylist.restore(str(repo_dir), ctx.store, host="antigravity")
    res_restored = antigravity_hook.handle_antigravity_event(
        "PreToolUse",
        dict(
            common,
            toolCall={
                "name": "call_mcp_tool",
                "args": {"ServerName": "canva", "ToolName": "create-design", "Arguments": {}},
            },
        ),
        env=env,
    )
    assert res_restored == {"decision": "allow"}


def test_antigravity_fold_learns_microskills_and_records_ledger(tmp_path):
    te_home = tmp_path / "te_home"
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    (repo_dir / "pyproject.toml").write_text("[project]\nname='demo'\n")
    env = {
        "TOKENECONOMIZER_HOME": str(te_home),
        "TE_CORE_PATH": REPO_ROOT,
        "TE_FOLD_SYNC": "1",
        "TE_MICROSKILLS": "envfacts",
    }

    host = hosts.Antigravity()
    ctx = LiveContext.build(host, str(repo_dir), env)

    # Fold 4 sessions where bare `pytest` fails with command not found and `python -m pytest` passes
    for i in range(1, 5):
        sid = f"agy-sess-{i}"
        tp = tmp_path / f"transcript-{i}.jsonl"
        _write_agy_transcript(str(tp), [
            {"type": "USER_INPUT", "source": "USER_EXPLICIT", "content": "run tests"},
            {
                "type": "PLANNER_RESPONSE",
                "source": "MODEL",
                "input_tokens": 5000,
                "cache_read_tokens": 10000,
                "output_tokens": 200,
                "model": "gemini-3.5-flash",
                "tool_calls": [{"name": "run_command", "args": {"CommandLine": '"pytest"'}}],
            },
            {
                "type": "GENERIC",
                "source": "MODEL",
                "content": "Command exited with code 127.\n\nCommand output:\n/bin/sh: pytest: command not found\n",
            },
            {
                "type": "PLANNER_RESPONSE",
                "source": "MODEL",
                "input_tokens": 1000,
                "cache_read_tokens": 15000,
                "output_tokens": 200,
                "model": "gemini-3.5-flash",
                "tool_calls": [{"name": "run_command", "args": {"CommandLine": '"python -m pytest"'}}],
            },
            {
                "type": "GENERIC",
                "source": "MODEL",
                "content": "Command exited with code 0.\n\nCommand output:\n3 passed in 0.05s\n",
            },
        ])
        sctx = LiveContext.build(host, str(repo_dir), env, session_id=sid)
        sctx.store.write(f"sessions/{sid}.json", {
            "session_id": sid, "host": "antigravity", "started": 1000.0 + i,
            "ended": 1010.0 + i, "cwd": str(repo_dir), "transcript": str(tp),
        })
        rec = fold.fold_session(sctx, sid, str(tp))
        assert rec is not None
        assert rec["effective_tokens"] > 0
        assert rec["priced_by"] == "model"

    inj = ctx.store.read("injection.json") or {}
    assert "python -m pytest" in (inj.get("rendered") or "")


def test_antigravity_hook_fails_open_on_invalid_input(tmp_path):
    env = {"TOKENECONOMIZER_HOME": str(tmp_path / "te_home"), "TE_CORE_PATH": REPO_ROOT}
    out = io.StringIO()
    rc = antigravity_hook.main(["--event", "SessionStart"], stdin=io.StringIO("{bad json"), stdout=out, env=env)
    assert rc == 0
    assert json.loads(out.getvalue()) == {}

    out_pre = io.StringIO()
    rc_pre = antigravity_hook.main(["--event", "PreToolUse"], stdin=io.StringIO("{bad json"), stdout=out_pre, env=env)
    assert rc_pre == 0
    assert json.loads(out_pre.getvalue()) == {"decision": "allow"}
