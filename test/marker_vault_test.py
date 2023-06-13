import unittest

from neuropack.utils.marker_vault import MarkerVault


class MarkerVaultTests(unittest.TestCase):
    def test_add_inorder(self):
        vault = MarkerVault()
        vault.add_marker(1, 0)
        vault.add_marker(1, 1)
        vault.add_marker(2, 2)
        vault.add_marker(1, 3)

        self.assertEqual(vault.get_marker(1), [0, 1, 3])
        self.assertEqual(vault.get_marker(2), [2])
        self.assertEqual(vault.get_timeline(), [(0, 1), (1, 1), (2, 2), (3, 1)])
    
    def test_add_shuffled_order(self):
        vault = MarkerVault()
        vault.add_marker(1, 0)
        vault.add_marker(1, 3)
        vault.add_marker(2, 2)
        vault.add_marker(1, 1)

        self.assertEqual(vault.get_marker(1), [0, 1, 3])
        self.assertEqual(vault.get_marker(2), [2])
        self.assertEqual(vault.get_timeline(), [(0, 1), (1, 1), (2, 2), (3, 1)])
        self.assertEqual(vault.get_marker(1), [0, 1, 3])
        self.assertEqual(vault.get_marker(2), [2])
        self.assertEqual(vault.get_timeline(), [(0, 1), (1, 1), (2, 2), (3, 1)])
