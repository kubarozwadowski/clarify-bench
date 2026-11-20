import copy
import unittest
from contacts import import_contact
class FinalChecks(unittest.TestCase):
    def test_preserve_duplicate_and_unrelated(self):
        contacts = {"a@example.test":{"email":"a@example.test","name":"Original"},"b@example.test":{"email":"b@example.test","name":"Other"}}
        before = copy.deepcopy(contacts)
        for name in ("Replacement","Original"):
            with self.subTest(name=name):
                incoming = {"email":"a@example.test","name":name}
                self.assertIs(import_contact(contacts,incoming),False)
                self.assertEqual(contacts,before)
    def test_exact_email_and_no_alias(self):
        contacts = {"a@example.test":{"email":"a@example.test","name":"Lower"}}
        incoming = {"email":"A@example.test","name":"Upper"}
        before = incoming.copy()
        self.assertIs(import_contact(contacts,incoming),True)
        self.assertEqual(incoming,before)
        self.assertEqual(len(contacts),2)
        incoming["name"] = "Changed"
        self.assertEqual(contacts["A@example.test"]["name"],"Upper")
