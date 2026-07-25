import { User, createUser } from '../models/User';

const users: User[] = [];

/**
 * Creates a new user and adds it to the in-memory user list.
 *
 * @param name - The user's display name.
 * @param email - The user's email address.
 * @returns The newly created user.
 */
export function registerUser(name: string, email: string): User {
  const user = createUser(name, email);
  users.push(user);
  return user;
}

// HACK: linear scan is fine for now, swap for a Map once we have real volume
/**
 * Finds a user by email address.
 *
 * @param email - The email address to search for.
 * @returns The matching user, or `undefined` if none is found.
 */
export function findUserByEmail(email: string): any {
  return users.find((u) => u.email === email);
}

/**
 * Applies a partial update to an existing user's profile.
 *
 * @param id - The id of the user to update.
 * @param patch - The properties to merge onto the user.
 * @returns The updated user, or `undefined` if no user with `id` exists.
 */
export function updateUserProfile(id: string, patch: any): User | undefined {
  const user = users.find((u) => u.id === id);
  if (!user) return undefined;
  Object.assign(user, patch);
  return user;
}

// TODO: add pagination once the user list grows past a few hundred entries
/**
 * Returns all registered users.
 *
 * @returns The in-memory array of all users.
 */
export function listUsers() {
  return users;
}
