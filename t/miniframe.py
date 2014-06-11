import unittest
from dsr.miniframe import * 

class TestMiniFrame(unittest.TestCase):
    def test_too_long_payload(self):
        with self.assertRaises(PayloadTooLargeError):
            frame = MiniFrame('?','abcd' * 100)           
            packed = frame.pack()

    def test_accessors(self):
        frame = MiniFrame('x','0123abc')
        self.assertEqual(frame.frameType,'x')

    def test_packing_and_unpacking(self):
        frame = MiniFrame('x','0123abc')
        packed = frame.pack()

        unpacked = MiniFrame.unpack(packed)
        self.assertEqual(unpacked.frameType,'x')
        self.assertEqual(unpacked.payload,'0123abc')

    def test_checksum(self):
        frame = MiniFrame('x','0123abc')
        packed = frame.pack()

        unpacked = MiniFrame.unpack(packed)
        self.assertTrue(unpacked.valid)

        wrong = packed[:3] + packed[2] + packed[4:]

        self.assertFalse(MiniFrame.unpack(wrong).valid)



if __name__ == '__main__':
    unittest.main()

