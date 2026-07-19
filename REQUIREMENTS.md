# Automated Tech Debt Scanning System — Requirements & Design

## Overview

This system runs a weekly, automated audit of the codebase's technical debt
using Claude Code inside a GitHub Actions workflow. It scans for five
categories of debt, classifies each finding by severity, and either opens a
labeled GitHub issue (when critical debt is found) or records a clean result
in the workflow's job summary. The goal is to surface debt trends over time
without requiring an engineer to manually audit the codebase.

## Components

| File | Purpose |
|---|---|
| `.claude/prompts/debt-scan.md` | The Claude Code prompt that performs the scan. Read-only: uses `Grep`, `Glob`, and a scoped `Bash(tsc --noEmit)` call. Produces a Markdown issue body followed by a fenced JSON summary. |
| `.github/workflows/claude-debt-scan.yml` | The GitHub Actions workflow that installs Claude Code, runs the prompt on a schedule (or on demand), parses its output, and conditionally opens an issue. |
| `src/**` | A small sample TypeScript project (models, services, utils) seeded with realistic, intentional debt, used to validate the scan end-to-end. |

## Scan categories and severity

The prompt evaluates five categories and buckets every individual finding
into exactly one severity:

- Critical: every `any` type usage, plus every untested source file that also
  contains an `any` usage (the highest-risk combination of low type-safety
  and no test coverage).
- Warning: every TODO / FIXME / HACK comment, plus untested files that do
  *not* use `any`.
- Info: exported functions missing JSDoc, and unused imports (detected via
  `tsc --noEmit` diagnostics `TS6133` / `TS6192`).

The prompt outputs a summary table, one checkbox per finding (grouped by
severity, with a detail sub-section per category), a rough fix-time estimate,
and a trailing JSON block (`total_issues`, `critical`, `warning`, `info`,
per-category counts, and `estimated_fix_hours`) that the workflow parses
programmatically to decide whether to open an issue.

## Workflow behavior

- Triggers: `schedule` (`0 3 * * 1` — every Monday 03:00 UTC) and
  `workflow_dispatch` for manual runs.
- Cost control: pinned to `claude-haiku-4-5-20251001` with `--max-turns 20`
  and an explicit `--allowedTools` allowlist (`Read`, `Grep`, `Glob`, and a
  scoped `tsc --noEmit` bash command) so the run stays read-only, bounded,
  and cheap.
