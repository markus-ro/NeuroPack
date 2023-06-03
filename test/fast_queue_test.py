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
        self.assertListEqual(queue.data.tolist(), np.array(
            [1, 2, 3, 4], dtype=np.float32).tolist())

    def test_overflow(self):
        queue = FastQueue(4)
        queue.push(1)
        queue.push(2)
        queue.push(3)
        queue.push(4)
        queue.push(5)
        self.assertListEqual(queue.data.tolist(), np.array(
            [2, 3, 4, 5], dtype=np.float32).tolist())

    def test_overflow_insert(self):
        queue = FastQueue(3)

        res = queue.overflow_push(1)
        self.assertIsNone(res)

        res = queue.overflow_push(2)
        self.assertIsNone(res)

        res = queue.overflow_push(3)
        self.assertIsNone(res)

        res = queue.overflow_push(4)
        self.assertEqual(res, 1)

        res = queue.overflow_push(5)
        self.assertEqual(res, 2)

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
