# Tech Debt Scan Report — 2026-07-19

## Summary

| Category | Count | Severity |
|---|---|---|
| `any` type usages | 9 | 🔴 Critical |
| Untested files (with `any`) | 3 | 🔴 Critical |
| Untested files (without `any`) | 1 | 🟡 Warning |
| TODO / FIXME / HACK comments | 5 | 🟡 Warning |
| Missing JSDoc on exports | 9 | 🔵 Info |
| Unused imports | 2 | 🔵 Info |
| **Total** | **29** | — |

**Estimated total fix time:** ~6.5 hours

## 🔴 Critical

### `any` type usages (9 occurrences across 6 locations)
- [ ] `src/utils/math.ts:2` — `export function average(values: any): number {`
- [ ] `src/utils/math.ts:3` — `return values.reduce((a: any, b: any) => a + b, 0) / values.length;` (2 occurrences)
- [ ] `src/utils/math.ts:11` — `export function sum(values: any[]): any {` (2 occurrences)
- [ ] `src/services/userService.ts:12` — `export function findUserByEmail(email: string): any {`
- [ ] `src/services/userService.ts:16` — `export function updateUserProfile(id: string, patch: any): User | undefined {`
- [ ] `src/services/paymentService.ts:27` — `export function refundPayment(payment: any): any {` (2 occurrences)

### Untested files using `any`
- [ ] `src/utils/math.ts` — exports `average`, `clamp`, `sum`; no `math.test.ts` found; contains `any` usages
- [ ] `src/services/userService.ts` — exports `registerUser`, `findUserByEmail`, `updateUserProfile`, `listUsers`; no `userService.test.ts` found; contains `any` usages
- [ ] `src/services/paymentService.ts` — exports `processPayment`, `refundPayment`, `describePayment`; no `paymentService.test.ts` found; contains `any` usages

## 🟡 Warning

### TODO / FIXME / HACK comments
- [ ] `src/utils/math.ts:1` — `// TODO: replace this with a proper stats library once we pick one`
- [ ] `src/utils/math.ts:10` — `// FIXME: this loses precision for very large numbers, needs BigInt support`
- [ ] `src/services/userService.ts:11` — `// HACK: linear scan is fine for now, swap for a Map once we have real volume`
- [ ] `src/services/userService.ts:23` — `// TODO: add pagination once the user list grows past a few hundred entries`
- [ ] `src/services/paymentService.ts:26` — `// HACK: refund logic is stubbed until the ledger service is ready`

### Untested files (no `any`)
- [ ] `src/models/User.ts` — exports `User`, `createUser`; no `User.test.ts` found

## 🔵 Info

### Exported functions missing JSDoc (9)
- [ ] `src/utils/math.ts:2` — `export function average(values: any): number`
- [ ] `src/utils/math.ts:6` — `export function clamp(value: number, min: number, max: number): number`
- [ ] `src/utils/math.ts:11` — `export function sum(values: any[]): any`
- [ ] `src/services/userService.ts:5` — `export function registerUser(name: string, email: string): User`
- [ ] `src/services/userService.ts:12` — `export function findUserByEmail(email: string): any`
- [ ] `src/services/userService.ts:16` — `export function updateUserProfile(id: string, patch: any): User | undefined`
- [ ] `src/services/userService.ts:24` — `export function listUsers()`
- [ ] `src/services/paymentService.ts:27` — `export function refundPayment(payment: any): any`
- [ ] `src/services/paymentService.ts:31` — `export function describePayment(payment: Payment)`

### Unused imports (2)
- [ ] `src/index.ts:3` — `'truncate' is declared but its value is never read.`
- [ ] `src/services/paymentService.ts:1` — `'capitalize' is declared but its value is never read.`

---
*Generated automatically by the weekly tech-debt scan. Check off items as you fix them.*
