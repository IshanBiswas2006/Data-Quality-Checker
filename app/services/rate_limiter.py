import time
from collections import defaultdict
from typing import Dict, List, Tuple

class SimpleRateLimiter:
    """
    Lightweight in-memory rate limiter for abuse prevention on upload/processing endpoints.
    Tracks timestamps per client IP.
    """
    _requests: Dict[str, List[float]] = defaultdict(list)
    
    @classmethod
    def is_allowed(cls, client_ip: str, max_requests: int = 30, window_seconds: int = 600) -> Tuple[bool, int]:
        """
        Checks if client_ip has exceeded max_requests within window_seconds.
        Returns:
            (is_allowed, remaining_seconds_until_reset)
        """
        now = time.time()
        timestamps = cls._requests[client_ip]
        
        # Filter out timestamps outside the sliding window
        valid_timestamps = [t for t in timestamps if now - t < window_seconds]
        cls._requests[client_ip] = valid_timestamps
        
        if len(valid_timestamps) >= max_requests:
            oldest = valid_timestamps[0]
            retry_after = int(window_seconds - (now - oldest)) + 1
            return False, max(1, retry_after)
            
        cls._requests[client_ip].append(now)
        return True, 0

    @classmethod
    def reset(cls) -> None:
        """For testing purposes."""
        cls._requests.clear()
