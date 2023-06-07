import unittest

from neuropack.utils.marker_vault import MarkerVault


class MarkerVaultTests(unittest.TestCase):
    def test_add_inorder(self):
        vault = MarkerVault()
        vault.add_marker("test", 0)
        vault.add_marker("test", 1)
        vault.add_marker("error", 2)
        vault.add_marker("test", 3)

        self.assertEqual(vault.get_marker("test"), [0, 1, 3])
        self.assertEqual(vault.get_marker("error"), [2])
        self.assertEqual(vault.get_timeline(), [(0, "test"), (1, "test"), (2, "error"), (3, "test")])
    
    def test_add_shuffled_order(self):
        vault = MarkerVault()
        vault.add_marker("test", 0)
        vault.add_marker("test", 3)
        vault.add_marker("error", 2)
        vault.add_marker("test", 1)

        self.assertEqual(vault.get_marker("test"), [0, 1, 3])
        self.assertEqual(vault.get_marker("error"), [2])
        self.assertEqual(vault.get_timeline(), [(0, "test"), (1, "test"), (2, "error"), (3, "test")])
        self.assertEqual(vault.get_marker("test"), [0, 1, 3])
        self.assertEqual(vault.get_marker("error"), [2])
        self.assertEqual(vault.get_timeline(), [(0, "test"), (1, "test"), (2, "error"), (3, "test")])
