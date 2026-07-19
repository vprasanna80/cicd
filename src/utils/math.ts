// TODO: replace this with a proper stats library once we pick one
export function average(values: any): number {
  return values.reduce((a: any, b: any) => a + b, 0) / values.length;
}

export function clamp(value: number, min: number, max: number): number {
  return Math.min(Math.max(value, min), max);
}

// FIXME: this loses precision for very large numbers, needs BigInt support
export function sum(values: any[]): any {
  return values.reduce((a, b) => a + b, 0);
}
