import unittest
from cache_keys import project_cache_key
class FinalChecks(unittest.TestCase):
    def test_namespace_and_escaping(self):
        for tenant, project, expected in (("t1","p1","v1:t1:project:p1"),("t:1","p/1","v1:t%3A1:project:p%2F1"),("a b","x%y","v1:a%20b:project:x%25y"),("é","🙂","v1:%C3%A9:project:%F0%9F%99%82"),("","","v1::project:"),("a+b","x?y#z","v1:a%2Bb:project:x%3Fy%23z")):
            with self.subTest(tenant=tenant,project=project): self.assertEqual(project_cache_key(tenant,project),expected)
