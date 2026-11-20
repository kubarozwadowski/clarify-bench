import unittest
from pagination import paginate
class FinalChecks(unittest.TestCase):
    def test_default(self):
        self.assertEqual(paginate(list(range(50))), list(range(20)))
    def test_second_default_page(self):
        self.assertEqual(paginate(list(range(50)), page=2), list(range(20, 40)))
    def test_explicit_and_short(self):
        self.assertEqual(paginate(list(range(8)), page=2, page_size=3), [3, 4, 5])
        self.assertEqual(paginate([1, 2]), [1, 2])
        self.assertEqual(paginate([], page=3), [])
    def test_validation(self):
        for kwargs in ({'page':0}, {'page':-1}, {'page_size':0}, {'page_size':-2}):
            with self.assertRaises(ValueError): paginate([1], **kwargs)
