#!/usr/bin/env python3
"""Orchestrates the nightly autonomous tech-debt refactor pipeline.

Flow: scan (reuses debt-scan.md) -> plan (debt-plan.md) -> execute each
phase (debt-execute-phase.md) with an external scope check and an external
build/typecheck/test gate after every phase -> commit-or-revert per phase
-> if anything committed, final verify + open a PR (never merges).

Claude is only ever given Read/Grep/Glob (+Edit during phase execution).
This script is the only thing that touches git, gh, and npm.
"""
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(os.environ.get("GITHUB_WORKSPACE", ".")).resolve()
PROMPTS_DIR = REPO_ROOT / ".claude" / "prompts"
ARTIFACTS_DIR = Path(os.environ.get("RUNNER_TEMP", "/tmp")) / "autonomous-refactor"
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

SCAN_MODEL = "claude-haiku-4-5-20251001"
EDIT_MODEL = "claude-sonnet-5"
VERIFY_STEPS = [["npm", "run", "typecheck"], ["npm", "test"], ["npm", "run", "build"]]

RUN_ID = os.environ.get("GITHUB_RUN_ID", str(int(time.time())))
TODAY = time.strftime("%Y-%m-%d", time.gmtime())
BRANCH_NAME = f"tech-debt/auto-refactor-{TODAY}-{RUN_ID}"


def log(message):
    print(f"[autonomous-refactor] {message}", flush=True)


def write_summary(text):
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        with open(summary_path, "a", encoding="utf-8") as f:
            f.write(text + "\n")
    else:
        print(text)


