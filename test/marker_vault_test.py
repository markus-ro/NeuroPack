import unittest

from neuropack.utils.marker_vault import MarkerVault


class MarkerVaultTests(unittest.TestCase):
    def test_add_inorder(self):
        vault = MarkerVault()
        vault.add_marker(1, 0)
        vault.add_marker(1, 10)
        vault.add_marker(2, 20)
        vault.add_marker(1, 30)

        self.assertEqual(vault.get_marker(1), [0, 10, 30])
        self.assertEqual(vault.get_marker(2), [20])
        self.assertEqual(
            vault.get_timeline(), [
                (0, 1), (10, 1), (20, 2), (30, 1)])

    def test_add_shuffled_order(self):
        vault = MarkerVault()
        vault.add_marker(1, 0)
        vault.add_marker(1, 30)
        vault.add_marker(2, 20)
        vault.add_marker(1, 10)

        self.assertEqual(vault.get_marker(1), [0, 10, 30])
        self.assertEqual(vault.get_marker(2), [20])
        self.assertEqual(
            vault.get_timeline(), [
                (0, 1), (10, 1), (20, 2), (30, 1)])
        self.assertEqual(vault.get_marker(1), [0, 10, 30])
        self.assertEqual(vault.get_marker(2), [20])
        self.assertEqual(
            vault.get_timeline(), [
                (0, 1), (10, 1), (20, 2), (30, 1)])

    def test_shift(self):
        vault = MarkerVault()
        vault.add_marker(1, 0)
        vault.add_marker(1, 1)
        vault.add_marker(2, 2)
        vault.add_marker(1, 3)

        vault.shift_timestamps(1)

        self.assertEqual(vault.get_marker(1), [1, 2, 4])
        self.assertEqual(vault.get_marker(2), [3])
        self.assertEqual(
            vault.get_timeline(), [
                (1, 1), (2, 1), (3, 2), (4, 1)])

    def test_shift_negative(self):
        vault = MarkerVault()
        vault.add_marker(1, 0)
        vault.add_marker(1, 1)
        vault.add_marker(2, 2)
        vault.add_marker(1, 3)

        vault.shift_timestamps(-1)

        self.assertEqual(vault.get_marker(1), [-1, 0, 2])
        self.assertEqual(vault.get_marker(2), [1])
        self.assertEqual(
            vault.get_timeline(), [
                (-1, 1), (0, 1), (1, 2), (2, 1)])

    def test_equal(self):
        vault1 = MarkerVault()
        vault1.add_marker(1, 0)
        vault1.add_marker(1, 1)
        vault1.add_marker(2, 2)
        vault1.add_marker(1, 3)

        vault2 = MarkerVault()
        vault2.add_marker(1, 0)
        vault2.add_marker(1, 1)
        vault2.add_marker(2, 2)
        vault2.add_marker(1, 3)

        self.assertEqual(vault1, vault2)

    def test_not_equal(self):
        vault1 = MarkerVault()
        vault1.add_marker(1, 0)
        vault1.add_marker(1, 1)
        vault1.add_marker(2, 2)
        vault1.add_marker(1, 3)

        vault2 = MarkerVault()
        vault2.add_marker(1, 0)
        vault2.add_marker(1, 1)
        vault2.add_marker(2, 2)
        vault2.add_marker(1, 4)

        self.assertNotEqual(vault1, vault2)

    def test_len(self):
        vault = MarkerVault()
        vault.add_marker(1, 0)
        vault.add_marker(1, 1)
        vault.add_marker(2, 2)
        vault.add_marker(1, 3)

        self.assertEqual(len(vault), 4)