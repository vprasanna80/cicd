import { createUser } from './User';

describe('createUser', () => {
  it('creates a user with the given name and email', () => {
    const user = createUser('Ada Lovelace', 'ada@example.com');
    expect(user.name).toBe('Ada Lovelace');
    expect(user.email).toBe('ada@example.com');
  });

  it('generates an id for the new user', () => {
    const user = createUser('Ada Lovelace', 'ada@example.com');
    expect(typeof user.id).toBe('string');
    expect(user.id.length).toBeGreaterThan(0);
  });

  it('sets createdAt to a Date', () => {
    const user = createUser('Ada Lovelace', 'ada@example.com');
    expect(user.createdAt).toBeInstanceOf(Date);
  });

  it('generates different ids for different users', () => {
    const a = createUser('A', 'a@example.com');
    const b = createUser('B', 'b@example.com');
    expect(a.id).not.toBe(b.id);
  });
});
