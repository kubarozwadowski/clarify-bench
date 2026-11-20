import copy
import itertools
import unittest
from settings import resolve_timeout
class FinalChecks(unittest.TestCase):
    def test_all_presence_combinations(self):
        for present in itertools.product((False,True),repeat=3):
            sources = [{"timeout":value} if flag else {} for flag,value in zip(present,(11,22,33))]
            before = copy.deepcopy(sources)
            expected = next((source["timeout"] for source in sources if "timeout" in source),30)
            with self.subTest(present=present):
                self.assertEqual(resolve_timeout(*sources),expected)
                self.assertEqual(sources,before)
    def test_zero_is_present(self):
        self.assertEqual(resolve_timeout({"timeout":0},{"timeout":20},{"timeout":30}),0)
        self.assertEqual(resolve_timeout({}, {"timeout":0},{"timeout":30}),0)
        self.assertEqual(resolve_timeout({}, {}, {"timeout":0}),0)
    def test_unrelated_keys(self):
        self.assertEqual(resolve_timeout({"port":99},{"workers":2},{"other":3}),30)