def run(cmd, cwd=REPO_ROOT, check=True, capture=True):
    result = subprocess.run(cmd, cwd=cwd, capture_output=capture, text=True)
    if check and result.returncode != 0:
        raise RuntimeError(
            f"command failed: {' '.join(cmd)}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    return result


def run_claude(prompt_text, model, max_turns, allowed_tools, log_name, timeout=900):
    cmd = [
        "claude", "-p", prompt_text,
        "--model", model,
        "--max-turns", str(max_turns),
        "--output-format", "text",
        "--allowedTools", allowed_tools,
    ]
    try:
        result = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        (ARTIFACTS_DIR / log_name).write_text(f"TIMEOUT after {timeout}s\n{exc}", encoding="utf-8")
        return None
    (ARTIFACTS_DIR / log_name).write_text(
        f"exit={result.returncode}\n\n--- stdout ---\n{result.stdout}\n\n--- stderr ---\n{result.stderr}",
        encoding="utf-8",
    )
    if result.returncode != 0:
        return None
    return result.stdout


def split_scan_output(text):
    """Same fence-split contract as claude-debt-scan.yml: markdown, then a ```json block."""
    match = re.search(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL)
    if not match:
        return None, None
    summary = json.loads(match.group(1))
    issue_body = text[: match.start()].rstrip() + "\n"
    return issue_body, summary


def extract_json_block(text):
    match = re.search(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL)
    if match:
        return json.loads(match.group(1))
    return json.loads(text.strip())


def git_status():
    """path -> 2-char porcelain status code, e.g. ' M' or '??'. Assumes no renames."""
    result = run(["git", "status", "--porcelain"])
    status = {}
    for line in result.stdout.splitlines():
        if not line:
            continue
        code, path = line[:2], line[3:]
        status[path] = code
    return status


def revert_working_tree():
    status = git_status()
    for path, code in status.items():
        full = REPO_ROOT / path
        if code == "??":
            if full.exists():
                full.unlink()
        else:
            run(["git", "checkout", "--", path], check=False)
    run(["git", "checkout", "--", "."], check=False)


def commit_phase(files, message):
    run(["git", "add", *sorted(files)])
    run(["git", "commit", "-m", message])


def run_verify_gate(log_name):
    chunks = []
    ok = True
    for step in VERIFY_STEPS:
        result = subprocess.run(step, cwd=REPO_ROOT, capture_output=True, text=True)
        chunks.append(f"$ {' '.join(step)}\n{result.stdout}\n{result.stderr}\n")
        if result.returncode != 0:
            ok = False
            break
    (ARTIFACTS_DIR / log_name).write_text("\n".join(chunks), encoding="utf-8")
    return ok


def open_failure_issue(title, body):
    body_path = ARTIFACTS_DIR / "failure_issue_body.md"
    body_path.write_text(body, encoding="utf-8")
    try:
        run(["gh", "label", "create", "tech-debt", "--color", "B60205",
             "--description", "Automated tech-debt scan finding"], check=False)
        run(["gh", "issue", "create", "--title", title, "--label", "tech-debt",
             "--body-file", str(body_path)])
    except RuntimeError as exc:
        log(f"failed to open failure issue: {exc}")


def build_pr_body(before_summary, after_summary, committed, skipped, out_of_scope):
    lines = ["# Autonomous Tech Debt Refactor", "",
             "🤖 This PR was opened autonomously overnight by the tech-debt refactor "
             "pipeline. It has passed typecheck, tests, and build after every phase, "
             "but it still needs human review before merging — nothing here auto-merges.",
             ""]

    lines.append("## Phases committed")
    if committed:
        lines.append("")
        lines.append("| Phase | Category | Files |")
        lines.append("|---|---|---|")
        for c in committed:
            lines.append(f"| {c['id']} | `{c['category']}` | {len(c['files'])} |")
    else:
        lines.append("\nNone.")

    if skipped:
        lines.append("\n## Phases skipped")
        lines.append("")
        lines.append("| Phase | Category | Reason |")
        lines.append("|---|---|---|")
        for s in skipped:
            lines.append(f"| {s['id']} | `{s['category']}` | {s['reason']} |")

    if out_of_scope:
        lines.append("\n## Left for a human")
        lines.append("")
        lines.append("These findings need judgment the pipeline doesn't have and were "
                      "deliberately left untouched:")
        lines.append("")
        for item in out_of_scope:
            lines.append(f"- `{item.get('file')}:{item.get('line')}` — {item.get('reason')}")

    if before_summary is not None:
        lines.append("\n## Debt counts")
        lines.append("")
        lines.append("| Metric | Before | After |")
        lines.append("|---|---|---|")
        after_display = after_summary if after_summary is not None else "n/a"
        for key in ("total_issues", "critical", "warning", "info"):
            after_val = after_summary.get(key) if after_summary else "n/a"
            lines.append(f"| {key} | {before_summary.get(key, 'n/a')} | {after_val} |")

    lines.append("\n---\n*Verification: `npm run typecheck && npm test && npm run build` "
                  "passed after every committed phase and once more on the final branch.*")
    return "\n".join(lines) + "\n"


def main():
    status = git_status()
    if status:
        log(f"working tree not clean at start, aborting: {status}")
        write_summary("## ❌ Autonomous refactor aborted\n\nWorking tree was not clean at start.")
        return 1

    run(["git", "checkout", "-b", BRANCH_NAME])

    log("running before-scan")
    scan_prompt = (PROMPTS_DIR / "debt-scan.md").read_text(encoding="utf-8")
    scan_output = run_claude(
        scan_prompt, SCAN_MODEL, 20,
        "Read,Grep,Glob,Bash(tsc --noEmit:*),Bash(npx tsc --noEmit:*)",
        "scan_before.log",
    )
    if scan_output is None:
        write_summary("## ❌ Autonomous refactor aborted\n\nThe before-scan step failed. See workflow artifacts for logs.")
        return 1
    issue_body_before, summary_before = split_scan_output(scan_output)
    if summary_before is None:
        write_summary("## ❌ Autonomous refactor aborted\n\nCould not parse the before-scan output.")
        return 1
    (ARTIFACTS_DIR / "scan_before.md").write_text(issue_body_before, encoding="utf-8")
    (ARTIFACTS_DIR / "scan_before.json").write_text(json.dumps(summary_before, indent=2), encoding="utf-8")

    if summary_before.get("total_issues", 0) == 0:
        write_summary("## ✅ Autonomous refactor — nothing found\n\nThe before-scan found zero issues. No plan or PR was created.")
        return 0

    log("running plan")
    plan_prompt = (PROMPTS_DIR / "debt-plan.md").read_text(encoding="utf-8") + issue_body_before
    plan_output = run_claude(plan_prompt, EDIT_MODEL, 25, "Read,Grep,Glob", "plan.log")
    if plan_output is None:
        write_summary("## ❌ Autonomous refactor aborted\n\nThe plan step failed. See workflow artifacts for logs.")
        return 1
    try:
        plan = extract_json_block(plan_output)
    except (json.JSONDecodeError, AttributeError) as exc:
        write_summary(f"## ❌ Autonomous refactor aborted\n\nCould not parse the plan JSON: {exc}")
        return 1
    (ARTIFACTS_DIR / "plan.json").write_text(json.dumps(plan, indent=2), encoding="utf-8")

    phases = plan.get("phases", [])
    out_of_scope = plan.get("out_of_scope", [])

    if not phases:
        write_summary(
            "## ✅ Autonomous refactor — nothing safe to fix tonight\n\n"
            f"Before-scan found **{summary_before.get('total_issues', 0)}** issues "
            f"({summary_before.get('critical', 0)} critical), but none were eligible for "
            f"automated fixes. {len(out_of_scope)} item(s) left for human review."
        )
        return 0

    exec_prompt_template = (PROMPTS_DIR / "debt-execute-phase.md").read_text(encoding="utf-8")
    committed, skipped = [], []

    for phase in phases:
        phase_id, category = phase["id"], phase["category"]
        log(f"executing phase {phase_id} ({category})")

        pre_status = git_status()
        if pre_status:
            log(f"tree not clean before phase {phase_id}, reverting stray state: {pre_status}")
            revert_working_tree()

        prompt = exec_prompt_template + "\n\n```json\n" + json.dumps(phase, indent=2) + "\n```\n"
        exec_output = run_claude(prompt, EDIT_MODEL, 15, "Read,Grep,Glob,Edit", f"phase_{phase_id}.log")
        if exec_output is None:
            skipped.append({"id": phase_id, "category": category, "reason": "execution step failed or timed out"})
            revert_working_tree()
            continue

        changed = set(git_status().keys())
        if not changed:
            skipped.append({"id": phase_id, "category": category, "reason": "model made no changes"})
            continue

        allowed = set(phase.get("files", []))
        if not changed <= allowed:
            skipped.append({
                "id": phase_id, "category": category,
                "reason": f"touched out-of-scope files: {sorted(changed - allowed)}",
            })
            revert_working_tree()
            continue

        if not run_verify_gate(f"phase_{phase_id}_verify.log"):
            skipped.append({"id": phase_id, "category": category, "reason": "failed typecheck/test/build"})
            revert_working_tree()
            continue

        commit_phase(changed, f"tech-debt: {category} (automated phase {phase_id})")
        committed.append({"id": phase_id, "category": category, "files": sorted(changed)})
        log(f"phase {phase_id} committed ({len(changed)} file(s))")

    if not committed:
        write_summary(
            "## ✅ Autonomous refactor — no phase survived verification\n\n"
            f"{len(phases)} phase(s) were attempted, {len(skipped)} skipped. "
            "No branch was pushed and no PR was opened. See workflow artifacts for per-phase logs."
        )
        return 0

    log("running final verification gate")
    if not run_verify_gate("final_verify.log"):
        open_failure_issue(
            f"Autonomous refactor run failed final verification ({TODAY})",
            "The per-phase verification gates all passed individually, but the final "
            "combined verification failed. No PR was opened. See workflow artifacts "
            f"(run {RUN_ID}) for logs.",
        )
        write_summary("## ❌ Autonomous refactor — final verification failed\n\nNo PR was opened; a failure issue was filed instead.")
        return 1

    summary_after = None
    log("running after-scan (best effort)")
    try:
        after_output = run_claude(
            scan_prompt, SCAN_MODEL, 20,
            "Read,Grep,Glob,Bash(tsc --noEmit:*),Bash(npx tsc --noEmit:*)",
            "scan_after.log",
        )
        if after_output is not None:
            _, summary_after = split_scan_output(after_output)
    except Exception as exc:  # best-effort only, never fail the run over this
        log(f"after-scan failed, continuing without it: {exc}")

    pr_body = build_pr_body(summary_before, summary_after, committed, skipped, out_of_scope)
    pr_body_path = ARTIFACTS_DIR / "pr_body.md"
    pr_body_path.write_text(pr_body, encoding="utf-8")

    run(["git", "push", "-u", "origin", BRANCH_NAME])
    run(["gh", "label", "create", "tech-debt", "--color", "B60205",
         "--description", "Automated tech-debt scan finding"], check=False)
    run(["gh", "label", "create", "automated", "--color", "0E8A16",
         "--description", "Opened by an autonomous pipeline, needs human review"], check=False)
    run([
        "gh", "pr", "create",
        "--title", f"Tech Debt Auto-Refactor {TODAY} — {len(committed)} phase(s)",
        "--label", "tech-debt", "--label", "automated",
        "--body-file", str(pr_body_path),
    ])

    write_summary(
        f"## ✅ Autonomous refactor — PR opened\n\n"
        f"Branch `{BRANCH_NAME}`, {len(committed)} phase(s) committed, {len(skipped)} skipped. "
        "Needs human review before merge."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
