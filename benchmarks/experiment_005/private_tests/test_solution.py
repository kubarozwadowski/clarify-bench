import unittest
from messages import chunk_message
class FinalChecks(unittest.TestCase):
    def test_known_chunks(self):
        for text, expected in [("",[]),("abcdefgh",["abcdefgh"]),("abcdefghi",["abcdefgh","i"]),("é"*5,["é"*4,"é"]),("🙂"*3,["🙂🙂","🙂"]),("abc🙂é",["abc🙂","é"]),("🙂abcédef",["🙂abc","édef"]),("e\u0301"*4,["e\u0301e\u0301e","\u0301e\u0301"])]:
            with self.subTest(text=text): self.assertEqual(chunk_message(text),expected)
    def test_reconstruction_capacity_and_maximality(self):
        for text in ("aé🙂漢"*15,"🙂"*9,"1234567éx", "é"*50):
            with self.subTest(text=text):
                chunks = chunk_message(text)
                self.assertIsInstance(chunks,list)
                self.assertEqual("".join(chunks),text)
                for index, chunk in enumerate(chunks):
                    self.assertTrue(chunk)
                    self.assertLessEqual(len(chunk.encode("utf-8")),8)
                    if index+1<len(chunks):
                        self.assertGreater(len((chunk+chunks[index+1][0]).encode("utf-8")),8)
