import { processPayment, refundPayment, describePayment } from './paymentService';

describe('processPayment', () => {
  it('returns a payment record with the given amount and currency', () => {
    const payment = processPayment(100, 'USD');
    expect(payment.amount).toBe(100);
    expect(payment.currency).toBe('USD');
  });

  it('generates an id for the payment', () => {
    const payment = processPayment(100, 'USD');
    expect(typeof payment.id).toBe('string');
    expect(payment.id.length).toBeGreaterThan(0);
  });

  it('clamps negative amounts to 0', () => {
    const payment = processPayment(-50, 'USD');
    expect(payment.amount).toBe(0);
  });

  it('clamps amounts above 1,000,000', () => {
    const payment = processPayment(2_000_000, 'USD');
    expect(payment.amount).toBe(1_000_000);
  });
});

describe('refundPayment', () => {
  it('returns a copy of the payment with refunded set to true', () => {
    const payment = { id: 'abc123', amount: 100, currency: 'USD' };
    const refunded = refundPayment(payment);
    expect(refunded).toEqual({ ...payment, refunded: true });
  });
});

describe('describePayment', () => {
  it('formats the payment as a human-readable description', () => {
    const payment = { id: 'abc123', amount: 100, currency: 'USD' };
    expect(describePayment(payment)).toBe('Payment of 100 USD');
  });
});
