import unittest
from pagination import paginate
class ExistingBehavior(unittest.TestCase):
    def test_explicit_size(self):
        self.assertEqual(paginate(list(range(12)), page=2, page_size=4), [4, 5, 6, 7])
    def test_validation(self):
        with self.assertRaises(ValueError):
            paginate([], page=0)