- After the prompt runs, a small Python step splits its output on the
  ` ```json ` fence into `issue_body.md` (everything above the fence) and
  `scan_summary.json` (the parsed JSON).
- If `critical != 0`: the workflow ensures a `tech-debt` label exists, then
  opens a new issue via `gh issue create` with that label and the Markdown
  body.
- If `critical == 0`: no issue is created; a "no critical issues" note plus
  the total/critical counts are written to `$GITHUB_STEP_SUMMARY` instead.
- Scan artifacts (raw output, JSON summary, issue body) are uploaded as a
  workflow artifact on every run, critical or not, for auditability.

### Required repository setup (not yet done — needs the repo owner)

- Add an `ANTHROPIC_API_KEY` repository secret so `claude` can authenticate.
- Ensure the default `GITHUB_TOKEN` has `issues: write` (already declared in
  the workflow's `permissions:` block; no manual step needed on modern repos).
- `npm ci` is attempted before installing Claude Code so the unused-imports
  check has real `node_modules` to type-check against; if the project has no
  lockfile yet or dependencies fail to install, that step is
  `continue-on-error: true` and the prompt is instructed to skip the
  unused-imports category gracefully rather than fail the whole scan.

## Manual test results

Two constraints in this sandbox meant the workflow could not be executed as
a live GitHub Actions run:

1. No `gh` CLI or GitHub credentials are available in this environment, so a
   repository/workflow_dispatch run and a real issue creation could not be
   triggered here.
2. No outbound network access to the npm registry, so `typescript` could not
   be installed to run a literal `tsc --noEmit` for the unused-imports
   check.

Per your direction, the scan was instead simulated locally: the same
`Grep`/`Glob` steps described in `debt-scan.md` were run for real against the
sample project in `src/`, and the unused-import check was approximated with
a static per-file usage check (each import symbol checked for a later
reference in the same file) standing in for `tsc`'s `TS6133` diagnostic. In
a real GitHub Actions run, with network access and Claude Code available,
this last category would come from actual `tsc --noEmit` output instead.

### Results against the sample project

| Category | Count | Severity |
|---|---|---|
| `any` type usages | 9 | Critical |
| Untested files (with `any`) | 3 | Critical |
| Untested files (without `any`) | 1 | Warning |
| TODO / FIXME / HACK comments | 5 | Warning |
| Missing JSDoc on exports | 9 | Info |
| Unused imports | 2 | Info |
| **Total** | **29** | — |

JSON summary produced:

```json
{
  "total_issues": 29,
  "critical": 12,
  "warning": 6,
  "info": 11,
  "categories": {
    "any_usages": 9,
    "untested_files": 4,
    "todo_fixme_hack": 5,
    "missing_jsdoc": 9,
    "unused_imports": 2
  },
  "estimated_fix_hours": 6.5
}
```

Because `critical` (12) is non-zero, the workflow's logic dictates that a
GitHub issue titled `Tech Debt Scan 2026-07-19 — 12 critical item(s)` would
be opened with the `tech-debt` label and the full Markdown report as its
body. That exact report is saved as `issue_body.md` alongside this file so
you can see precisely what would have been posted. The raw combined output
is in `scan_output.md`, and the machine-readable summary is in
`scan_summary.json`.

## Known limitations and follow-ups

- The unused-imports category currently relies on a real `tsc --noEmit` run
  inside GitHub Actions (where network access is available); it was only
  approximated here. Recommend running the workflow once for real after the
  `ANTHROPIC_API_KEY` secret is added, and spot-checking that its unused
  import findings match expectations.
- The `any` type detection regex is intentionally simple
  (`:\s*any\b|as\s+any\b|<any>|any\[\]`) and will miss more exotic patterns
  such as `any` inside generics passed as type arguments elsewhere in a line,
  or `any` reached through a type alias. Treat it as a useful heuristic, not
  a complete type-safety audit.
- The JSDoc check only verifies a `/** ... */` block sits immediately above
  an export; it does not check that the JSDoc is complete (e.g., has
  `@param` for every parameter) or accurate.
- Consider adding a `dry-run` input to `workflow_dispatch` if you want to be
  able to preview a report without ever opening an issue.

## Autonomous overnight refactor pipeline

Built on top of the scanner above: a nightly pipeline that scans, plans a
bounded refactor, executes it in phases, and opens a **pull request** with
the result — no human in the loop until review. It never merges anything
itself; opening the PR is the last autonomous step.

### Components

| File | Purpose |
|---|---|
| `.claude/prompts/debt-plan.md` | Read-only (`Read`/`Grep`/`Glob`). Takes the scan's Markdown report as input and produces a JSON refactor plan: ordered phases of auto-fixable findings, plus an `out_of_scope` list of findings that need a human. |
| `.claude/prompts/debt-execute-phase.md` | Scoped to `Read`/`Grep`/`Glob`/`Edit`. Given one phase's JSON, makes only the edits for that phase's findings in that phase's files. No `Bash`, no git — it cannot verify or commit anything itself. |
| `scripts/autonomous_refactor.py` | Orchestrates the whole run: invokes the scan, the plan, loops over phases (execute → external scope check → external build/typecheck/test gate → commit or revert), does a final verification pass, and pushes/opens the PR (or files a failure issue). Owns every git/gh/npm call — Claude never runs them directly. |
| `.github/workflows/claude-autonomous-refactor.yml` | Nightly (`0 4 * * *`) + `workflow_dispatch`. Installs dependencies, Claude Code, and the GitHub CLI, runs the orchestration script, uploads everything under `$RUNNER_TEMP/autonomous-refactor` as a workflow artifact. |

The existing `.claude/prompts/debt-scan.md` is reused unchanged for both the
"before" scan (feeds the plan) and a best-effort "after" scan (feeds the
PR's before/after debt-count table).

### What gets fixed autonomously — and what doesn't

Only four categories are ever eligible for a phase, and `debt-plan.md` is
instructed to be conservative — anything ambiguous goes to `out_of_scope`
instead:

- `unused_imports` — always safe, removal only.
- `missing_jsdoc` — always safe, purely additive documentation.
- `any_to_type` — only when the correct type is unambiguous from how the
  value is actually used in that file; otherwise deferred.
- `add_tests` — new `*.test.ts` files covering existing behavior; never
  modifies the source file it's testing.

TODO/FIXME/HACK comments and any ambiguous `any` usage are **never**
auto-resolved — they're surfaced in the PR body under "Left for a human"
with a reason, since they typically encode a real product or architecture
decision (e.g. `paymentService.ts`'s `refundPayment` being stubbed pending
a ledger service) rather than a mechanical fix.

Phases run in a fixed order — `unused_imports` → `missing_jsdoc` →
`any_to_type` → `add_tests` — so tests are always written against the
code's final typed shape, and a phase is skipped entirely (not emitted)
if it has zero eligible findings.

### Safety rails

- Planning is read-only; execution can only `Edit`, never run `Bash`/git.
- Every phase's file scope is checked externally via `git status`, not
  trusted from the prompt — touching anything outside the phase's declared
  `files` reverts the whole phase.
- Verification is always an external command
  (`npm run typecheck && npm test && npm run build`), never a model
  self-report. A phase that fails it is fully reverted (tracked files
  `git checkout`'d back, new untracked files deleted) and the pipeline
  moves on to the next phase rather than aborting the run.
- A second, final verification pass runs on the accumulated branch before
  anything is pushed, as defense in depth beyond the per-phase gates.
- New branch per run (`tech-debt/auto-refactor-<date>-<run_id>`); never
  pushes to the default branch, never force-pushes, never auto-merges.
- Bounded `--max-turns` and pinned models per Claude invocation
  (`claude-haiku-4-5-20251001` for scanning, `claude-sonnet-5` for planning
  and editing — code changes warrant a stronger model than text scanning
  does), a 60-minute job timeout, and a `concurrency` group so overlapping
  nightly runs can't race each other.
- If nothing is safe to fix, or every phase fails verification, no branch
  is pushed and no PR opens — the run just logs a summary. If the *final*
  verification pass somehow fails despite every phase passing individually,
  no PR opens either; a failure issue is filed instead so nothing broken is
  ever proposed for review.

### Required repository setup (same as the scanner, not yet done)

- `ANTHROPIC_API_KEY` repository secret.
- `contents: write`, `issues: write`, `pull-requests: write` are already
  declared in the workflow's `permissions:` block.

### Manual test results

This pipeline could not be run end-to-end in this sandbox, for the same
reasons noted under the scanner above, plus one more specific to this
system: this working directory is not a git repository, and the pipeline's
entire safety model (branch, commit-per-phase, revert-on-failure, push,
PR) depends on git/`gh` operating against a real GitHub remote. What was
verified locally instead:

- `python -m py_compile scripts/autonomous_refactor.py` — passes.
- `npm run typecheck`, `npm test`, and `npm run build` were run against the
  current `src/` to confirm the exact commands the verification gate
  depends on actually pass today.
- The whitelist rules in `debt-plan.md` were traced by hand against the
  real findings already catalogued in the scanner's manual test results
  above (9 `any` usages, 4 untested files, 5 TODO/FIXME/HACK, 9 missing
  JSDoc, 2 unused imports). Expected grouping: both unused-import findings
  and all 9 missing-JSDoc findings are eligible outright; `sum(values: any[])`
  and `average(values: any)` in `math.ts` have an unambiguous `number[]`
  type from their usage; `refundPayment(payment: any)`,
  `findUserByEmail(...): any`, and `updateUserProfile(id, patch: any)` are
  judgment calls the plan prompt is instructed to push to `out_of_scope`
  rather than guess at; all 5 TODO/FIXME/HACK comments go to
  `out_of_scope`; the 4 untested files become one `add_tests` phase.

Recommend the repo owner do a first live `workflow_dispatch` run once
`ANTHROPIC_API_KEY` is set, and spot-check: that reverted phases actually
leave the working tree clean, that the PR body's before/after counts look
right, and that the `out_of_scope` reasons in the PR are genuinely
judgment calls rather than things the plan prompt should have handled.

### Known limitations and follow-ups

- `debt-plan.md`'s judgment about what counts as an "unambiguous" type for
  `any_to_type` is inherently fuzzy — treat early PRs from this pipeline as
  a chance to tighten that prompt's rules, not as ground truth.
- The per-phase scope/revert logic in `scripts/autonomous_refactor.py`
  assumes no renames and doesn't quote-unescape unusual filenames from
  `git status --porcelain`; fine for typical source trees, but worth
  hardening (`git status --porcelain -z`) if the repo ever has paths with
  spaces or special characters.
- There's no cap today on how many nights in a row the pipeline can open a
  PR before an earlier one is merged — consider having it check for an
  already-open `automated` PR and skip (or stack onto it) rather than
  opening a second one.
