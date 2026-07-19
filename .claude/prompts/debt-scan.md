# Tech Debt Scan

You are running an automated, read-only technical debt audit of this TypeScript
repository. Do not modify any files. Use `Grep`, `Glob`, and `Bash` (for
`tsc --noEmit` only) to gather evidence, then produce the two outputs
specified at the end of this prompt.

Work only within the `src/` directory tree (and its subdirectories) unless a
step below says otherwise. Ignore `node_modules/`, `dist/`, `build/`, and any
`.d.ts` files.

## 1. Scan categories

### a) `any` type usages — Critical
- Use `Grep` with a pattern that matches real type annotations, not the word
  "any" inside comments or strings. A good starting pattern is:
  `:\s*any\b|as\s+any\b|<any>|any\[\]`
- Search glob `src/**/*.ts`, excluding `src/**/*.test.ts`.
- For every match, record `path:line` and the trimmed line of code.
- Count the total number of matches (count occurrences, not files).

### b) Exported functions missing JSDoc — Info
- Use `Grep` to find exported function declarations and arrow functions:
  pattern like `^export function \w+|^export const \w+\s*=\s*\(`.
- Search glob `src/**/*.ts`, excluding `*.test.ts`.
- For each match, check whether the line(s) immediately preceding it contain a
  `/** ... */` JSDoc block. If not, flag it as undocumented.
- Record `path:line` and the function signature for every undocumented
  export.
- Count the total number of undocumented exported functions.

### c) TODO / FIXME / HACK comments — Warning
- Use `Grep` with pattern `TODO|FIXME|HACK` (case-sensitive, matching the
  common comment-tag convention) across `src/**/*.ts`.
- For each match, record `path:line` and the **full comment text** (not just
  the tag).
- Count the total number of such comments.

### d) Test coverage gaps — Critical (when combined with exported code)
- Use `Glob` to list all `src/**/*.ts` files, excluding `*.test.ts` and files
  named `index.ts` (entry points are typically covered by integration tests,
  not unit tests).
- For each remaining file `foo.ts`, check whether a sibling `foo.test.ts` (or
  `foo.spec.ts`) exists.
- Any file that exports at least one function/class/const AND has no
  corresponding test file is a coverage gap. Record the file path.
- Count the total number of files with coverage gaps. Separately note how
  many of those files also contain `any` types found in step (a) — these
  overlap cases (untested + uses `any`) are the ones that drive the
  **Critical** severity bucket, since untested loosely-typed code is the
  highest-risk combination.

### e) Unused imports — Info
- Run `tsc --noEmit` from the repository root (assume dependencies are
  already installed; if the command fails because dependencies are missing,
  note that in the output and skip this category rather than failing the
  whole scan).
- Parse the compiler output for `TS6133` ("'X' is declared but its value is
  never read") and `TS6192` ("All imports in import declaration are unused")
  diagnostics.
- Record `path:line` and the unused symbol name for each diagnostic.
- Count the total number of unused-import diagnostics.

## 2. Severity classification

Classify every individual finding into exactly one bucket:

- **Critical**: every `any` type usage (a), and every test coverage gap file
  that also uses `any` (overlap of (a) and (d)).
- **Warning**: every TODO / FIXME / HACK comment (c), and any test coverage
  gap file that does **not** use `any` (d without overlap).
- **Info**: every undocumented exported function (b), and every unused
  import (e).

## 3. Output 1 — GitHub-flavored Markdown issue body

Produce a Markdown document with this structure:

```markdown
# Tech Debt Scan Report — <YYYY-MM-DD>

## Summary

| Category | Count | Severity |
|---|---|---|
| `any` type usages | N | 🔴 Critical |
| Untested files (with `any`) | N | 🔴 Critical |
| Untested files (without `any`) | N | 🟡 Warning |
| TODO / FIXME / HACK comments | N | 🟡 Warning |
| Missing JSDoc on exports | N | 🔵 Info |
| Unused imports | N | 🔵 Info |
| **Total** | **N** | — |

**Estimated total fix time:** ~X hours (see estimate methodology below)

## 🔴 Critical

### `any` type usages
- [ ] `path/to/file.ts:12` — `function foo(x: any): any {`
- [ ] ...

### Untested files using `any`
- [ ] `path/to/file.ts` — exports `foo`, `bar`; no `file.test.ts` found
- [ ] ...

## 🟡 Warning

### TODO / FIXME / HACK comments
- [ ] `path/to/file.ts:5` — `// TODO: replace this with a proper stats library once we pick one`
- [ ] ...

### Untested files (no `any`)
- [ ] `path/to/file.ts` — exports `foo`; no test file found
- [ ] ...

## 🔵 Info

### Exported functions missing JSDoc
- [ ] `path/to/file.ts:20` — `export function foo(...)`
- [ ] ...

### Unused imports
- [ ] `path/to/file.ts:2` — `'bar' is declared but its value is never read.`
- [ ] ...

---
*Generated automatically by the weekly tech-debt scan. Check off items as you fix them.*
```

Fix-time estimate methodology (use these per-item defaults unless the code
suggests otherwise, then sum and round to the nearest half hour):
- `any` type usage: 15 min each (add a proper type)
- Untested file: 30 min each (write a basic unit test)
- TODO/FIXME/HACK: 20 min each (varies, but use this as a rough default)
- Missing JSDoc: 5 min each
- Unused import: 2 min each

## 4. Output 2 — JSON summary

After the Markdown report, output a fenced JSON code block with exactly this
shape (counts must match the Markdown summary table):

```json
{
  "total_issues": N,
  "critical": N,
  "warning": N,
  "info": N,
  "categories": {
    "any_usages": N,
    "untested_files": N,
    "todo_fixme_hack": N,
    "missing_jsdoc": N,
    "unused_imports": N
  },
  "estimated_fix_hours": N
}
```

Note: `total_issues = critical + warning + info`, and `critical` = (`any`
usages) + (untested files with `any`); `warning` = (TODO/FIXME/HACK) +
(untested files without `any`); `info` = (missing JSDoc) + (unused imports).
Do not double count a single untested-file-with-`any` in both the `any`
usages count and the untested-files count when computing `total_issues` —
each finding is counted once, in whichever bucket it was classified into
above.

## 5. Rules

- Do not edit, create, or delete any files in the repository.
- Do not invent findings — every row in the report must trace back to an
  actual `Grep`/`Glob`/`tsc` result.
- If a category has zero findings, still include it in the summary table
  with a count of 0 and omit its detail section (or state "None found").
- Keep the two outputs in the order specified above (Markdown first, then
  JSON) so the calling workflow can split on the ```json fence.
