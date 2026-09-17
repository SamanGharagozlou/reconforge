import unittest

from reconforge.money import format_eur, parse_eur


class MoneyTests(unittest.TestCase):
    def test_exact_decimal_arithmetic(self):
        self.assertEqual(parse_eur("0.10") + parse_eur("0.20"), 30)
        self.assertEqual(parse_eur("-250.00"), -25000)

    def test_rejects_unsupported_representations(self):
        for value in (0.1, True, "1.001", "1e3", "NaN", "Infinity", "1,000.00", " 1.00", "1"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                parse_eur(value)

    def test_formatting_preserves_sign_and_cents(self):
        self.assertEqual(format_eur(11530000), "EUR 115,300.00")
        self.assertEqual(format_eur(-1), "EUR -0.01")


if __name__ == "__main__":
    unittest.main()
