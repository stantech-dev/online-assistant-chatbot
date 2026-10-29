import threading
import time
from collections import defaultdict, deque


class RateLimiter:
    """Allow at most max_calls per key within window_seconds (in memory, one process)."""

    def __init__(self, max_calls, window_seconds):
        self.max_calls = max_calls
        self.window = window_seconds
        self.calls = defaultdict(deque)
        self.lock = threading.Lock()

    def allow(self, key):
        now = time.time()
        with self.lock:
            if len(self.calls) > 10000:  # forget old visitors so memory can't grow forever
                stale = [k for k, q in self.calls.items() if not q or q[-1] <= now - self.window]
                for k in stale:
                    del self.calls[k]
            q = self.calls[key]
            while q and q[0] <= now - self.window:
                q.popleft()
            if len(q) >= self.max_calls:
                return False
            q.append(now)
            return True