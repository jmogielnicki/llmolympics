import random as py_random
import numpy as np
from unittest.mock import patch

class DeterministicRandom:
    """
    Provides deterministic replacements for random functions.

    This allows tests to have consistent, reproducible behavior.
    """

    def __init__(self, seed=42):
        """
        Initialize with a fixed seed.

        Args:
            seed (int): Seed value for deterministic behavior
        """
        self.random = py_random.Random(seed)
        self.np_random = np.random.RandomState(seed)

    def choice(self, seq):
        """Deterministic version of random.choice"""
        if not seq:
            raise IndexError("Cannot choose from an empty sequence")
        return seq[0]  # Always choose first element

    def sample(self, population, k):
        """Deterministic version of random.sample"""
        if k > len(population):
            raise ValueError("Sample larger than population")
        return population[:k]  # Take first k elements

    def randint(self, a, b):
        """Deterministic version of random.randint"""
        return a  # Always return the lower bound

    def random(self):
        """Deterministic version of random.random"""
        return 0.5  # Always return 0.5

    def shuffle(self, x):
        """Deterministic version of random.shuffle - does nothing"""
        return  # Don't shuffle, keep original order

    def np_choice(self, a, size=None, replace=True, p=None):
        """Deterministic version of numpy.random.choice"""
        if isinstance(a, int):
            # If a is an integer, the choice is made from range(a)
            return 0 if size is None else np.zeros(size, dtype=int)
        else:
            # If a is an array, the choice is made from it
            if size is None:
                return a[0]
            else:
                return np.array([a[0]] * size)

    def apply_patches(self):
        """
        Apply all patches to make random functions deterministic.

        Returns:
            list: List of patch objects that must be stopped later
        """
        patches = [
            patch('random.choice', self.choice),
            patch('random.sample', self.sample),
            patch('random.randint', self.randint),
            patch('random.random', self.random),
            patch('random.shuffle', self.shuffle),
            patch('numpy.random.choice', self.np_choice)
        ]

        for p in patches:
            p.start()

        return patches