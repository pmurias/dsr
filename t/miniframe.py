import unittest
from dsr.miniframe import * 

class TestMiniFrame(unittest.TestCase):
    def test_too_long_payload(self):
        with self.assertRaises(PayloadTooLargeError):
            frame = MiniFrame('abcd' * 100)           
            packed = frame.pack()


if __name__ == '__main__':
    unittest.main()

