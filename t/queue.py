import unittest
from dsr.queue import * 

class TestMiniFrame(unittest.TestCase):
    def test_basic_add(self):
        log = []
        q = Queue()
        def x():
            log.append(1)
        def y():
            log.append(2)
        def z():
            log.append(3)

        q.add(3,z)
        q.add(1,x)
        q.add(2,y)

        q.execute(1)
        q.execute(2)
        q.execute(3)

        self.assertEqual(log,[1,2,3])

    def test_recursion_with_zero_time(self):
        q = Queue()
        log = []


        def x():
            log.append((len(log)+1)*2)
            if len(log) < 3:
                q.add(0,x) 
     
        q.add(0,x)

        self.assertEqual(log,[])
        q.execute(1)
        self.assertEqual(log,[2])
        q.execute(1)
        self.assertEqual(log,[2,4])
        q.execute(1)
        self.assertEqual(log,[2,4,6])
        q.execute(1)
        self.assertEqual(log,[2,4,6])

    def test_complex_recursion(self):
        log = []
        q = Queue()
        def x():
            log.append(1)
            q.add(1,x)
        def y():
            log.append(2)
            q.add(2,y)
        def z():
            log.append(3)
            q.add(3,z)

        q.add(3,z)
        q.add(1,x)
        q.add(2,y)

        q.execute(1)
        q.execute(2)
        q.execute(2)
        q.execute(3)

        self.assertEqual(log,[1,2,1,2,1,3,2,1])




if __name__ == '__main__':
    unittest.main()

