import unittest
from handlers import get_user, get_team
class ExistingBehavior(unittest.TestCase):
    def test_user(self):
        self.assertEqual(get_user({"u1": {"name": "Ada"}}, "u1"), (200, {"data": {"name": "Ada"}}))
    def test_team_error(self):
        self.assertEqual(get_team({}, "t1"), (404, {"error": {"code": "not_found", "resource": "team", "id": "t1"}}))
