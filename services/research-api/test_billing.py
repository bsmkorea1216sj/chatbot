import unittest
from billing import *

class BillingTests(unittest.TestCase):
    def test_half_budget(self):
        self.assertEqual(grant_for_payment(22000), 11000 * MICRO)
        self.assertEqual(grant_for_payment(10000), 5000 * MICRO)

    def test_reservation_prevents_overspend(self):
        b = Balance(grant_for_payment(22000))
        b = reserve(b, 10000 * MICRO)
        with self.assertRaises(PermissionError):
            reserve(b, 1001 * MICRO)
        b = settle(b, 10000 * MICRO, 8000 * MICRO)
        self.assertEqual(b.available, 3000 * MICRO)

    def test_free_and_deep(self):
        self.assertTrue(free_eligible(2, 0, 'basic'))
        self.assertFalse(free_eligible(2, 1, 'basic'))
        self.assertFalse(free_eligible(0, 0, 'deep'))

    def test_token_conversion(self):
        # Synthetic rates for arithmetic testing, not actual model pricing.
        self.assertEqual(token_cost(1000, 2000, '1', '2', '1000'),
                         5 * MICRO)

    def test_invalid_inputs(self):
        for value in (0, -1, True, 1.5):
            with self.assertRaises(ValueError): grant_for_payment(value)
        with self.assertRaises(ValueError):
            token_cost(1, 2, 'NaN', '2', '1000')

if __name__ == '__main__': unittest.main()
