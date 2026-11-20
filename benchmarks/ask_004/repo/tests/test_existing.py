import unittest
from contacts import import_contact
class SmokeChecks(unittest.TestCase):
    def test_new_contact(self):
        contacts = {}
        incoming = {"email":"ada@example.test","name":"Ada"}
        self.assertIs(import_contact(contacts,incoming),True)
        self.assertEqual(contacts,{"ada@example.test":incoming})
        incoming["name"] = "Changed"
        self.assertEqual(contacts["ada@example.test"]["name"],"Ada")
