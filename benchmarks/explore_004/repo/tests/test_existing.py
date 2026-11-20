import unittest
from listings import list_users, list_projects
class ExistingBehavior(unittest.TestCase):
    def test_user_visibility(self):
        records = [{"id":"u1"},{"id":"u2","deleted_at":None},{"id":"u3","deleted_at":"2026-01-01"}]
        self.assertEqual(list_users(records),records[:2])
    def test_project_visibility(self):
        self.assertEqual(list_projects([{"id":"p1","deleted_at":""}]),[])
