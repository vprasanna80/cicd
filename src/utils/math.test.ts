import { average, clamp, sum } from './math';

describe('average', () => {
  it('computes the arithmetic mean of a list of numbers', () => {
    expect(average([1, 2, 3, 4])).toBe(2.5);
  });

  it('returns the value itself for a single-element list', () => {
    expect(average([5])).toBe(5);
  });
});

describe('clamp', () => {
  it('returns the value when within range', () => {
    expect(clamp(5, 0, 10)).toBe(5);
  });

  it('returns the lower bound when value is below range', () => {
    expect(clamp(-5, 0, 10)).toBe(0);
  });

  it('returns the upper bound when value is above range', () => {
    expect(clamp(15, 0, 10)).toBe(10);
  });
});

describe('sum', () => {
  it('adds a list of numbers together', () => {
    expect(sum([1, 2, 3, 4])).toBe(10);
  });

  it('returns 0 for an empty list', () => {
    expect(sum([])).toBe(0);
  });
});
