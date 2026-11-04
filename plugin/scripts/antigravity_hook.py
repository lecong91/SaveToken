#!/usr/bin/env python3
"""Native Google Antigravity lifecycle hook dispatcher for TokenEconomizer.

Translates Antigravity's `hooks.json` stdin/stdout contract:
  * `SessionStart`  -> injects learned micro-skills and notices via `injectSteps.systemMessage`
  * `PreToolUse`    -> enforces applied tool-pruning deny lists (`decision: "ask"` or `"allow"`)
  * `PostToolUse`   -> folds completed tool calls into `TurnGuard`, queueing any redirect/notice
  * `PreInvocation` -> opens new prompt-turns and delivers queued Loop Guard redirects via
                       `injectSteps.ephemeralMessage`
  * `Stop`          -> closes the turn, feeds green turns into the repository envelope

Always fails open: any unhandled exception logs to `~/.tokeneconomizer/errors.log` and prints
`{"decision": "allow"}` (for `PreToolUse`) or `{}` (for all other events).
"""
import contextlib
import hashlib
import json
import os
import sys
import time
import traceback


def _bootstrap():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    plugin_root = os.path.dirname(script_dir)
    os.environ["TE_PLUGIN_ROOT"] = plugin_root
    for cand in (
        os.environ.get("TE_CORE_PATH"),
        os.path.join(plugin_root, "lib"),
        os.path.dirname(plugin_root),
    ):
        if cand and os.path.isfile(os.path.join(cand, "tokeneconomizer", "plugin", "hook.py")):
            if cand not in sys.path:
                sys.path.insert(0, cand)
            return True
    return False


def _extract_messages(out):
    """Extract (context_text, notice_text) from a LiveController output dict."""
    if not isinstance(out, dict):
        return "", ""
    hso = out.get("hookSpecificOutput") if isinstance(out.get("hookSpecificOutput"), dict) else {}
    ctx_text = (hso.get("additionalContext") or out.get("additionalContext")
                or out.get("additional_context") or "").strip()
    notice_text = (out.get("systemMessage") or "").strip()
    return ctx_text, notice_text


def _truthy(v):
    return str(v or "").strip().lower() in ("1", "true", "yes", "on")


