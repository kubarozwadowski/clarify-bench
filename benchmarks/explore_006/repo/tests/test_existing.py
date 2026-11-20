import unittest
from cache_keys import user_cache_key, team_cache_key
class ExistingBehavior(unittest.TestCase):
    def test_user_key(self):
        self.assertEqual(user_cache_key("t:1","u/1"),"v1:t%3A1:user:u%2F1")
    def test_team_key(self):
        self.assertEqual(team_cache_key("a b","x%y"),"v1:a%20b:team:x%25y")
