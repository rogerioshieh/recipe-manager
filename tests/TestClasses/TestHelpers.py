"""
TestClass to test functions on helpers.py
Useful resources:
- https://stackoverflow.com/questions/17375340/testing-code-that-requires-a-flask-app-or-request-context
"""

import unittest
from random import randint
import app.helpers as h
from app.tests.BaseTest import BaseTest


class TestHelpers(BaseTest):

    def test_convert(self):

        x = randint(1, 1000)

        # weight measurements
        self.assertEqual(h.convert('g', x), x)
        self.assertEqual(h.convert('lb', x), x * 454)
        self.assertEqual(h.convert('oz', x), x * 28.35)
        self.assertEqual(h.convert('kg', x), x * 1000)

        # volume measurements
        self.assertEqual(h.convert('cup', x), x * 236.58)
        self.assertEqual(h.convert('l', x), x * 1000)
        self.assertEqual(h.convert('gal', x), x * 3785.41)
        self.assertEqual(h.convert('T', x), x * 15)
        self.assertEqual(h.convert('t', x), x * 5)

    def test_get_recipe_price(self):
        self.assertAlmostEqual(h.get_recipe_price(1), 3.49)
        self.assertAlmostEqual(h.get_recipe_price(2), 5.70)

    def get_meal_price(self):
        self.assertNotEqual(h.get_meal_price(1), 3.49)

    def get_macros_price(self):
        self.assertNotEqual(h.get_macros_price(1), [[0, 0, 0, 0], 3.49])
        self.assertNotEqual(h.get_macros_price(2), [[0, 0, 0, 0], 3.49])


if __name__ == '__main__':
    unittest.main()