def handle_antigravity_event(event, payload, env=None):
    """Process one Antigravity hook payload and return the Antigravity-formatted stdout dict."""
    env = os.environ if env is None else env
    if _truthy(env.get("TE_SIDECALL")) or _truthy(env.get("TE_DISABLE")):
        return {"decision": "allow"} if event == "PreToolUse" else {}

    from tokeneconomizer import trace
    from tokeneconomizer.plugin import denylist, hosts
    from tokeneconomizer.plugin.context import LiveContext
    from tokeneconomizer.plugin.controller import LiveController

    host = hosts.Antigravity()
    sid = host.session_id(payload)
    if not sid:
        return {"decision": "allow"} if event == "PreToolUse" else {}

    cwd = host.cwd(payload, env)
    ctx = LiveContext.build(host, cwd, env, session_id=sid, settle=False)
    if not ctx.config.enabled:
        return {"decision": "allow"} if event == "PreToolUse" else {}

    # 1. PreToolUse: check tool pruning deny list
    if event == "PreToolUse":
        if ctx.config.toolprune != "off" and not ctx.config.shadow:
            applied = set(denylist.applied_for(ctx.store, ctx.repo.root, "antigravity"))
            if applied:
                tc = payload.get("toolCall") if isinstance(payload.get("toolCall"), dict) else {}
                raw_name = tc.get("name") or ""
                raw_args = tc.get("args") if isinstance(tc.get("args"), dict) else {}
                tname = trace.raw_antigravity_tool_name(raw_name, raw_args)
                srv = raw_args.get("ServerName") if raw_name == "call_mcp_tool" else None
                matched = tname if tname in applied else (srv if srv in applied else None)
                if matched:
                    return {
                        "decision": "ask",
                        "reason": (
                            f"TokenEconomizer Tool Pruning: '{matched}' was pruned in "
                            f"{ctx.repo.label} due to non-use. Confirm to run once, or execute "
                            f"`~/.tokeneconomizer/bin/te --host antigravity toolprune restore` "
                            f"to restore permanently."
                        ),
                    }
        return {"decision": "allow"}

    # 2. SessionStart: inject learned micro-skills & notices
    if event == "SessionStart":
        p = dict(payload, hook_event_name="SessionStart")
        p = host.prepare(p, env)
        out = LiveController(ctx, p).handle() or {}
        ctx_text, notice_text = _extract_messages(out)
        parts = [x for x in (ctx_text, notice_text) if x]
        if parts:
            return {
                "injectSteps": [
                    {
                        "systemMessage": {
                            "systemMessage": "\n\n".join(parts)
                        }
                    }
                ]
            }
        return {}

    # 3. PostToolUse: fold tool call into TurnGuard and queue any redirect/notice for PreInvocation
    if event == "PostToolUse":
        inner_event = "PostToolUseFailure" if payload.get("error") else "PostToolUse"
        p = dict(payload, hook_event_name=inner_event)
        p = host.prepare(p, env)
        out = LiveController(ctx, p).handle() or {}
        ctx_text, notice_text = _extract_messages(out)
        parts = [x for x in (ctx_text, notice_text) if x]
        if parts:
            sess_path = os.path.join("sessions", f"{sid}.json")
            sess = ctx.store.read(sess_path) or {}
            queued = list(sess.get("pending_inject_steps") or [])
            queued.append("\n\n".join(parts))
            sess["pending_inject_steps"] = queued
            ctx.store.write(sess_path, sess)
        return {}

    # 4. PreInvocation: detect new prompt-turn (UserPromptSubmit) and flush queued redirects
    if event == "PreInvocation":
        sess_path = os.path.join("sessions", f"{sid}.json")
        sess = ctx.store.read(sess_path) or {}
        prompt_text = str(payload.get("lastUserInput") or "")
        init_steps = payload.get("initialNumSteps")
        marker = hashlib.sha1(f"{init_steps}:{prompt_text}".encode("utf-8")).hexdigest()[:16]

        inject_texts = []
        if prompt_text and sess.get("last_turn_marker") != marker:
            sess["last_turn_marker"] = marker
            ctx.store.write(sess_path, sess)
            p = dict(payload, hook_event_name="UserPromptSubmit")
            p = host.prepare(p, env)
            out = LiveController(ctx, p).handle() or {}
            ctx_text, notice_text = _extract_messages(out)
            for x in (ctx_text, notice_text):
                if x:
                    inject_texts.append(x)
            # Re-read session after controller updated it
            sess = ctx.store.read(sess_path) or {}
            sess["last_turn_marker"] = marker

        queued = list(sess.get("pending_inject_steps") or [])
        if queued:
            inject_texts.extend(queued)
            sess.pop("pending_inject_steps", None)
            ctx.store.write(sess_path, sess)
        elif prompt_text:
            ctx.store.write(sess_path, sess)

        if inject_texts:
            return {
                "injectSteps": [
                    {
                        "ephemeralMessage": "\n\n".join(inject_texts)
                    }
                ]
            }
        return {}

    # 5. Stop: close turn and update envelope
    if event == "Stop":
        p = dict(payload, hook_event_name="Stop")
        p = host.prepare(p, env)
        LiveController(ctx, p).handle()
        return {}

    return {}


def _record_error(env):
    try:
        from tokeneconomizer.plugin.paths import state_root
        root = state_root(env)
        os.makedirs(root, exist_ok=True)
        with open(os.path.join(root, "errors.log"), "a", encoding="utf-8") as fh:
            fh.write(f"--- {time.strftime('%Y-%m-%dT%H:%M:%S')} antigravity_hook pid={os.getpid()}\n")
            fh.write(traceback.format_exc())
    except Exception:
        pass


def main(argv=None, stdin=None, stdout=None, env=None):
    argv = sys.argv[1:] if argv is None else argv
    stdin = sys.stdin if stdin is None else stdin
    stdout = sys.stdout if stdout is None else stdout
    env = os.environ if env is None else env

    event = "SessionStart"
    if "--event" in argv:
        i = argv.index("--event")
        if i + 1 < len(argv):
            event = argv[i + 1]

    default_out = {"decision": "allow"} if event == "PreToolUse" else {}
    out = default_out
    try:
        os.umask(0o077)
        buf = getattr(stdin, "buffer", None)
        raw = buf.read().decode("utf-8", errors="replace") if buf is not None else stdin.read()
        if _bootstrap():
            payload = json.loads(raw) if raw.strip() else {}
            if isinstance(payload, dict):
                with contextlib.redirect_stdout(sys.stderr):
                    out = handle_antigravity_event(event, payload, env=env)
                    if not isinstance(out, dict):
                        out = default_out
                from tokeneconomizer.plugin.paths import secure_root
                secure_root(env)
    except Exception:
        _record_error(env)
        out = default_out

    stdout.write(json.dumps(out))
    stdout.write("\n")
    stdout.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main())
