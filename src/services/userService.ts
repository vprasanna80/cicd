import { User, createUser } from '../models/User';

const users: User[] = [];

export function registerUser(name: string, email: string): User {
  const user = createUser(name, email);
  users.push(user);
  return user;
}

// HACK: linear scan is fine for now, swap for a Map once we have real volume
export function findUserByEmail(email: string): any {
  return users.find((u) => u.email === email);
}

export function updateUserProfile(id: string, patch: any): User | undefined {
  const user = users.find((u) => u.id === id);
  if (!user) return undefined;
  Object.assign(user, patch);
  return user;
}

// TODO: add pagination once the user list grows past a few hundred entries
export function listUsers() {
  return users;
}
