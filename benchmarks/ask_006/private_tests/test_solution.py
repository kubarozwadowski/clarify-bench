import unittest
from accounts import create_account
class FinalChecks(unittest.TestCase):
    def test_defaults_and_identity(self):
        for user_id, email in (("u1","ada@example.test"),("U2","Case+tag@example.test"),("","")):
            with self.subTest(user_id=user_id):
                self.assertEqual(create_account(user_id,email),{"id":user_id,"email":email,"product_notifications":False})
                self.assertIs(create_account(user_id,email)["product_notifications"],False)
    def test_independent_records(self):
        first = create_account("u1","a@example.test")
        second = create_account("u1","a@example.test")
        self.assertIsNot(first,second)
        first["product_notifications"] = True
        first["email"] = "changed@example.test"
        self.assertEqual(second,{"id":"u1","email":"a@example.test","product_notifications":False})
