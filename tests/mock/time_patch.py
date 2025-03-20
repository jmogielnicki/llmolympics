import time
import datetime
from unittest.mock import patch, MagicMock
import sys

# Store references to original functions before any patching
original_localtime = time.localtime
original_strftime = time.strftime

class DeterministicTime:
    """
    Provides deterministic replacements for time functions.

    This allows tests to have consistent timestamps across runs.
    """

    def __init__(self, start_time=1609459200.0):  # 2021-01-01 00:00:00
        """
        Initialize with a fixed start time.

        Args:
            start_time (float): Starting timestamp (default: 2021-01-01 00:00:00)
        """
        self.current_time = start_time
        self.step = 60  # Increment by 1 minute each call
        self.orig_datetime = datetime.datetime

    def time(self):
        """Deterministic version of time.time()"""
        value = self.current_time
        self.current_time += self.step
        return value

    def now_func(self, tz=None):
        """Deterministic version of datetime.now()"""
        new_dt = self.orig_datetime.fromtimestamp(self.current_time)
        self.current_time += self.step
        return new_dt

    def apply_patches(self):
        """
        Apply all patches to make time functions deterministic.

        Returns:
            list: List of patch objects that must be stopped later
        """
        patches = [
            patch('time.time', self.time),
        ]

        # For the datetime.now issue, we'll use a backdoor to modify the method
        # We'll save and restore the original to avoid affecting other tests
        self._orig_now = datetime.datetime.now

        # Create a FakeDateTime class that inherits from datetime.datetime
        # but has a modified now() classmethod
        class FakeDateTime(datetime.datetime):
            @classmethod
            def now(cls, tz=None):
                return self.now_func(tz)

        # Use the backdoor to replace the original datetime
        datetime.datetime = FakeDateTime

        # Define the deterministic localtime function
        def det_localtime(t=None):
            # If t is None or a number, proceed normally
            if t is None or isinstance(t, (int, float)):
                return original_localtime(self.time() if t is None else t)
            # If t is already a struct_time, return it as is
            elif isinstance(t, time.struct_time):
                return t
            # For other cases, try to convert or use current time
            else:
                try:
                    return original_localtime(float(t))
                except (TypeError, ValueError):
                    return original_localtime(self.time())

        # Define the deterministic strftime function
        def det_strftime(fmt, t=None):
            # Handle struct_time objects directly
            if isinstance(t, time.struct_time):
                return original_strftime(fmt, t)
            # For other cases, convert to struct_time first
            else:
                return original_strftime(fmt, det_localtime(t))

        patches.append(patch('time.localtime', det_localtime))
        patches.append(patch('time.strftime', det_strftime))

        # Start time-related patches
        for p in patches:
            p.start()

        return patches

    def stop_patches(self, patches):
        """Stop patches and restore original datetime"""
        # Restore original datetime
        datetime.datetime = self.orig_datetime

        # Stop patches
        for p in patches:
            p.stop()