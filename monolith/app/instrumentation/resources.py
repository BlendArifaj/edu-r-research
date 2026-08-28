from __future__ import annotations

import resource


def sample_rusage() -> tuple[float, float, int]:
    usage = resource.getrusage(resource.RUSAGE_SELF)
    rss = int(usage.ru_maxrss)
    return usage.ru_utime, usage.ru_stime, rss


def rss_bytes_if_available() -> int | None:
    try:
        import psutil

        return int(psutil.Process().memory_info().rss)
    except Exception:
        return None
