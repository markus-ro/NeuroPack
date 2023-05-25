import unittest

import numpy as np

from neuropack.utils import FastQueue


class FastQueueTests(unittest.TestCase):
    def test_insert(self):
        queue = FastQueue(4)
        queue.push(1)
        queue.push(2)
        queue.push(3)
        queue.push(4)
        self.assertEqual(queue.data, np.array([1, 2, 3, 4], dtype=np.float32))

    def test_overflow(self):
        queue = FastQueue(4)
        queue.push(1)
        queue.push(2)
        queue.push(3)
        queue.push(4)
        queue.push(5)
        self.assertEqual(queue.data, np.array([2, 3, 4, 5], dtype=np.float32))

    def test_pop(self):
        queue = FastQueue(4)
        queue.push(1)
        queue.push(2)
        queue.push(3)
        queue.push(4)
        self.assertEqual(queue.pop(), 1)

    def test_len(self):
        queue = FastQueue(4)
        queue.push(1)
        queue.push(2)
        queue.push(3)
        queue.push(4)
        self.assertEqual(len(queue), 4)
