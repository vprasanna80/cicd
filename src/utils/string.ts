/**
 * Capitalizes the first letter of a string.
 *
 * @param value - The string to capitalize.
 * @returns The input string with its first character upper-cased.
 */
export function capitalize(value: string): string {
  if (value.length === 0) return value;
  return value.charAt(0).toUpperCase() + value.slice(1);
}

/**
 * Truncates a string to a maximum length, appending an ellipsis when truncated.
 *
 * @param value - The string to truncate.
 * @param maxLength - The maximum allowed length before truncation.
 * @returns The truncated string.
 */
export function truncate(value: string, maxLength: number): string {
  if (value.length <= maxLength) return value;
  return `${value.slice(0, maxLength)}...`;
}
