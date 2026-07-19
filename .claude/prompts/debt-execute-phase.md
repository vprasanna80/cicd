# Execute One Refactor Phase

You are executing exactly one phase of an autonomous overnight tech-debt
refactor. The phase to execute (its `category`, `files`, and `findings`)
is appended below this prompt under `## Phase input`, as a JSON object
with the same shape produced by `debt-plan.md`.

This is one step in a pipeline with external safety checks around you:
after you finish, a script diffs the working tree and **reverts everything
you did** if you touched any file outside this phase's `files` list, and
separately runs the real build/typecheck/test suite and reverts everything
if any of them fail. You don't need to (and can't) run those yourself —
just make the correct, narrowly-scoped edits and stop.

## Rules

1. **Only edit files listed in this phase's `files` array.** Do not touch
   any other file for any reason, even if you notice unrelated debt while
   you're in there — that belongs to a different phase or to
   `out_of_scope`, not to you right now.
2. **Only address the specific `findings` given for this phase.** Don't
   expand scope to nearby code that looks similar but wasn't flagged.
3. Make the smallest correct edit for each finding:
   - `unused_imports`: remove the unused import/specifier. If removing it
     leaves an import statement with no specifiers, remove the whole
     statement.
   - `missing_jsdoc`: add a `/** ... */` block immediately above the
     export, describing what the function actually does based on reading
     its body — include `@param` for each parameter and `@returns` (or
     `@returns void`) when the function returns a value.
   - `any_to_type`: replace `any` with the `suggested_type` from the
     finding (or an equally concrete type you derive from actually reading
     the code, if `suggested_type` is absent). Update only the type
     annotation — do not change runtime behavior.
   - `add_tests`: create a sibling `*.test.ts` file (matching this
     project's existing test file convention — check an existing
     `*.test.ts` file for style) covering the target file's actual
     exported behavior as it exists today. Do not modify the source file
     in this phase.
4. Do not run any build, test, or lint commands yourself — you have no
   `Bash` access in this phase, and verification happens externally after
   you're done.
5. Do not touch `package.json`, config files, or anything not explicitly
   listed in `files`.
6. When every finding for this phase has been addressed, stop. Do not
   continue looking for more work.

## Phase input
