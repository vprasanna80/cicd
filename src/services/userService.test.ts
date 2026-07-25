import { registerUser, findUserByEmail, updateUserProfile, listUsers } from './userService';

describe('registerUser', () => {
  it('creates a new user and adds it to the user list', () => {
    const user = registerUser('Grace Hopper', 'grace@example.com');
    expect(user.name).toBe('Grace Hopper');
    expect(user.email).toBe('grace@example.com');
    expect(listUsers()).toContain(user);
  });
});

describe('findUserByEmail', () => {
  it('finds a registered user by email', () => {
    const user = registerUser('Alan Turing', 'alan@example.com');
    expect(findUserByEmail('alan@example.com')).toEqual(user);
  });

  it('returns undefined when no user matches', () => {
    expect(findUserByEmail('nobody@example.com')).toBeUndefined();
  });
});

describe('updateUserProfile', () => {
  it('applies a partial update to an existing user', () => {
    const user = registerUser('Margaret Hamilton', 'margaret@example.com');
    const updated = updateUserProfile(user.id, { name: 'M. Hamilton' });
    expect(updated?.name).toBe('M. Hamilton');
    expect(updated?.email).toBe('margaret@example.com');
  });

  it('returns undefined when no user matches the id', () => {
    expect(updateUserProfile('nonexistent-id', { name: 'Nobody' })).toBeUndefined();
  });
});

describe('listUsers', () => {
  it('returns all registered users', () => {
    const before = listUsers().length;
    registerUser('New User', 'new-user@example.com');
    expect(listUsers().length).toBe(before + 1);
  });
});
