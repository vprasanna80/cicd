# Tech Debt Refactor Plan

You are turning a tech-debt scan report into a bounded, ordered refactor
plan for a fully autonomous overnight pipeline. **You do not fix anything
in this step** — you only decide what is safe to fix automatically and
group it into phases. A separate step executes each phase, and a human
still reviews the resulting pull request before it merges, but the
execution itself runs unattended, so be conservative: when in doubt, defer
to a human by putting the finding in `out_of_scope` instead of a phase.

Do not edit, create, or delete any files. Use `Read`, `Grep`, and `Glob`
only, to inspect the actual code behind a finding before deciding whether
it's safe to automate — the scan report gives you locations, not enough
context by itself to judge safety.

The scan report (Markdown, produced by `debt-scan.md`) is appended below
this prompt under `## Scan report input`. Treat every finding in it as the
full set of candidate work; do not go looking for additional debt beyond
what it already found.

## 1. What is safe to automate

Only these four categories may ever appear in a `phases` entry:

- **`unused_imports`** — every unused-import finding from the scan report.
  Always safe: removing a symbol nothing references cannot change
  behavior. `tsc --noEmit` after the edit is the ground truth check.
- **`missing_jsdoc`** — every "missing JSDoc" finding. Always safe: adding
  a doc comment never changes behavior. Base the comment on the function's
  actual parameters and return type/behavior (read the file — don't
  invent behavior it doesn't have).
- **`any_to_type`** — an `any` usage finding qualifies **only if** you can
  determine a concrete, unambiguous type from how the value is actually
  used in that file (e.g. a function that only ever calls `.reduce`,
  `.map`, or arithmetic on a parameter is safely `number[]`; a parameter
  passed straight into `Object.assign` on a typed object with no other use
  is safely `Partial<TheType>`). If the correct type requires guessing at
  intent, touches a public API boundary in a way that could ripple beyond
  the file, or the value is used in more than one incompatible way, it is
  **not** unambiguous — send it to `out_of_scope` instead.
- **`add_tests`** — every "untested file" finding. Always safe in the sense
  that it's purely additive (a new `*.test.ts` file); write tests that
  cover the file's actual exported behavior as it exists today. Do not
  change the source file itself in this phase — if a source change seems
  needed to make something testable, that's a sign the file needs a human,
  not an autonomous test.

Everything else is **never** eligible for a phase, regardless of how
simple it looks:

- Every TODO / FIXME / HACK comment. These almost always encode a real
  product or architecture decision (e.g. "stubbed until the ledger service
  is ready", "swap for a Map once we have real volume") — resolving them
  requires judgment this pipeline doesn't have. Put each one in
  `out_of_scope` with a one-line reason based on what the comment actually
  says.
- Any `any` usage you couldn't classify as unambiguous under the rule
  above.

## 2. Phase grouping

Group eligible findings into up to four phases, in this fixed order
(omit a phase entirely if it would have zero findings — do not emit an
empty phase):

1. `unused_imports`
2. `missing_jsdoc`
3. `any_to_type`
4. `add_tests`

This order matters: imports and JSDoc are inert cleanup, `any_to_type`
should land before tests are written so the tests target the final typed
signatures, and `add_tests` goes last since it depends on every prior
phase's output.

Each phase's `files` list must be exactly the set of files touched by that
phase's `findings` — the execution step will treat any file edited outside
this list as a violation and revert the whole phase, so don't scope it
loosely.

## 3. Output

Output **only** a single fenced JSON block, nothing else — no prose before
or after it. Shape:

```json
{
  "phases": [
    {
      "id": 1,
      "category": "unused_imports",
      "files": ["src/relative/path.ts"],
      "findings": [
        {"file": "src/relative/path.ts", "line": 12, "detail": "'foo' is declared but its value is never read."}
      ]
    }
  ],
  "out_of_scope": [
    {
      "file": "src/relative/path.ts",
      "line": 26,
      "category": "hack_comment",
      "reason": "one-line reason grounded in the actual comment/code, not a generic disclaimer"
    }
  ]
}
```

Rules for the output:
- `id` starts at 1 and increments in the fixed phase order above (an
  omitted phase does not consume an id — e.g. if there are no unused
  imports, the first emitted phase still starts at whatever its position
  in the fixed order would imply is fine, but ids must stay in ascending
  order matching phase order).
- For `any_to_type` findings, include a `suggested_type` field with the
  concrete type you determined and a short `detail` explaining why it's
  unambiguous.
- Every finding from the scan report must end up in exactly one place:
  a `phases[].findings` entry, or an `out_of_scope` entry. None may be
  dropped silently.
- If literally nothing is eligible, output `{"phases": [], "out_of_scope": [...]}`
  with every finding accounted for in `out_of_scope`.

## Scan report input
