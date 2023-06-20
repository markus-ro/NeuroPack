import unittest

from time import time
from neuropack.utils.run_for import run_for

class RunForTests(unittest.TestCase):
    def test_run_for_1(self):
        start = time()
        while run_for(5):
            pass
        self.assertTrue(time() - start >= 5)

        start = time()
        while run_for(5):
            pass
        self.assertTrue(time() - start >= 5)