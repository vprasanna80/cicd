/**
 * Represents a registered user of the system.
 */
export interface User {
  id: string;
  name: string;
  email: string;
  createdAt: Date;
}

/**
 * Creates a new User object with a generated id and timestamp.
 *
 * @param name - The user's display name.
 * @param email - The user's email address.
 * @returns A fully populated User object.
 */
export function createUser(name: string, email: string): User {
  return {
    id: Math.random().toString(36).slice(2),
    name,
    email,
    createdAt: new Date(),
  };
}
