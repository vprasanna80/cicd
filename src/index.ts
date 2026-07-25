import { registerUser, listUsers } from './services/userService';
import { processPayment } from './services/paymentService';

/**
 * Application entry point. Registers a demo user and processes a demo payment.
 *
 * @returns void
 */
export function main(): void {
  registerUser('Ada Lovelace', 'ada@example.com');
  processPayment(500, 'USD');
  console.log(listUsers());
}

main();
