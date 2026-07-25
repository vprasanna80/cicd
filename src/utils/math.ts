// TODO: replace this with a proper stats library once we pick one
/**
 * Computes the arithmetic mean of a list of numbers.
 *
 * @param values - The numbers to average.
 * @returns The sum of `values` divided by their count.
 */
export function average(values: any): number {
  return values.reduce((a: any, b: any) => a + b, 0) / values.length;
}

/**
 * Restricts a value to lie within an inclusive range.
 *
 * @param value - The number to clamp.
 * @param min - The lower bound of the range.
 * @param max - The upper bound of the range.
 * @returns `value` if within range, otherwise the nearest bound.
 */
export function clamp(value: number, min: number, max: number): number {
  return Math.min(Math.max(value, min), max);
}

// FIXME: this loses precision for very large numbers, needs BigInt support
/**
 * Sums a list of numbers.
 *
 * @param values - The numbers to add together.
 * @returns The total of all values in `values`.
 */
export function sum(values: any[]): any {
  return values.reduce((a, b) => a + b, 0);
}
