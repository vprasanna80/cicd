import { capitalize } from '../utils/string';
import { clamp } from '../utils/math';

interface Payment {
  id: string;
  amount: number;
  currency: string;
}

/**
 * Processes a payment and returns a confirmation record.
 *
 * @param amount - The payment amount in the smallest currency unit.
 * @param currency - The ISO currency code.
 * @returns A confirmation record for the processed payment.
 */
export function processPayment(amount: number, currency: string): Payment {
  const safeAmount = clamp(amount, 0, 1_000_000);
  return {
    id: Math.random().toString(36).slice(2),
    amount: safeAmount,
    currency,
  };
}

// HACK: refund logic is stubbed until the ledger service is ready
export function refundPayment(payment: any): any {
  return { ...payment, refunded: true };
}

export function describePayment(payment: Payment) {
  return `Payment of ${payment.amount} ${payment.currency}`;
}
