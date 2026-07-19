import { capitalize, truncate } from './string';

describe('capitalize', () => {
  it('capitalizes the first letter', () => {
    expect(capitalize('hello')).toBe('Hello');
  });

  it('handles empty strings', () => {
    expect(capitalize('')).toBe('');
  });
});

describe('truncate', () => {
  it('truncates long strings', () => {
    expect(truncate('hello world', 5)).toBe('hello...');
  });

  it('leaves short strings untouched', () => {
    expect(truncate('hi', 5)).toBe('hi');
  });
});
